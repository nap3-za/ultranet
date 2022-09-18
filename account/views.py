import os
import cv2
import json
import base64
import requests

from django.core import files
from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse
from django.core.files.storage import default_storage
from django.core.files.storage import FileSystemStorage
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.decorators import login_required
from django.conf import settings
from django.core.paginator import Paginator
from django.views import View
from django.utils.decorators import method_decorator

from .forms import (
	RegistrationForm,
	SettingsAccountForm,
	SettingsNotificationsForm,
	SettingsPrivacyForm,
	AuthenticationForm,
	UpdateProfileForm,
	DeleteAccountForm,
	)

from .models import Account, AccountSettings
from blog.models import Content, Comment, Choice
from friend.models import FriendList, FriendRequest
from feedback.models import Question
from friend.friend_request_status import FriendRequestStatus
from friend.utils import get_mutual_friends
# from main_asgi.models import Notification, UserChannel
from .relation import RelationStatus
from .utils import get_account_settings , get_relation,get_or_create_friend_list


# Create your views here.
# print([[error for error in field.errors] for field in form])

TEMP_PROFILE_IMAGE_NAME = "temp_profile_image.png"

def register_view(request, *args, **kwargs):
	context = {}
	auth_user = request.user

	if auth_user.is_authenticated:
		return redirect('home')

	elif not auth_user.is_authenticated:
		if request.method == "POST" and request.POST:
			form = RegistrationForm(request.POST)
			if form.is_valid():
				auth_user_account = form.save()
				login(request, auth_user_account)
				return redirect("account:redirect")
			else:
				context["form"] = form
		else:
			context["form"] = RegistrationForm()
	else:
		return redirect("403")
	return render(request, 'account/register.html', context)

@login_required(login_url="login")
def redirect_view(request, *args, **kwargs):
	context = {}
	return render(request, "account/redirect.html", context)

def login_view(request, *args, **kwargs):
	auth_user = request.user
	context = {}

	if auth_user.is_authenticated:
		return redirect("home")

	elif not auth_user.is_authenticated:
		if request.method == 'POST' and request.POST:
			form = AuthenticationForm(request.POST)
			if form.is_valid():
				email = form.cleaned_data['email']
				password = form.cleaned_data['password']
				try:
					auth_user_account = authenticate(email=email, password=password)
				except:
					return redirect("login")

				if auth_user_account != None:
					login(request, auth_user_account)
					return redirect("feed")
				else:
					return redirect("login")
			else:
				context["form"] = form
		else:
			pass
	else:
		return redirect("403")

	return render(request, "account/login.html", context)

@login_required(login_url="login")
def logout_view(request):
	logout(request)
	return redirect("login")

@login_required(login_url="login")
def settings_view(request, *args, **kwargs):
	context = {}
	auth_user = request.user

	if not auth_user.is_authenticated:
		return redirect('login')
	elif auth_user.is_authenticated:
		auth_user_account = get_object_or_404(Account, pk=request.user.pk)
		if kwargs.get("page") == "account":

			if request.method == "POST" and request.POST:
				form = SettingsAccountForm(request.POST, instance=auth_user_account)
				if form.is_valid():
					form.save(instance=auth_user_account)
					return redirect("account:settings", page="main")
				else:
					context["form"] = form
			else:
				context["form"] = SettingsAccountForm(instance=auth_user_account)		
		elif kwargs.get("page") == "privacy":
	
			if request.method == "POST" and request.POST:
				form = SettingsPrivacyForm(request.POST, instance=auth_user_account.settings)
				if form.is_valid():
					form.save(instance=auth_user_account.settings)
					return redirect("account:settings", page="main")
				else:
					context["form"] = form
			else:
				context["form"] = SettingsPrivacyForm(instance=auth_user_account.settings)
		elif kwargs.get("page") == "notifications":
			if request.method == "POST" and request.POST:
				form = SettingsNotificationsForm(request.POST, instance=auth_user_account.settings)
				if form.is_valid():
					form.save(instance=auth_user_account.settings)
					return redirect("account:settings", page="main")
				else:
					context["form"] = form
			else:
				context["form"] = SettingsNotificationsForm(instance=auth_user_account.settings)

	context["channel"] = get_object_or_404(Account, pk=request.user.pk).channel_name
	context["connect_general"] = True
	return render(request, "account/settings.html", context)

@login_required(login_url="login")
def update_profile_view(request, *args, **kwargs):
	context = {}
	auth_user = request.user

	if not auth_user.is_authenticated:
		return redirect('login')
	elif auth_user.is_authenticated:
		auth_user_account = get_object_or_404(Account, pk=request.user.pk)

		if request.method == "POST" and request.POST:
			form = UpdateProfileForm(request.POST, instance=auth_user_account)
			if form.is_valid():
				form.save(instance=auth_user_account)
				return redirect("account:details", subject_username=auth_user_account.username)
			else:
				context["form"] = form
		else:
			context["form"] = UpdateProfileForm(instance=auth_user_account)
	else:
		return redirect("403")

	context["channel"] = auth_user_account.channel_name
	context["connect_general"] = True
	context["DATA_UPLOAD_MAX_MEMORY_SIZE"] = settings.DATA_UPLOAD_MAX_MEMORY_SIZE

	return render(request, "account/update_profile.html", context)

@login_required(login_url="login")
def delete_account_view(request, *args, **kwargs):
	context = {}
	auth_user = request.user

	if not auth_user.is_authenticated:
		return redirect('login')
	elif auth_user.is_authenticated:
		auth_user_account = get_object_or_404(Account, pk=request.user.pk)

		if request.method == "POST" and request.POST:
			form = DeleteAccountForm(request.POST)
			if form.is_valid():
				form.save(instance=auth_user_account)
				return redirect("register")
			else:
				context["form"] = form
		else:
			pass
	else:
		return redirect("403")

	context["channel"] = get_object_or_404(Account, pk=request.user.pk).channel_name
	context["connect_general"] = True
	return render(request, "account/delete.html", context)

@login_required(login_url="login")
def details_view(request, *args, **kwargs):
	context = {}
	auth_user = request.user

	if not auth_user.is_authenticated:
		return redirect('login')
	elif auth_user.is_authenticated:

		auth_user_account = get_object_or_404(Account, pk=request.user.pk)
		subject_account = get_object_or_404(Account, username=kwargs.get("subject_username"))
		
		context["subject"] = subject_account
		context["id"]=subject_account.id
		context["debug_mode"]=True

		is_self = False
		is_friend = False
		is_mutual_friend = False
		request_sent = FriendRequestStatus.NO_REQUEST_SENT.value

		if auth_user_account == subject_account:
			is_self = True
			context["subject_settings"] = get_account_settings(auth_user_account, subject_account, False, False)
			try:
				context['friends'] = get_or_create_friend_list(user=auth_user_account).friends.all()
				context["fr_count"] = len(FriendRequest.objects.filter(receiver=auth_user_account))
			except Exception as e:
				context["friends"] = []
				context["fr_count"] = 0

			draft_count = len(Content.objects.filter(author=auth_user_account, draft=True))
			if draft_count>=1:
				context["draft_count"]=draft_count
		elif auth_user_account != subject_account:
			if subject_account in auth_user_account.friend_list.friends.all():
				is_friend = True
				context["mututal_friends"] = get_mutual_friends(user1=auth_user_account, user2=subject_account)
			else:
				# CASE1: Request has been sent from THEM to YOU: FriendRequestStatus.THEM_SENT_TO_YOU
				if get_relation(user1=subject_account, user2=auth_user_account) == RelationStatus.USER1_TO_USER2:
					request_sent = FriendRequestStatus.THEM_SENT_TO_YOU.value
					context['pending_fr'] = FriendRequest.objects.get(sender=subject_account, receiver=auth_user_account).id
				# CASE2: Request has been sent from YOU to THEM: FriendRequestStatus.YOU_SENT_TO_THEM
				elif get_relation(user1=subject_account, user2=auth_user_account) == RelationStatus.USER2_TO_USER1:
					request_sent = FriendRequestStatus.YOU_SENT_TO_THEM.value
				# CASE4: No request sent from YOU or THEM: FriendRequestStatus.NO_REQUEST_SENT
				else:
					request_sent = FriendRequestStatus.NO_REQUEST_SENT.value

			if get_relation(user1=subject_account, user2=auth_user_account) == RelationStatus.MUTUAL_FRIEND:
				is_mutual_friend = True
				
			context["subject_settings"] = get_account_settings(auth_user_account, subject_account, is_friend, is_mutual_friend)
			
			if context["subject_settings"]["friends"]:
				context['friends'] = get_or_create_friend_list(user=subject_account).friends.all()

		# Timeline config
		if is_self or context["subject_settings"]["timeline"]:
			contents_list = []
			contents = Content.objects.filter(author=subject_account)
			for content in contents:
				is_friend = True
				is_mine = False
				if content.author in auth_user_account.friend_list.friends.all():
					is_friend = True
				if content.author == auth_user_account:
					is_mine = True


				if is_mine or (is_friend and content.draft==False) or (content.visibility == "Anyone" and content.draft==False):
					comments = []
					for comment in Comment.objects.filter(content=content, reply=None).order_by('-timestamp')[:5]:
						c_is_mine = False
						if comment.author == auth_user:
							c_is_mine = True
						replies = Comment.objects.filter(content=content, reply=comment)
						if len(replies)>=1:
							replies=replies[0]
						c_count = Comment.objects.filter(content=content)
						comments.append((comment, c_is_mine, replies, c_count))
					
					if content.content_type == 'Poll':
						vote_count=Choice.objects.filter(content=content)[0].total_votes
						print(vote_count)
						contents_list.append((content, is_mine, comments, vote_count))
					else:
						contents_list.append((content, is_mine, comments))

			p = Paginator(contents_list, 10)
			page = request.GET.get('page')
			content_paginated = p.get_page(page)
			context['contents'] = content_paginated
		
		context['is_self'] = is_self
		context['is_friend'] = is_friend
		context['is_mutual_friend'] = is_mutual_friend
		context['request_sent'] = request_sent

	else:
		return redirect("403")

	context["connect_general"] = True
	context["channel"] = auth_user_account.channel_name
	return render(request, "account/details.html", context)

def save_temp_profile_image_from_base64String(imageString, user):
	INCORRECT_PADDING_EXCEPTION = "Incorrect padding"
	try:
		if not os.path.exists(settings.TEMP):
			os.mkdir(settings.TEMP)
		if not os.path.exists(str(settings.TEMP) + "/" + str(user.pk)):
			os.mkdir(str(settings.TEMP) + "/" + str(user.pk))
		url = os.path.join(str(settings.TEMP) + "/" + str(user.pk),TEMP_PROFILE_IMAGE_NAME)
		storage = FileSystemStorage(location=url)
		image = base64.b64decode(imageString)
		with storage.open('', 'wb+') as destination:
			destination.write(image)
			destination.close()
		return url
	except Exception as e:
		# workaround for an issue I found
		if str(e) == INCORRECT_PADDING_EXCEPTION:
			imageString += "=" * ((4 - len(imageString) % 4) % 4)
			return save_temp_profile_image_from_base64String(imageString, user)
	return None
def crop_image_view(request, *args, **kwargs):
	payload = {}
	user = request.user
	if request.POST and user.is_authenticated:
		try:
			imageString = request.POST.get("image")
			url = save_temp_profile_image_from_base64String(imageString, user)
			img = cv2.imread(url)

			cropX = int(float(str(request.POST.get("cropX"))))
			cropY = int(float(str(request.POST.get("cropY"))))
			cropWidth = int(float(str(request.POST.get("cropWidth"))))
			cropHeight = int(float(str(request.POST.get("cropHeight"))))
			if cropX < 0:
				cropX = 0
			if cropY < 0: # There is a bug with cropperjs. y can be negative.
				cropY = 0
			crop_img = img[cropY:cropY+cropHeight, cropX:cropX+cropWidth]

			cv2.imwrite(url, crop_img)

			# delete the old image
			user.profile_image.delete()

			# Save the cropped image to user model
			user.profile_image.save("profile_image.png", files.File(open(url, 'rb')))
			user.save()

			payload['result'] = "success"
			payload['cropped_profile_image'] = user.profile_image.url

			# delete temp file
			os.remove(url)

		except Exception as e:
			raise e
			print("exception: " + str(e))
			payload['result'] = "error"
			payload['exception'] = str(e)
	return HttpResponse(json.dumps(payload), content_type="application/json")
