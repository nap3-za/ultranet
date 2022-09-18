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
from .utils import calculate_timestamp, LazyRoomChatMessageEncoder, LazyNotificationEncoder
from .exceptions import ClientError
from .constants import *

from .models import PrivateChatMessage, PrivateChatRoom, PublicChatRoom, PublicChatMessage,Notification, UserChannel
from friend.models import FriendList
from account.models import BaseAccount
from django.conf import settings
from friend.models import FriendRequest


class MainConsumer(AsyncJsonWebsocketConsumer):

	async def connect(self):
		print("[+] connect" + str(self.scope["user"]))

		# let everyone connect. But limit read/write to authenticated users
		await self.accept()

	async def join(self, data):
		print("[+] join")
		print(f"[>> data : {data}")
		"""
		data :
			> room_id
			> room_type
		"""
		try:
			room = await join_room(data["room_id"], self.scope["user"].username, room_type=data["room_type"])
		except Exception as e:
			return await self.handle_client_error(e)
			print(f"[>> join : {str(e)}")

		await self.channel_layer.group_add(
			room.group_name,
			self.channel_name,
		)

		payload = await get_notifications(self.scope["user"])
		if payload != None:
			payload = json.loads(payload)
			if len(payload['notifications']) > 0:
				await self.send_json({ 
						"noti_payload": "true",
						"notifications": payload['notifications'],
					})

		if data["room_type"] == "public_channel":
			# Notify the group that someone has joined and send new user count
			await update_user_channel_state(self.scope["user"].username, state=room.group_name)
			timestamp = calculate_timestamp(timezone.now())
			user_count = await get_num_connected_users(room)
			noti_count = await get_noti_count(self.scope["user"].username)
			await self.send_json({
					"setup_room": "true",
					"user_count": str(user_count),
					"noti_count": str(noti_count),
				})
			await self.channel_layer.group_send(
				room.group_name,
				{
					"type": "on.pub.condiscon",
					"username": self.scope["user"].username,
					"timestamp": timestamp,
					"msg": "Joined",
					"user_count": user_count,
					"noti_count": str(noti_count),
				}
			)
			
		elif data["room_type"] == "private_channel":
			# Notify the group that someone has joined
			timestamp = calculate_timestamp(timezone.now())
			noti_count = await get_noti_count(self.scope["user"].username)
			await update_user_channel_state(self.scope["user"].username, state=room.group_name)
			await self.send_json({
					"setup_room": "true",
					"noti_count": str(noti_count),
				})

		elif data["room_type"] == "user_channel":
			noti_count = await get_noti_count(self.scope["user"].username)
			await update_user_channel_state(self.scope["user"].username, state=room.group_name)
			await self.send_json({
				"noti_count": str(noti_count),
			})

		print(str(self.scope['user'])+"[>> joined a channel")

	async def leave(self, data):
		print("[+] leave")
		print(f"[>> data : {data}")
		"""
		data :
			> room_id
			> room_type
		"""
		try:
			room = await join_room(data["room_id"], self.scope["user"].username, room_type=data["room_type"])
		except ClientError as e:
			return await self.handle_client_error(e)
			print(f"[>> leaves : {str(e)}")

		await self.channel_layer.group_discard(
			room.group_name,
			self.channel_name,
		)

		if data["room_type"] == "public_channel":
			# Notify the group that someone has joined and send new user count
			await update_user_channel_state(self.scope["user"].username, state="")
			print("Successfully left")

		elif data["room_type"] == "private_channel":
			# Notify the group that someone has joined
			timestamp = calculate_timestamp(timezone.now())

			await update_user_channel_state(self.scope["user"].username, state="")
			print("Successfully left")

		elif data["room_type"] == "user_channel":
			await update_user_channel_state(self.scope["user"].username, state="")

		print("[>> "+self.scope['user'].username+"left channel a channel")

	async def get_notification(self, data):
		try:
			notification = await get_latest_notification(self.scope["user"])
			print(notification[1])
			await self.send_json({
					"incoming_notification": "true",
					"notification_content": notification[0],
					"natural_timestamp": notification[1],
					"profile_image": notification[2],
					"sender": notification[3],
					"noti_id": notification[4],
				})
		except Exception as e:
			print(f"[>> get notification : {e}")

	async def send_fr_notification(self, data):
		print("[+] send fr notification")
		friend_request_data = None
		try:
			friend_request_data = await get_friend_request_data(sender=self.scope["user"], receiver=data["receiver"])
		except Exception as e:
			print(f"[>> send fr noti : {e}")

		if friend_request_data[0] and friend_request_data[1]:

			if friend_request_data[1].state == "self_account_details":
				if friend_request_data[2] == "false":
					fr_count = str(friend_request_data[3])
				else:
					fr_count = "1"
				await self.channel_layer.group_send(
					friend_request_data[1].current_channel,
				{
					"incoming_notification": "true",
					"notification_content": friend_request_data[3][0],
					"natural_timestamp": friend_request_data[3][1],
					"profile_image": friend_request_data[3][2],
					"sender": friend_request_data[3][3],
					"noti_id": friend_request_data[3][4],
					"fr": "true",
					"fr_count": fr_count,
				})

			else:
				if friend_request_data[2] == "false":
					fr_count = str(friend_request_data[3])
				else:
					fr_count = "1"
				await self.channel_layer.group_send(
					friend_request_data[1].current_channel,
				{
					"incoming_notification": "true",
					"notification_content": friend_request_data[3][0],
					"natural_timestamp": friend_request_data[3][1],
					"profile_image": friend_request_data[3][2],
					"sender": friend_request_data[3][3],
					"noti_id": friend_request_data[3][4],
					"fr": "false",
				})


		elif friend_request_data == None:
			await self.send_json({
				"error": "No friend request , do that again and you will be terminated"
				})

	async def reload_recipient(self, data):

		try:
			recipient = await get_recipient(data["recipient"])
			if recipient != None and not "form" in str(recipient.current_channel):
				await self.channel_layer.group_send(
					recipient.current_channel,
				{
					"reload": "true",
				})

		except Exception as e:
			print(f"[>> reload : {e}")

	async def send_accept_notification(self, data):
		print("[+] send accept notification")
		user_data = None
		try:
			user_data = await get_user_data(sender=self.scope["user"], receiver=data["receiver"])
		except Exception as e:
			print(f"[>> send accept noti : {e}")

		if user_data[0] and user_data[2]:

			if user_data[1] == "true":
				await self.channel_layer.group_send(
					user_data[0].current_channel,
				{
					"incoming_notification": "true",
					"notification_content": user_data[2][0],
					"natural_timestamp": user_data[2][1],
					"profile_image": user_data[2][2],
					"sender": user_data[2][3],
					"noti_id": user_data[2][4],
					"chat_btn": "true",
				})

			else:
				await self.channel_layer.group_send(
					user_data[0].current_channel,
				{
					"incoming_notification": "true",
					"notification_content": user_data[2][0],
					"natural_timestamp": user_data[2][1],
					"profile_image": user_data[2][2],
					"sender": user_data[2][3],
					"noti_id": user_data[2][4],
					"chat_btn": "false",
				})


		elif user_data == None:
			await self.send_json({
				"error": "No friend request , do that again and you will be terminated"
				})

	commands = {
		'join': join,
		'leave':leave,
		'get_notification': get_notification,
		'send_fr_notification': send_fr_notification,
		'send_accept_notification': send_accept_notification,
		'reload': reload_recipient
	}

	async def send_notification(self, event):
		noti_count = await get_noti_count(self.scope["user"].username)
		await self.send_json({
				"noti": "true",
				"receiver": event["receiver"],
				"noti_count": noti_count
			})

	async def send_msg_notification(self, notification):
		print("[>> send private chat msg notification to receiver")
		try:
			current_group = await get_channel_state(notification.target)
			await self.channel_layer.group_send(
				current_group,
				{
					"type": "send.notification",
					"receiver": str(notification.target),
				}
			)
			print("Notification sent")
		except Exception as e:
			print(f"[>> send pri msg notification : {e}")

	async def new_chat(self, event):
		await self.send_json({
				"msg_type": event["new_msg"],
				"message":event["message"],
				"sender": event["sender"],
				"natural_timestamp": event["natural_timestamp"],
				"profile_image": event["profile_image"],
				"sender_id": event["sender_id"],
				"username": event["sender"],
				"unread_count": event["unread_count"]
			})

	async def update_chats(self, msg, sender, msg_id, notification_id):
		print("update_chats")
		try:
			noti_target = await get_noti_target(notification_id)
			current_group = await get_channel_state(noti_target)
			msg_data = await get_msg_data(msg_id)
			timestamp = calculate_timestamp(timezone.now())
			await self.channel_layer.group_send(
				current_group, {
					"type":"new.chat",
					"new_msg": str(msg_data[2]),
					"message":msg,
					"sender": sender,
					"natural_timestamp": timestamp,
					"username": sender,
					"profile_image": str(msg_data[1]),
					"sender_id": str(msg_data[0]),
					"unread_count": msg_data[3],
				}
			)
		except Exception as e:
			print("[>> update_chat :"+str(e))

	async def send_private_message(self, data):
		print("[>> send_private msg")
		if len(data["message"].lstrip()) == 0:
			raise ClientError(204, "Message cannot be nothing")

		room = await get_room(data["room_id"], room_type="private_room")
		procceed = await send_message_validation(data["room_id"], self.scope["user"], msg_type="private_msg")

		if procceed:
			msg = await create_pri_chat_message(data["room_id"], self.scope["user"], data["message"])
			await self.channel_layer.group_send(
				room.group_name,
				{
					"type": "pri.message",
					"profile_image": self.scope["user"].profile_image.url,
					"username": self.scope["user"].username,
					"user_id": self.scope["user"].id,
					"message": data["message"],
					"message_id": msg[0].id,
				}
			)


			if msg[2]:
				await self.update_chats(msg[0].content, str(msg[0].user), msg[0].id, msg[1].id)

			elif msg[1] != None:
				await self.send_msg_notification(msg[1])

			else:
				print("No need to send notification")

	async def send_public_message(self, data):

		print("[>> send public chat msg")
		if len(data["message"].lstrip()) == 0:
			raise ClientError(204, "Message cannot be nothing")

		room = await get_room(data["room_id"], room_type="public_room")
		procceed = await send_message_validation(data["room_id"], self.scope["user"], msg_type="public_msg")
		
		if procceed:
			msg = await create_pub_chat_message(data["room_id"], self.scope["user"], data["message"])
			await self.channel_layer.group_send(
				room.group_name,
				{
					"type": "pub.message",
					"profile_image": self.scope["user"].profile_image.url,
					"username": self.scope["user"].username,
					"user_id": self.scope["user"].id,
					"message": data["message"],
				}
			)
			print("Msg sent")

			if msg[1] != None:
				await self.send_msg_notification(msg[1])
			else:
				print("No need to send notification")

		else:
			pass

	async def send_private_chat_messages(self, data):
		await self.display_progress_bar(True)
		payload = await get_private_chat_messages(data["room_id"], data['page_number'], user=self.scope["user"])
		if payload != None:
			payload = json.loads(payload)
			await self.send_json(
				{
					"messages_payload": "messages_payload",
					"messages": payload["messages"],
					"new_page_number": payload["new_page_number"],
				},
			)
		else:
			raise ClientError(204,"Something went wrong retrieving the chatroom messages.")
		await self.display_progress_bar(False)
	
	async def send_public_chat_messages(self, data):
		print("[>> send messages to public")
		await self.display_progress_bar(True)
		payload = await get_public_chat_messages(data["room_id"], data['page_number'])
		if payload != None:
			payload = json.loads(payload)
			await self.send_json(
				{
					"messages_payload": "messages_payload",
					"messages": payload["messages"],
					"new_page_number": payload["new_page_number"],
				},
			)
			print("[>> public messages sent")
		else:
			raise ClientError(204,"Something went wrong retrieving the chatroom messages.")
		await self.display_progress_bar(False)

	async def send_user_info(self, data):
		print("[>> get user info")
		await self.display_progress_bar(True)
		payload = await get_user_info(data["room_id"], self.scope["user"])
		if payload != None:
			payload = json.loads(payload)
			await self.send_json({
					"user_info": payload['user_info'],
				})
			print("[+] user info sent")

		else:
			raise ClientError(204, "Something went wrong retrieving the other users account details.")
		await self.display_progress_bar(False)
	
	async def pri_message(self, event):
		"""
		Called when someone has messaged our chat.
		"""
		# Send a message down to the client
		print("[>> pri_message")

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
				},
			)
			print("Chatconsumer chat_message done")
		except Exception as e:
			print(str(e))
	
	async def pub_message(self, event):
		"""
		Called when someone has messaged our chat.
		"""
		# Send a message down to the client
		print("[>> pri_message")
		timestamp = calculate_timestamp(timezone.now())
		try:
			await self.send_json({
				"msg_type": MSG_TYPE_MESSAGE,
				"profile_image": event["profile_image"],
				"username": event["username"],
				"user_id": event["user_id"],
				"message": event["message"],
				"natural_timestamp": timestamp,
			})

			print("Public msg sent")

		except Exception as e:
			print(str(e))

	chat_commands = {
		'get_user_info': send_user_info,
		'get_private_chat_messages': send_private_chat_messages,
		'get_public_chat_messages': send_public_chat_messages,
		'send_private_msg': send_private_message,
		'send_public_msg': send_public_message,
	}



	async def receive_json(self, content):
		print("[+] receive_json")
		try:
			if content["command"] == "chat":
				await self.chat_commands[content['type']](self,content)
			else:
				await self.commands[content['command']](self,content)
		except Exception as e:
			print(str(e))

	async def display_progress_bar(self, is_displayed):
		"""
		1. is_displayed = True
		- Display the progress bar on UI
		2. is_displayed = False
		- Hide the progress bar on UI
		"""
		await self.send_json(
			{
				"display_progress_bar": is_displayed
			}
		)
	



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
		
	# Sends a msg to the public room to notify when someone joins / leaves
	async def on_pub_condiscon(self, event):
		self.send_json({
			"setup_room": "",
			"metadata": [str(event["username"]),str(event["timestamp"]), str(event["msg"])],
			"user_count": event["user_count"],
		})

@database_sync_to_async
def join_room(room_id, username, room_type):
	print("[>> get room")
	if room_type == "private_channel":
		try:
			room = PrivateChatRoom.objects.get(id=int(room_id))
			user = BaseAccount.objects.get(username=username)
			# If you are one of the room participants
			if user == room.user1:
				room.connect_user(user)
				return room 
			elif user == room.user2:
				room.connect_user(user)
				return room 
			else:
				print(f"[>> [-] {user.username} tring to join invalid room")
				return None

		except Exception as e:
			print(f"[>> [-] {str(e)}")
			return None
	elif room_type == "public_channel":
		try:
			room = PublicChatRoom.objects.get(id=int(room_id))
			user = BaseAccount.objects.get(username=username)
			if room.admin == user:
				room.connect_user(user)
				print(f"[>> {user.username} connected to : {room.title}")
				return room

			elif ((room.accessibility == "All Fiends") or (room.accessibility == "Selected Friends")) and (user in room.allowed_friends.all()):
				room.connect_user(user)
				print(f"[>> {user.username} connected to : {room.title}")
				return room
			elif room.accessibility == "Everyone":
				room.connect_user(user)
				print(f"[>> {user.username} connected to : {room.title}")
				return room
			else:
				print(f"[>> {user.username} tring to join invalid room")
				return None
		except Exception as e:
			print(f"[>> [-] {str(e)}")
			return None
	elif room_type == "user_channel":
		try:
			room = UserChannel.objects.get(id=int(room_id))
			user = BaseAccount.objects.get(username=username)
			if room.user == user:
				room.connect()
				print(f"[>> {user.username} connected to own channel")
				return room
			else:
				print(f"[>> {user.username} tring to join invalid room")
				return None
		except Exception as e:
			print(f"[>> [-] {str(e)}")
			return None

@database_sync_to_async
def leave_room(room_id, username, room_type):
	print("[>> leave room")
	if room_type == "private_channel":
		try:
			room = PrivateChatRoom.objects.get(id=int(room_id))
			user = BaseAccount.objects.get(username=username)
			# If you are one of the room participants
			if user == room.user1:
				room.disconnect_user(user)
				return room 
			elif user == room.user2:
				room.disconnect_user(user)
				return room 
			else:
				print(f"[>> [-] {user.username} tring to join invalid room")
				return None

		except Exception as e:
			print(f"[>> [-] {str(e)}")
			return None
	elif room_type == "public_channel":
		try:
			room = PublicChatRoom.objects.get(id=int(room_id))
			user = BaseAccount.objects.get(username=username)
			if room.admin == user:
				room.disconnect_user(user)
				print(f"[>> {user.username} disconnected to : {room.title}")
				return room

			elif ((room.accessibility == "All Fiends") or (room.accessibility == "Selected Friends")) and (user in room.allowed_friends.all()):
				room.disconnect_user(user)
				print(f"[>> {user.username} disconnected to : {room.title}")
				return room
			else:
				print(f"[>> {user.username} tring to join invalid room")
				return None
		except Exception as e:
			print(f"[>> [-] {str(e)}")
			return None

	elif room_type == "user_channel":
		try:
			room = UserChannel.objects.get(id=int(room_id))
			user = BaseAccount.objects.get(username=username)
			if room.user == user:
				room.connect()
				print(f"[>> {user.username} connected to own channel")
				return room
			else:
				print(f"[>> {user.username} tring to join invalid room")
				return None
		except Exception as e:
			print(f"[>> [-] {str(e)}")
			return None

@database_sync_to_async
def get_room(room_id, room_type):
	print("[>> get room")
	try:
		if room_type == "private_room":
			return PrivateChatRoom.objects.get(id=int(room_id))
		elif room_type == "public_room":
			return PublicChatRoom.objects.get(id=int(room_id))
		elif room_type == "user_room":
			return UserChannel.objects.get(id=int(room_id))	
	except Exception as e:
		print(f"[>> get_room : {e}")

@database_sync_to_async
def send_noti(username):
	pass

@database_sync_to_async
def get_num_connected_users(room):
	if room.users:
		return len(room.users.all())
	return 0

@database_sync_to_async
def get_noti_count(username):
	try:
		user = BaseAccount.objects.get(username=username)
		noti_count = len(Notification.objects.filter(target=user, read=False))
		return noti_count
	except Exception as e:
		print(f"[>> {e}")

@database_sync_to_async
def get_user_info(room_id, user):
	print("[>> get user info sync func")
	"""
	Retrieve the user info for the user you are chatting with
	"""
	try:
		room = PrivateChatRoom.objects.get(id=int(room_id))
		# Determine who is who h
		other_user = room.user1
		
		print(room)
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
		raise ClientError
		raise ClientError("DATA_ERROR", "Unable to get that users information.")
	return None

@database_sync_to_async
def get_private_chat_messages(room_id, page_number, **kwargs):
	print("[>> get private chat room msgs")
	try:
		room = PrivateChatRoom.objects.get(id=int(room_id))
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
def get_public_chat_messages(room_id, page_number):
	try:
		room = PublicChatRoom.objects.get(id=int(room_id))
		qs = PublicChatMessage.objects.by_room(room)
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
		print("[>> get public chat messages :" + str(e))
		return None

@database_sync_to_async
def send_message_validation(room_id, user, msg_type):
	print("[>> send msg validation")
	if msg_type == "private_msg":
		try:
			room = PrivateChatRoom.objects.get(id=int(room_id))
			if (user == room.user1) or (user == room.user2):
				return True 
			else:
				print(f"[>> {user.username} tried sending an illegal msg")
				return False
		except Exception as e:
			print("[>> send msg validation"+str(e))
			return False
	elif msg_type == "public_msg":
		try:
			room = PublicChatRoom.objects.get(id=int(room_id))
			if user == room.admin:
				return True
			elif ((room.accessibility == "All Fiends") or (room.accessibility == "Selected Friends")) and (user in room.allowed_friends.all()):
				return True 
			elif room.accessibility == "Everyone":
				return True
			else:
				print(f"[>> {user.username} tried sending an illegal msg")
				return False
		except Exception as e:
			print("[>> msg_validation"+str(e))
			return False

@database_sync_to_async
def create_pri_chat_message(room_id, user, message):
	try:
		room = PrivateChatRoom.objects.get(id=int(room_id))
		msg = PrivateChatMessage.objects.create(user=user, room=room, content=message)
		msg.save()
		receiver = room.user1
		if user == room.user1:
			receiver = room.user2
		notification = None

		if receiver.current_channel == room.group_name:
			msg.seen = True
			msg.save()

		if receiver.current_channel != room.group_name:
			notification = Notification.objects.create(
			target=receiver,
			from_user=user,
			redirect_url=f"{settings.BASE_URL}/account/{user.username}/details/",
			verb=f"{user.username} sent you a message.",
			)
			notification.save()
		else:
			print("notification not created beacause both users are connected")
			

		receiver_channel = UserChannel.objects.get(user=receiver)
		if receiver_channel.state == "chats":
			return [msg, notification, True]
		else:
			return [msg, notification, False]
	except Exception as e:
		print(str(e))

@database_sync_to_async
def create_pub_chat_message(room_id, user, message):
	try:
		room = PublicChatRoom.objects.get(id=int(room_id))
		msg = PublicChatMessage.objects.create(user=user, room=room, content=message)
		msg.save()
		notification = None
		admin = room.admin
		if user == admin:
			pass
		else:
			if admin.current_channel == room.group_name:
				msg.seen = True
				msg.save()

			if admin.current_channel != room.group_name:
				notification = Notification.objects.create(
				target=admin,
				from_user=user,
				redirect_url=f"{settings.BASE_URL}/account/{user.username}/details/",
				verb=f"{user.username} sent a message to the chat {room.title}.",
				)
				notification.save()
			else:
				print("notification not created beacause both admin is in the chat")
			if admin.state == "chats":
				return [msg, notification, True]
			else:
				return [msg, notification, False]
	except Exception as e:
		print(str(e))

@database_sync_to_async
def update_user_channel_state(username,state):
	print("[>> updating state")
	try:
		user = BaseAccount.objects.get(username=username)
		user.current_channel = state
		user.save()
	except Exception as e:
		print(f"[>> get channel state : {str(e)}")

@database_sync_to_async
def get_channel_state(username):
	try:
		user = BaseAccount.objects.get(username=username)
		return user.current_channel
	except Exception as e:
		print(str(e))

@database_sync_to_async
def get_latest_notification(user):
	try:
		latest_notification = list(Notification.objects.filter(target=user).order_by('timestamp'))[-1]
		if user.state == "notifications_home":
			latest_notification.read = True 
			latest_notification.save()
		return [str(latest_notification.verb), str(calculate_timestamp(latest_notification.timestamp)), str(latest_notification.from_user.profile_image.url), str(latest_notification.from_user.username), str(latest_notification.id)]
	except Exception as e:
		print(f"[>> get latest noti : {str(e)}")

@database_sync_to_async
def get_noti_target(noti_id):
	try:
		noti = Notification.objects.get(id=int(noti_id))
		return noti.target.username
	except Exception as e:
		print(f"[>> get latest noti : {str(e)}")

@database_sync_to_async
def get_msg_data(msg_id):
	try:
		msg = PrivateChatMessage.objects.get(id=int(msg_id))
		profile_image = msg.user.profile_image.url 
		msg_type = "new"
		sender_id = msg.user.id
		if len(PrivateChatMessage.objects.filter(room=msg.room)) > 1:
			msg_type = "recent"

		unread_count = len(PrivateChatMessage.objects.filter(seen=False))

		
		return [sender_id, profile_image, msg_type, unread_count]

	except Exception as e:
		print("[>> get_msg_type : "+str(e))	


@database_sync_to_async
def get_notifications(user):
	print("[>> get notifications")
	try:
		qs = list(Notification.objects.filter(target=user, read=False).order_by('-timestamp'))[0:5]
		payload = {}
		if len(qs) > 0:
			s = LazyNotificationEncoder()
			payload['notifications'] = s.serialize(qs)
		else:
			payload['notifications'] = "None"
		return json.dumps(payload)
	except Exception as e:
		raise Exception(e)
		
		print("EXCEPTION: " + str(e))
	return None


@database_sync_to_async
def get_friend_request_data(sender, receiver):
	print("[+] get friend request")
	try:
		receiver = BaseAccount.objects.get(username=receiver)
		friend_request = None
		try:
			friend_requests = list(FriendRequest.objects.filter(sender=sender, receiver=receiver, is_active=True))
			if len(friend_requests) > 1:
				friend_request = friend_requests.pop()
				for fr in friend_requests:
					fr.delete()

				if len(FriendRequest.objects.filter(receiver=receiver, is_active=True)) >= 2:
					return [friend_request,receiver, "false"]
				elif len(FriendRequest.objects.filter(receiver=receiver, is_active=True)) == 1:
					return [friend_request,receiver, "true"]

			elif len(friend_requests) == 0:
				return None
			elif len(friend_requests) == 1:
				notification = None
				try:
					notification = Notification.objects.create(from_user=sender, target=receiver, verb=f"{sender.username} sent you a friend request")
					notification.save()
				except Exception as e:
					print(f"[>> get friend request : 1 : {e}")

				if receiver.state == "notifications_home":
					notification.read=True,
					notification.save()

				if len(FriendRequest.objects.filter(receiver=receiver, is_active=True)) >= 2:
					return [friend_requests[0],receiver, "false", [str(notification.verb), str(calculate_timestamp(notification.timestamp)), str(notification.from_user.profile_image.url), str(notification.from_user.username), str(notification.id)]]
				elif len(FriendRequest.objects.filter(receiver=receiver, is_active=True)) == 1:
					return [friend_requests[0],receiver, "true", [str(notification.verb), str(calculate_timestamp(notification.timestamp)), str(notification.from_user.profile_image.url), str(notification.from_user.username), str(notification.id)]]


		except Exception as e:
			print(f"[>> get friend request : 2 : {e}")
	except Exception as e:
		print(f"[>> get friend request : 3 : {e}")

@database_sync_to_async
def get_user_data(sender, receiver):
	print("[+] get friend request")
	try:
		receiver = BaseAccount.objects.get(username=receiver)
		notification = None

		try:
			notification = Notification.objects.create(from_user=sender, target=receiver, verb=f"{sender.username} accepted your friend request")
			notification.save()
		except Exception as e:
			print(f"[>> get friend request : 1 : {e}")

		if receiver.state == "notifications_home":
			notification.read=True,
			notification.save()

		if receiver.state == f"{sender.username}_account_details":
			return [receiver, "true", [str(notification.verb), str(calculate_timestamp(notification.timestamp)), str(notification.from_user.profile_image.url), str(notification.from_user.username), str(notification.id)]]
		else:
			return [receiver, "false", [str(notification.verb), str(calculate_timestamp(notification.timestamp)), str(notification.from_user.profile_image.url), str(notification.from_user.username), str(notification.id)]]
	except Exception as e:
		print(f"[>> get friend request : 3 : {e}")




@database_sync_to_async
def get_recipient(username):
	try:
		return BaseAccount.objects.get(username=username)
	except Exception as e:
		print(f"[>> get recipient : {e}")
		return None



