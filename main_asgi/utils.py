from django.core.serializers.python import Serializer
from django.contrib.humanize.templatetags.humanize import naturaltime
from datetime import datetime
from django.contrib.humanize.templatetags.humanize import naturalday

from .models import PrivateChatRoom, Notification, UserChannel
from .constants import *

class LazyNotificationEncoder(Serializer):
    def get_dump_object(self, obj):
        dump_object = {}
        dump_object.update({'sender': str(obj.from_user.username)})
        dump_object.update({'profile_image': str(obj.from_user.profile_image.url)})
        dump_object.update({'notification_content': str(obj.verb)})
        dump_object.update({'natural_timestamp': calculate_timestamp(obj.timestamp)})
        return dump_object



def find_or_create_private_chat(user1, user2):
	try:
		chat = PrivateChatRoom.objects.get(user1=user1, user2=user2)
	except PrivateChatRoom.DoesNotExist:
		try:
			chat = PrivateChatRoom.objects.get(user1=user2, user2=user1)
		except PrivateChatRoom.DoesNotExist:
			chats = list(PrivateChatRoom.objects.filter(user1=user1, user2=user2)) + list(PrivateChatRoom.objects.filter(user1=user2, user2=user1)) + list(PrivateChatRoom.objects.filter(user1=user1, user2=user1)) + list(PrivateChatRoom.objects.filter(user1=user2, user2=user2))
			for chat in chats:
				chat.delete()
			chat = PrivateChatRoom(user1=user1, user2=user2)
			chat.save()
	return chat

def calculate_timestamp(timestamp):
	"""
	1. Today or yesterday:
		- EX: 'today at 10:56 AM'
		- EX: 'yesterday at 5:19 PM'
	2. other:
		- EX: 05/06/2020
		- EX: 12/28/2020
	"""
	ts = ""
	# Today or yesterday
	if (naturalday(timestamp) == "today") or (naturalday(timestamp) == "yesterday"):
		str_time = datetime.strftime(timestamp, "%I:%M %p")
		str_time = str_time.strip("0")
		ts = f"{naturalday(timestamp)} at {str_time}"
	# other days
	else:
		str_time = datetime.strftime(timestamp, "%m/%d/%Y")
		ts = f"{str_time}"
	return str(ts)

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



def get_or_create_channel(user, state):
	context = []
	try:
		channel = UserChannel.objects.get(user=user)
		noti_count = noti_count = len(Notification.objects.filter(target=user))
		context.append(channel)
		context.append(noti_count)
	except UserChannel.DoesNotExist:
		channel = UserChannel.objects.create(user=user, is_connected=True,state=state)
		channel.save()
		noti_count = noti_count = len(Notification.objects.filter(target=user))
		context.append(channel)
		context.append(noti_count)

	return context
		
