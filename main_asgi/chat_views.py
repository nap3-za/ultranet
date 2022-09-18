from django.shortcuts import render, redirect
from django.urls import reverse
from django.conf import settings
from django.core.paginator import Paginator
from django.http import HttpResponse
from django.utils import timezone
from django.contrib.auth.decorators import login_required
from urllib.parse import urlencode
import json
from django.utils import timezone

from itertools import chain
from datetime import datetime
import pytz
from django.contrib.auth.decorators import login_required


from friend.models import FriendList
from account.models import Account
from .models import PrivateChatRoom, PrivateChatMessage , PublicChatRoom, PublicChatMessage, Notification

from .forms import PubChatCreationForm, PubChatUpdateForm
# Create your views here.

DEBUG = False


def private_chat_room_view(request, *args, **kwargs):
	room_id = request.GET.get("room_id")
	user = request.user
	if not user.is_authenticated:
		base_url = reverse('login')
		query_string = urlencode({'next': f"/chat/?room_id={room_id}"})
		url = f"{base_url}?{query_string}"
		return redirect(url)

	context = {}
	auth_user_account = Account.objects.get(username=user.username)



	context["BASE_URL"] = settings.BASE_URL
	if room_id:
		context["room_id"] = room_id
		try:
			room = PrivateChatRoom.objects.get(id=room_id, is_deleted=False)
			context['room'] = room 
			context["receiver"] = room.user1
			if auth_user_account == room.user1:
				context["receiver"] = room.user2
		except Exception as e:
			print(str(e))

	context['debug'] = True
	context['debug_mode'] = settings.DEBUG
	context["con_general"] = False
	context["channel"] = UserChannel.objects.get(user=auth_user_account)
	
	return render(request, "chat/room.html", context)

def get_recent_chatroom_messages(user):
	"""
	sort in terms of most recent chats (users that you most recently had conversations with)
	"""
	# 1. Find all the rooms this user is a part of 
	rooms1 = PrivateChatRoom.objects.filter(user1=user, is_active=True)
	rooms2 = PrivateChatRoom.objects.filter(user2=user, is_active=True)

	# 2. merge the lists
	rooms = list(chain(rooms1, rooms2))

	# 3. find the newest msg in each room
	m_and_f = []
	for room in rooms:
		# Figure out which user is the "other user" (aka friend)
		if room.user1 == user:
			friend = room.user2
		else:
			friend = room.user1

		# confirm you are even friends (in case chat is left active somehow)
		friend_list = FriendList.objects.get(user=user)
		if not friend_list.is_mutual_friend(friend):
			chat = find_or_create_private_chat(user, friend)
			chat.is_active = False
			chat.save()
		else:	
			# find newest msg from that friend in the chat room
			try:
				message = PrivateChatMessage.objects.filter(room=room, user=friend).latest("timestamp")
			except PrivateChatMessage.DoesNotExist:
				# create a dummy message with dummy timestamp
				today = datetime(
					year=1950, 
					month=1, 
					day=1, 
					hour=1,
					minute=1,
					second=1,
					tzinfo=pytz.UTC
				)
				message = PrivateChatMessage(
					user=friend,
					room=room,
					timestamp=today,
					content="",
				)
			m_and_f.append({
				'message': message,
				'friend': friend
			})

	print(m_and_f)
	return sorted(m_and_f, key=lambda x: x['message'].timestamp, reverse=True)

# Ajax call to return a private chatroom or create one if does not exist
def create_or_return_private_chat(request, *args, **kwargs):
	print("ChatViews : create_or_return_private_chat")
	user1 = request.user
	payload = {}
	if user1.is_authenticated:
		user1 = Account.objects.get(username=request.user.username)
		if request.method == "POST":
			user2_id = request.POST.get("user2_id")
			try:
				user2 = Account.objects.get(pk=user2_id)
				print(f"User 1 : {user1.username}")
				print(f"User 2 : {user2.username}")
				if user1 == user2:
					print("User 1 and User 2 are the same")
				elif user1 != user2:
					chat = find_or_create_private_chat(user1, user2)
					print("Successfully got the chat")
					payload['response'] = "Successfully got the chat."
					payload['chatroom_id'] = chat.id
			except Account.DoesNotExist:
				payload['response'] = "Unable to start a chat with that user."
	else:
		payload['response'] = "You can't start a chat if you are not authenticated."
	return HttpResponse(json.dumps(payload), content_type="application/json")

@login_required(login_url="login")
def private_chats_view(request, *args, **kwargs):
	context = {}
	auth_user = request.user

	if not auth_user.is_authenticated:
		return redirect("error:forbidden", origin=origin)
	elif auth_user.is_authenticated:
		auth_user_account = Account.objects.get(username=auth_user.username)
		try:
			chats1 = list(PrivateChatRoom.objects.filter(user1=auth_user_account, is_deleted=False))
			chats2 = list(PrivateChatRoom.objects.filter(user2=auth_user_account, is_deleted=False))
			chats = chats1 + chats2
			chats_container = []
			potential_chats = list(FriendList.objects.get(user=auth_user_account).friends.all())
			for chat in chats:
				if len(PrivateChatMessage.objects.filter(room=chat)) > 0:
					recent_msg = list(PrivateChatMessage.objects.filter(room=chat).order_by("-id"))[0]
					user = chat.user1
					if chat.user1 == auth_user_account:
						user = chat.user2
					unread = len(PrivateChatMessage.objects.filter(room=chat,user=user, seen=False))
					chats_container.append((chat, recent_msg, user, unread))
					potential_chats.remove(user)
					
				else:
					pass
			
	
					
			context['chats'] = chats_container
			context['potential_chats'] = potential_chats
				
		except Exception as e:
			print(str(e))
				
	def get_or_create_channel(user, state):
		context = []
		try:
			channel = UserChannel.objects.get(user=user)
			noti_count = noti_count = len(Notification.objects.filter(target=user))
			channel.state = "chats"
			channel.save()
			context.append(channel)
			context.append(noti_count)
		except UserChannel.DoesNotExist:
			channel = UserChannel.objects.create(user=user, is_connected=True,state=state)
			channel.save()
			noti_count = noti_count = len(Notification.objects.filter(target=user))
			context.append(channel)
			context.append(noti_count)
		return context	

	context['debug'] = True
	context['debug_mode'] = settings.DEBUG
	context["con_general"] = False
	data = get_or_create_channel(auth_user_account, "chats")
	context["channel"] = data[0]
	context["noti_count"] = data[1]
	return render(request, "chat/chats.html", context)

@login_required(login_url="login")
def chats_update_view(request, *args, **kwargs):
	payload = {}
	auth_user = request.user

	if not auth_user.is_authenticated:
		return redirect("error:forbidden", origin=origin)
	elif auth_user.is_authenticated:
		auth_user_account = Account.objects.get(username=auth_user.username)

		try:
			chats1 = list(PrivateChatRoom.objects.filter(user1=auth_user_account))
			chats2 = list(PrivateChatRoom.objects.filter(user2=auth_user_account))
			chats = chats1 + chats2
			chats_container = []
			potential_chats = list(FriendList.objects.get(user=auth_user_account).friends.all())
			for chat in chats:
				if len(PrivateChatMessage.objects.filter(room=chat)) > 0:
					recent_msg = list(PrivateChatMessage.objects.filter(room=chat).order_by("-id"))[0]
					user = chat.user1
					if chat.user1 == auth_user_account:
						user = chat.user2
					unread = len(PrivateChatMessage.objects.filter(room=chat,user=user, seen=False))
					chats_container.append((chat, recent_msg, user, unread))
					potential_chats.remove(user)
					
				else:
					pass
					
			payload['chats'] = chats_container
			payload['potential_chats'] = potential_chats
				
		except Exception as e:
			print(str(e))

	return HttpResponse(json.dumps(payload), content_type="application/json")

@login_required(login_url="login")
def delete_private_chat_view(request, *args, **kwargs):
	print("del")
	context = {}
	auth_user = request.user
	context["errors"] = []
	if not auth_user.is_authenticated:
		return redirect("error:forbidden", origin=origin)
	elif auth_user.is_authenticated:
		auth_user_account = Account.objects.get(username=auth_user.username)
		room_id = kwargs.get("room_id")
		if room_id:
			try:
				room = PrivateChatRoom.objects.get(id=room_id, is_deleted=False)
			except Exception as e:
				context["errors"].append("the room does not exist")
				print(str(e))

			if room.user1 == auth_user_account or room.user2 == auth_user_account:
				room.is_deleted = True
				room.save()
				return redirect("chat:chats")
			else:
				context["errors"].append("You are not a participant of the room , try this again and you will be terminated")


	return redirect("chat:chats")

DEBUG = False
@login_required(login_url="login")
def public_chat_home_view(request, *args, **kwargs):
    context = {}
    auth_user = request.user
    if not auth_user.is_authenticated:
        return redirect("error:forbidden", origin=origin)
    elif auth_user.is_authenticated:
        auth_user_account = Account.objects.get(username=auth_user.username)
        try:
            rooms = PublicChatRoom.objects.filter(admin=auth_user_account)
            rooms_container = []
            for room in rooms:
                if room.accessibility == "Everyone":
                    msg_count = len(PublicChatMessage.objects.filter(room=room))
                    rooms_container.append((room, 0,msg_count))
                elif room.accessibility == "All Friends":
                    msg_count = len(PublicChatMessage.objects.filter(room=room))
                    rooms_container.append((room, 0, msg_count))
                elif room.accessibility == "Selected Friends":
                    msg_count = len(PublicChatMessage.objects.filter(room=room))
                    rooms_container.append((room, 1, msg_count, list(room.allowed_friends.all())))
            context["rooms"] = rooms_container
            if len(rooms) >= 5:
                context["qualify"] = False
            else:
                context["qualify"] = True
        except Exception as e:
            raise e
            print(str(e))
    context["con_general"] = True
    data = get_or_create_channel(auth_user_account, state="chat_home")
    context["channel"] = data[0]
    context["noti_count"] = data[1]

    return render(request, "public_chat/home.html", context)

@login_required(login_url="login")
def public_chat_room_view(request, *args, **kwargs):
    context = {}
    context["errors"] = []
    auth_user = request.user
    room_name = kwargs.get("room_name")

    if not auth_user.is_authenticated:
        return redirect("error:forbidden", origin=origin)
    elif auth_user.is_authenticated and room_name:
        try:
            auth_user_account = Account.objects.get(username=auth_user.username)
            try:
                room = PublicChatRoom.objects.get(room_name=room_name)
            except Exception as e:
                print("[>> public chat room view : "+str(e))
                context["errors"].append("No room found , try again")
                return render(request, "public_chat/home.html", context)
            if room.admin == auth_user_account:
                context['debug_mode'] = settings.DEBUG
                context['debug'] = DEBUG
                context['room'] = room
                context['room_title'] = room.title
            elif ((room.accessibility == "All Fiends") or (room.accessibility == "Selected Friends")) and (auth_user_account in room.allowed_friends.all()):
                context['debug_mode'] = settings.DEBUG
                context['debug'] = DEBUG
                context['room'] = room
                context['room_title'] = room.title
            elif room.accessibility == "Everyone":
                context['debug_mode'] = settings.DEBUG
                context['debug'] = DEBUG
                context['room'] = room
                context['room_title'] = room.title
            else:
                context["errors"].append("No room found , try again")
                return render(request, "public_chat/home.html", context)

        except Exception as e:
            print(str(e))
            return redirect("error:does_not_exist", origin="chat")

    context["con_general"] = False
	
    get_or_create_channel(auth_user_account, "general")

    return render(request, "public_chat/room.html", context)

@login_required(login_url="login")
def public_chat_create_view(request, *args, **kwargs):
    context = {}
    context["errors"] = []
    auth_user = request.user
    if not auth_user.is_authenticated:
        return redirect("error:forbidden", origin=origin)
    elif auth_user.is_authenticated:
        auth_user_account = Account.objects.get(username=auth_user.username)
        friends_list = []
        try:
            for friend in auth_user_account.friends.all():
                friends_list.append(friend.user.username,)
        except Exception as e:
            print(str(e))
        context["friends_list"] = friends_list
        if len(PublicChatRoom.objects.filter(admin=auth_user_account)) >= 5:
            context["errors"].append("You have reached your max number of rooms , delete some to create some")
        if request.method == "POST":
            print("Method is post")
            if len(PublicChatRoom.objects.filter(admin=auth_user_account)) >= 5:
                context["errors"].append("You have reached your max number of rooms , delete some to create some")
            form = PubChatCreationForm(request.POST)
            if form.is_valid():
                print("Form is valid")
                room_name = form.cleaned_data["room_name"]
                title = form.cleaned_data["title"]
                allowed_friends = form.cleaned_data["allowed_friends"]
                accessibility = form.cleaned_data["accessibility"]
                print(accessibility)
                if accessibility == "Selected Friends":
                    if len(PublicChatRoom.objects.filter(room_name=room_name)) == 0:
                        print("Access is select")
                        if len(allowed_friends) == 0:
                            context["errors"].append("Please check the Select friends checkox and select friends")
                        else:
                            pub_room = PublicChatRoom.objects.create(admin=auth_user_account, room_name=room_name, title=title, accessibility=accessibility)
                            pub_room.save()
                            auth_friends = list(FriendList.objects.get(user=auth_user_account).friends.all())
                            for friend in allowed_friends:
                                try:
                                    friend_obj = Account.objects.get(username=friend)
                                    if friend_obj in auth_friends:
                                        pub_room.allowed_friends.add(friend_obj)
                                        pub_room.save()
                                except Exception as e:
                                    print(str(e))
                            return redirect("public_chat:room", room_name=room_name)
                    else:
                        context["errors"].append("That room name is taken") 

                elif accessibility == "Everyone":
                    print("Access is Everyone")
                    if len(PublicChatRoom.objects.filter(room_name=room_name)) == 0:
                        pub_room = PublicChatRoom.objects.create(admin=auth_user_account, room_name=room_name, title=title, accessibility=accessibility)
                        pub_room.save()
                        return redirect("chat:public_room", room_name=room_name)
                    else:
                        context["errors"].append("That room name is taken") 
                elif accessibility == "All Friends":
                    print("Access is friends")
                    if len(PublicChatRoom.objects.filter(room_name=room_name)) == 0:
                        pub_room = PublicChatRoom.objects.create(admin=auth_user_account, room_name=room_name, title=title, accessibility=accessibility)
                        auth_friends = list(FriendList.objects.get(user=auth_user_account).friends.all())
                        for friend in auth_friends:
                            pub_room.allowed_friends.add(friend)
                            pub_room.save()
                        pub_room.save() 
                        return redirect("chat:public_room", room_name=room_name) 
                    else:
                        context["errors"].append("That room name is taken") 

            elif request.method == "POST":
                form = PubChatCreationForm(request.POST)
                context["form"] = form
    context["con_general"] = True

    data = get_or_create_channel(auth_user_account, state="general")
    context["channel"] = data[0]
    context["noti_count"] = data[1]
    return render(request, "public_chat/create.html", context)
        
@login_required(login_url="login")
def public_chat_update_view(request, *args, **kwargs):
    context = {}
    context["errors"] = []
    auth_user = request.user
    if not auth_user.is_authenticated:
        return redirect("error:forbidden", origin=origin)
    elif auth_user.is_authenticated:
        auth_user_account = Account.objects.get(username=auth_user.username)
        friends_list = []
        try:
            room_name = kwargs.get("room_name")
            room = PublicChatRoom.objects.get(room_name=room_name)
            for friend in auth_user_account.friends.all():
                status = False
                friend_obj = Account.objects.get(username=friend)
                if friend_obj in room.allowed_friends.all():
                    status = True
                friends_list.append((friend_obj.username, status))

        except Exception as e:
            print(str(e))
        context["friends_list"] = friends_list
        context["room"] = room
        if len(PublicChatRoom.objects.filter(admin=auth_user_account)) >= 5:
            context["errors"].append("You have reached your max number of rooms , delete some to create some")
        if request.method == "POST":
            if len(PublicChatRoom.objects.filter(admin=auth_user_account)) >= 5:
                context["errors"].append("You have reached your max number of rooms , delete some to create some")
            form = PubChatUpdateForm(request.POST)
            if form.is_valid():
                room_name = form.cleaned_data["room_name"]
                title = form.cleaned_data["title"]
                allowed_friends = form.cleaned_data["allowed_friends"]
                accessibility = form.cleaned_data["accessibility"]
                if (room.room_name == room_name) or (len(PublicChatRoom.objects.filter(room_name=room_name)) == 0):
                    room.room_name = room_name
                    room.title = title
                    room.save()
                    if accessibility == "Selected Friends":
                        if len(allowed_friends) == 0:
                            context["errors"].append("Please check the Select friends checkox and select friends")
                        else:
                            auth_friends = list(FriendList.objects.get(user=auth_user_account).friends.all())
                            for old_friend in auth_friends:
                                if old_friend in room.allowed_friends.all():
                                    room.allowed_friends.remove(old_friend)
                                    room.save()
                            for friend in allowed_friends:
                                try:
                                    friend_obj = Account.objects.get(username=friend)
                                    if friend_obj in auth_friends:
                                        room.allowed_friends.add(friend_obj)
                                        room.save()
                                except Exception as e:
                                    print(str(e))
                            return redirect("public_chat:room", room_name=room_name)
                    elif accessibility == "Everyone":
                        room.accessibility = accessibility
                        room.save()
                        return redirect("public_chat:room", room_name=room_name)


                    elif accessibility == "All Friends":
                        auth_friends = list(FriendList.objects.get(user=auth_user_account).friends.all())
                        
                        for friend in auth_friends:
                            room.allowed_friends.add(friend)
                            room.save()
                        room.save() 
                        return redirect("public_chat:room", room_name=room_name) 


            elif request.method == "POST":
                form = PubChatUpdateForm(request.POST)
                context["form"] = form
    context["con_general"] = True

    get_or_create_channel(auth_user_account, "general")
    
    return render(request, "public_chat/update.html", context)
       
@login_required(login_url="login")
def delete_pub_room_view(request, *args, **kwargs):
    payload = {}
    auth_user = request.user
    if not auth_user.is_authenticated:
        return redirect("error:forbidden", origin=origin)
    elif auth_user.is_authenticated:
        auth_user_account = Account.objects.get(username=auth_user.username)
        room_id = kwargs.get("room_id")
        try:
            room = PublicChatRoom.objects.get(id=room_id)
            if room.admin == auth_user_account:
                room.delete()
                return redirect("chat:public_home")
        except Exception as e:
            print(str(e))
            return redirect("error:does_not_exist", origin="chat")

@login_required(login_url="login")
def reset_view(request, *args, **kwargs):
    auth_user = request.user
    if not auth_user.is_authenticated:
        return redirect("error:forbidden", origin=origin)
    elif auth_user.is_authenticated:
        auth_user_account = Account.objects.get(username=auth_user.username)
        try:
            room_name = kwargs.get("room_name")
            room = PublicChatRoom.objects.get(room_name=room_name)
            if not room.admin == auth_user_account:
                return redirect("error:forbidden", origin="chat")
            elif room.admin == auth_user_account:
                messages = PublicChatMessage.objects.filter(room=room)
                for msg in messages:
                    msg.delete()
                for user in room.users.all():
                    room.disconnect_user(user)
                room.save()

                return redirect("chat:public_home")
        except Exception as e:
            print("[-] Error : "+str(e))

    return redirect("chat:public_home")