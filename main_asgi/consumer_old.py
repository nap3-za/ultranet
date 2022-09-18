import json
import asyncio

from channels.generic.websocket import AsyncJsonWebsocketConsumer
from channels.db import database_sync_to_async

from django.core.serializers import serialize
from django.core.serializers.python import Serializer
from django.core.paginator import Paginator
from django.utils import timezone
from asgiref.sync import sync_to_async, async_to_sync


from account.utils import LazyAccountEncoder
from .utils import calculate_timestamp, LazyRoomChatMessageEncoder
from .exceptions import ClientError
from .constants import *

from .models import PrivateChatMessage, PrivateChatRoom, PublicChatRoom, PublicChatMessage,Notification, UserChannel
from friend.models import FriendList
from account.models import BaseAccount as Account
from django.conf import settings


class MainConsumer(AsyncJsonWebsocketConsumer):

	async def connect(self):
		print("[+] connect" + str(self.scope["user"]))

		# let everyone connect. But limit read/write to authenticated users
		await self.accept()

	async def receive_json(self, content):
		print("[+] receive_json")
		"""
		Posible commands
			> join
				>> target
					>>> main
					>>> private
					>>> public
				>> context {}
			> send
				>> target
					>>> ... 
				>> destination
					>> ...
				>> context
					>>> ...
			> leave
				>> target
				>> destination
			> fetch
				>> target 
				>> context


		"""
		command = content.get("command", None)
		print(f">>	command : {content['command']}")
		try:
			if command == "join_private":
				print(content)
				await self.join_private_room(content["room"], content["skip"])
				self.room_id = content["room"]
			elif command == "send_private":
				if len(content["message"].lstrip()) == 0:
					raise ClientError(422,"You can't send an empty message.")
				room_id = content["room"]
				self.room_id = room_id
				print("Room : "+str(room_id))
				print("Message : "+content["message"])
				await self.send_room(room_id=room_id, message=content["message"])
			elif command == "leave_private":
				# Leave the room
				await self.leave_room(content["room"])
			elif command == "get_private_chat_messages":
				await self.display_progress_bar(True)
				room = await get_room_or_error(content['room_id'], self.scope["user"])
				payload = await get_room_chat_messages(room, content['page_number'], user=self.scope["user"])
				if payload != None:
					payload = json.loads(payload)
					await self.send_messages_payload(payload['messages'], payload['new_page_number'])
				else:
					raise ClientError(204,"Something went wrong retrieving the chatroom messages.")
				await self.display_progress_bar(False)
			elif command == "get_user_info":
				await self.display_progress_bar(True)
				room = await get_room_or_error(content['room_id'], self.scope["user"])
				payload = await get_user_info(room, self.scope["user"])
				if payload != None:
					payload = json.loads(payload)
					await self.send_user_info_payload(payload['user_info'])
				else:
					raise ClientError(204, "Something went wrong retrieving the other users account details.")
				await self.display_progress_bar(False)



			elif command == "join_public":
				await self.join_public_room(content["room"])
			elif command == "send_public":
				if len(content["message"].lstrip()) != 0:
					await self.pub_send_room(content["room_id"], content["message"])
					# raise ClientError(422,"You can't send an empty message.")
			elif command == "get_public_chat_messages":
				await self.display_progress_bar(True)
				room = await get_room_or_error(content['room_id'])
				payload = await pub_get_room_chat_messages(room, content['page_number'])
				if payload != None:
					payload = json.loads(payload)
					await self.pub_send_messages_payload(payload['messages'], payload['new_page_number'])
				else:
					raise ClientError(204,"Something went wrong retrieving the chatroom messages.")
				await self.display_progress_bar(False)
			elif command == "leave":
				# Leave the room
				await self.leave_public(content["room"])







		except ClientError as e:
			await self.handle_client_error(e)

	async def disconnect(self, code):
		"""
		Called when the WebSocket closes for any reason.
		"""
		# Leave the room
		print("ChatConsumer: disconnect")
		try:
			if self.room_id != None:
				await self.leave_room(self.room_id)
		except Exception as e:
			print("EXCEPTION: " + str(e))
			pass



	async def join_private_room(self, room_id, skip):
		"""
		Called by receive_json when someone sent a join command.
		"""
		# The logged-in user is in our scope thanks to the authentication ASGI middleware (AuthMiddlewareStack)
		print("ChatConsumer: join_room: " + str(room_id))
		try:
			room = await get_room_or_error(room_id, self.scope["user"])
		except ClientError as e:
			return await self.handle_client_error(e)


		await on_user_connected(room, self.scope["user"])
		# Add user to "users" list for room
		await connect_user(room, self.scope["user"])

		# Add them to the group so they get room messages
		await self.channel_layer.group_add(
			room.group_name,
			self.channel_name,
		)

		# Store that we're in the room
		self.room_id = room.id
		if skip == "false":
			# Instruct their client to finish opening the room
			await self.send_json({
				"join": str(room.id),
			})

		if self.scope["user"].is_authenticated:
			# Notify the group that someone joined
			await self.channel_layer.group_send(
				room.group_name,
				{
					"type": "chat.join",
					"room_id": room_id,
					"profile_image": self.scope["user"].profile_image.url,
					"username": self.scope["user"].username,
					"user_id": self.scope["user"].id,
					"skip": skip,
				}
			)

	async def join_public_room(self, room_id):
		"""
		Called by receive_json when someone sent a join command.
		"""
		print("PublicChatConsumer: join_room")
		is_auth = is_authenticated(self.scope["user"])
		try:
			room = await pub_get_room_or_error(room_id)
		except ClientError as e:
			await self.handle_client_error(e)

		# Add user to "users" list for room
		if is_auth:
			await pub_connect_user(room, self.scope["user"])

		# Store that we're in the room
		self.room_id = room.id

		# Add them to the group so they get room messages
		await self.channel_layer.group_add(
			room.group_name,
			self.channel_name,
		)

		# Instruct their client to finish opening the room
		await self.send_json({
			"join": str(room.id)
		})

		# send the new user count to the room
		num_connected_users = await pub_get_num_connected_users(room)
		await self.channel_layer.group_send(
			room.group_name,
			{
				"type": "pubconnected.user.count",
				"connected_user_count": num_connected_users,
			}
		)

	async def leave_room(self, room_id):
		"""
		Called by receive_json when someone sent a leave command.
		"""
		# The logged-in user is in our scope thanks to the authentication ASGI middleware
		print("ChatConsumer: leave_room")

		room = await get_room_or_error(room_id, self.scope["user"])

		# Remove user from "connected_users" list
		await disconnect_user(room, self.scope["user"])

		# Notify the group that someone left
		await self.channel_layer.group_send(
			room.group_name,
			{
				"type": "chat.leave",
				"room_id": room_id,
				"profile_image": self.scope["user"].profile_image.url,
				"username": self.scope["user"].username,
				"user_id": self.scope["user"].id,
			}
		)

		# Remove that we're in the room
		self.room_id = None

		# Remove them from the group so they no longer get room messages
		await self.channel_layer.group_discard(
			room.group_name,
			self.channel_name,
		)
		# Instruct their client to finish closing the room
		await self.send_json({
			"leave": str(room.id),
		})

	async def send_room(self, room_id, message):
		"""
		Called by receive_json when someone sends a message to a room.
		"""
		print("ChatConsumer: send_room")
		# Check they are in this room
		if self.room_id != None:
			if str(room_id) != str(self.room_id):
				print("CLIENT ERRROR 1")
				raise ClientError("ROOM_ACCESS_DENIED", "Room access denied 1")
		else:
			print("CLIENT ERRROR 2")
			raise ClientError("ROOM_ACCESS_DENIED", "Room access denied 2")

		# Get the room and send to the group about it
		room = await get_room_or_error(room_id, self.scope["user"])

		# get list of connected_users
		connected_users = room.connected_users.all()

		# Execute these functions asychronously
		message_obj = await create_room_chat_message(room, self.scope["user"], message)
		await self.channel_layer.group_send(
			room.group_name,
			{
				"type": "chat.message",
				"profile_image": self.scope["user"].profile_image.url,
				"username": self.scope["user"].username,
				"user_id": self.scope["user"].id,
				"message": message,
				"message_id": message_obj.id,
			}
		)

	# These helper methods are named by the types we send - so chat.join becomes chat_join
	async def chat_join(self, event):
		"""
		Called when someone has joined our chat.
		"""
		# Send a message down to the client
		if event["skip"] == "false":
			print("ChatConsumer: chat_join: " + str(self.scope["user"].id))
			if event["username"]:
				await self.send_json(
					{
						"msg_type": MSG_TYPE_ENTER,
						"room": event["room_id"],
						"profile_image": event["profile_image"],
						"username": event["username"],
						"user_id": event["user_id"],
						"message": event["username"] + " connected.",
					},
				)

	async def chat_leave(self, event):
		"""
		Called when someone has left our chat.
		"""
		# Send a message down to the client
		print("ChatConsumer: chat_leave")
		if event["username"]:
			await self.send_json(
			{
				"msg_type": MSG_TYPE_LEAVE,
				"room": event["room_id"],
				"profile_image": event["profile_image"],
				"username": event["username"],
				"user_id": event["user_id"],
				"message": event["username"] + " disconnected.",
			},
		)

	async def chat_message(self, event):
		"""
		Called when someone has messaged our chat.
		"""
		# Send a message down to the client
		print("ChatConsumer: chat_message")

		timestamp = calculate_timestamp(timezone.now())
		try:
			await self.send_json(
				{
					"msg_type": MSG_TYPE_MESSAGE,
					"username": event["username"],
					"user_id": event["user_id"],
					"profile_image": event["profile_image"],
					"message": event["message"],
					"msg_id": event["message_id"],
					"natural_timestamp": timestamp,
					"new": "True",
				},
			)
			print("Chatconsumer chat_message done")
		except Exception as e:
			print(str(e))

	async def send_messages_payload(self, messages, new_page_number):
		"""
		Send a payload of messages to the ui
		"""
		print("ChatConsumer: send_messages_payload. ")

		await self.send_json(
			{
				"messages_payload": "messages_payload",
				"messages": messages,
				"new_page_number": new_page_number,
			},
		)
	
	async def send_user_info_payload(self, user_info):
		"""
		Send a payload of user information to the ui
		"""
		print("ChatConsumer: send_user_info_payload. ")
		await self.send_json(
			{
				"user_info": user_info,
			},
		)
	
	async def display_progress_bar(self, is_displayed):
		"""
		1. is_displayed = True
		- Display the progress bar on UI
		2. is_displayed = False
		- Hide the progress bar on UI
		"""
		print("DISPLAY PROGRESS BAR: " + str(is_displayed))
		await self.send_json(
			{
				"display_progress_bar": is_displayed
			}
		)
	
	async def handle_client_error(self, e):
		"""
		Called when a ClientError is raised.
		Sends error data to UI.
		"""
		errorData = {}
		errorData['error'] = e.code
		if e.message:
			errorData['message'] = e.message
			await self.send_json(errorData)
		return



	async def pub_send_room(self, room_id, message):
		"""
		Called by receive_json when someone sends a message to a room.
		"""
		# Check they are in this room
		print("PublicChatConsumer: send_room")
		if self.room_id != None:
			if str(room_id) != str(self.room_id):
				raise ClientError("ROOM_ACCESS_DENIED", "Room access denied")
			if not is_authenticated(self.scope["user"]):
				raise ClientError("AUTH_ERROR", "You must be authenticated to chat.")
		else:
			raise ClientError("ROOM_ACCESS_DENIED", "Room access denied")

		# Get the room and send to the group about it
		room = await pub_get_room_or_error(room_id)
		await pub_create_room_chat_message(room, self.scope["user"], message)

		await self.channel_layer.group_send(
			room.group_name,
			{
				"type": "pubchat.message",
				"profile_image": self.scope["user"].profile_image.url,
				"username": self.scope["user"].username,
				"user_id": self.scope["user"].id,
				"message": message,
			}
		)

	async def pubchat_message(self, event):
		"""
		Called when someone has messaged our chat.
		"""
		# Send a message down to the client
		print("PublicChatConsumer: chat_message from user #" + str(event["user_id"]))
		timestamp = calculate_timestamp(timezone.now())
		await self.send_json(
			{
				"msg_type": MSG_TYPE_MESSAGE,
				"profile_image": event["profile_image"],
				"username": event["username"],
				"user_id": event["user_id"],
				"message": event["message"],
				"natural_timestamp": timestamp,
			},
		)

	async def pub_join_room(self, room_id):
		"""
		Called by receive_json when someone sent a join command.
		"""
		print("PublicChatConsumer: join_room")
		is_auth = is_authenticated(self.scope["user"])
		try:
			room = await pub_get_room_or_error(room_id)
		except ClientError as e:
			await self.handle_client_error(e)

		# Add user to "users" list for room
		if is_auth:
			await pub_connect_user(room, self.scope["user"])

		# Store that we're in the room
		self.room_id = room.id

		# Add them to the group so they get room messages
		await self.channel_layer.group_add(
			room.group_name,
			self.channel_name,
		)

		# Instruct their client to finish opening the room
		await self.send_json({
			"join": str(room.id)
		})

		# send the new user count to the room
		num_connected_users = await pub_get_num_connected_users(room)
		await self.channel_layer.group_send(
			room.group_name,
			{
				"type": "pubconnected.user.count",
				"connected_user_count": num_connected_users,
			}
		)

	async def pub_leave_room(self, room_id):
		"""
		Called by receive_json when someone sent a leave command.
		"""
		print("PublicChatConsumer: leave_room")
		is_auth = is_authenticated(self.scope["user"])
		room = await pub_get_room_or_error(room_id)

		# Remove user from "users" list
		if is_auth:
			await pub_disconnect_user(room, self.scope["user"])

		# Remove that we're in the room
		self.room_id = None
		# Remove them from the group so they no longer get room messages
		await self.channel_layer.group_discard(
			room.group_name,
			self.channel_name,
		)

		# send the new user count to the room
		num_connected_users = await pub_get_num_connected_users(room)
		await self.channel_layer.group_send(
		room.group_name,
			{
				"type": "pubconnected.user.count",
				"connected_user_count": num_connected_users,
			}
		)

	async def pub_handle_client_error(self, e):
		"""
		Called when a ClientError is raised.
		Sends error data to UI.
		"""
		errorData = {}
		errorData['error'] = e.code
		if e.message:
			errorData['message'] = e.message
			await self.send_json(errorData)
		return

	async def pub_send_messages_payload(self, messages, new_page_number):
		"""
		Send a payload of messages to the ui
		"""
		print("PublicChatConsumer: send_messages_payload. ")

		await self.send_json(
			{
				"messages_payload": "messages_payload",
				"messages": messages,
				"new_page_number": new_page_number,
			},
		)

	async def pubconnected_user_count(self, event):
		"""
		Called to send the number of connected users to the room.
		This number is displayed in the room so other users know how many users are connected to the chat.
		"""
		# Send a message down to the client
		print("PublicChatConsumer: connected_user_count: count: " + str(event["connected_user_count"]))
		await self.send_json(
			{
				"msg_type": MSG_TYPE_CONNECTED_USER_COUNT,
				"connected_user_count": event["connected_user_count"]
			},
		)

	async def pub_display_progress_bar(self, is_displayed):
		"""
		1. is_displayed = True
		- Display the progress bar on UI
		2. is_displayed = False
		- Hide the progress bar on UI
		"""
		print("DISPLAY PROGRESS BAR: " + str(is_displayed))
		await self.send_json(
			{
				"display_progress_bar": is_displayed
			}
		)

@database_sync_to_async
def get_room_or_error(room_id, user):
	"""
	Tries to fetch a room for the user, checking permissions along the way.
	"""
	print("ChatConsumer : get_room_or_error")
	try:
		room = PrivateChatRoom.objects.get(pk=room_id)
	except PrivateChatRoom.DoesNotExist:
		print("Room does not exist")
		raise ClientError("ROOM_INVALID", "Invalid room.")

	# Is this user allowed in the room? (must be user1 or user2)
	if user != room.user1 and user != room.user2:
		print("No perm")
		raise ClientError("ROOM_ACCESS_DENIED", "You do not have permission to join this room.")

	# Are the users in this room friends?
	friend_list = FriendList.objects.get(user=user).friends.all()
	if not room.user1 in friend_list:
		if not room.user2 in friend_list:
			print(user)
			print(room.user1)
			print(room.user2)
			print("Not friends")
			raise ClientError("ROOM_ACCESS_DENIED", "You must be friends to chat.")
	return room

@database_sync_to_async
def get_user_info(room, user):
	print("get user info func running")
	"""
	Retrieve the user info for the user you are chatting with
	"""
	try:
		# Determine who is who h
		other_user = room.user1
		try:
			if other_user == user:
				other_user = room.user2
		except Exception as e:
			raise e

		payload = {}
		s = LazyAccountEncoder()
		# convert to list for serializer and select first entry (there will be only 1)
		payload['user_info'] = s.serialize([other_user])[0] 
		return json.dumps(payload)
	except ClientError as e:
		raise ClientError("DATA_ERROR", "Unable to get that users information.")
	return None

@database_sync_to_async
def create_room_chat_message(room, user, message):
	msg = PrivateChatMessage.objects.create(user=user, room=room, content=message)
	msg.save()
	if len(room.connected_users.all()) > 1:
		msg.seen = True
		msg.save()
	if len(room.connected_users.all()) == 1:
		receiver = room.user1
		if user == room.user1:
			receiver = room.user2
			notification = Notification.objects.create(
			target=receiver,
			from_user=user,
			redirect_url=f"{settings.BASE_URL}/account/{user.username}/details/",
			verb=f"{user.username} sent you a message.",
			)
			notification.save()
	else:
		print("notification not created beacause both users are connected")
	return msg

@database_sync_to_async
def get_room_chat_messages(room, page_number, **kwargs):
	try:
		qs = PrivateChatMessage.objects.by_room(room)
		if kwargs.get("user"):
			user = kwargs.get("user")
			for q in qs:
				if q.user != user:
					q.seen = True
					q.save()
				else:
					pass
			
		p = Paginator(qs, DEFAULT_ROOM_CHAT_MESSAGE_PAGE_SIZE)

		payload = {}
		messages_data = None
		new_page_number = int(page_number)  
		if new_page_number <= p.num_pages:
			new_page_number = new_page_number + 1
			s = LazyRoomChatMessageEncoder()
			payload['messages'] = s.serialize(p.page(page_number).object_list)
		else:
			payload['messages'] = "None"
		payload['new_page_number'] = new_page_number
		return json.dumps(payload)
	except Exception as e:
		print("EXCEPTION: " + str(e))
	return None

@database_sync_to_async
def connect_user(room, user):
	# add user to connected_users list
	account = Account.objects.get(pk=user.id)
	return room.connect_user(account)

@database_sync_to_async
def disconnect_user(room, user):
	# remove from connected_users list
	account = Account.objects.get(pk=user.id)
	return room.disconnect_user(account)

# If the user is not connected to the chat, increment "unread messages" count
@database_sync_to_async
def append_unread_msg_if_not_connected(room, user, connected_users, message):
	if not user in connected_users:
		pass
		"""
		EMERGENCY
		""" 
		# try:
		# 	unread_msgs = UnreadChatRoomMessages.objects.filter(room=room, user=user)[0]
		# 	unread_msgs.most_recent_message = message
		# 	unread_msgs.count += 1
		# 	unread_msgs.save()
		# except UnreadChatRoomMessages.DoesNotExist:
		# 	UnreadChatRoomMessages(room=room, user=user, count=1).save()
		# 	pass
	else:
		pass

# When a user connects, reset their unread message count
@database_sync_to_async
def on_user_connected(room, user):
	# confirm they are in the connected users list
	connected_users = room.connected_users.all()
	if user in connected_users:
		pass
		"""
		EMERGENCY
		"""
		# try:
		# 	# reset count
		# 	unread_msgs = UnreadChatRoomMessages.objects.filter(room=room, user=user)[0]
		# 	unread_msgs.count = 0
		# 	unread_msgs.save()
		# except UnreadChatRoomMessages.DoesNotExist:
		# 	UnreadChatRoomMessages(room=room, user=user).save()
		# 	pass

def is_authenticated(user):
	if user.is_authenticated:
		return True
	return False

@database_sync_to_async
def pub_get_num_connected_users(room):
	if room.users:
		return len(room.users.all())
	return 0

@database_sync_to_async
def pub_create_room_chat_message(room, user, message):
    return PrivateChatMessage.objects.create(user=user, room=room, content=message)

@database_sync_to_async
def pub_connect_user(room, user):
    return room.connect_user(user)

@database_sync_to_async
def pub_disconnect_user(room, user):
    return room.disconnect_user(user)

@database_sync_to_async
def pub_get_room_or_error(room_id):
	"""
	Tries to fetch a room for the user
	"""
	try:
		room = PublicChatRoom.objects.get(pk=room_id)
	except PublicChatRoom.DoesNotExist:
		raise ClientError("ROOM_INVALID", "Invalid room.")
	return room

@database_sync_to_async
def pub_get_room_chat_messages(room, page_number):
	try:
		qs = PrivateChatMessage.objects.by_room(room)
		p = Paginator(qs, DEFAULT_PUBLIC_ROOM_CHAT_MESSAGE_PAGE_SIZE)

		payload = {}
		messages_data = None
		new_page_number = int(page_number)  
		if new_page_number <= p.num_pages:
			new_page_number = new_page_number + 1
			s = LazyRoomChatMessageEncoder()
			payload['messages'] = s.serialize(p.page(page_number).object_list)
		else:
			payload['messages'] = "None"
		payload['new_page_number'] = new_page_number
		return json.dumps(payload)
	except Exception as e:
		print("EXCEPTION: " + str(e))
		return None

class LazyRoomChatMessageEncoder(Serializer):
	def get_dump_object(self, obj):
		dump_object = {}
		dump_object.update({'msg_type': MSG_TYPE_MESSAGE})
		dump_object.update({'msg_id': str(obj.id)})
		dump_object.update({'user_id': str(obj.user.id)})
		dump_object.update({'username': str(obj.user.username)})
		dump_object.update({'message': str(obj.content)})
		dump_object.update({'profile_image': str(obj.user.profile_image.url)})
		dump_object.update({'natural_timestamp': calculate_timestamp(obj.timestamp)})
		return dump_object