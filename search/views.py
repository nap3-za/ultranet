from django.http import HttpResponse
from django.shortcuts import render, redirect
from account.models import Account as BaseAccount
from blog.models import Content
from .forms import ResourceForm, UpdateResourceForm
from .models import Resource
from django.core.files.storage import default_storage
from django.core.files.storage import FileSystemStorage
import os
import cv2
import json
import base64
import requests
from django.core import files
from django.conf import settings
from django.contrib.auth.decorators import login_required
# Create your views here.

TEMP_PROFILE_IMAGE_NAME = "temp_profile_image.png"






"""
Searches for contents
"""
@login_required(login_url="login")
def search_view(request, *args, **kwargs):
	print("search")
	context = {}
	auth_user = request.user

	if not auth_user.is_authenticated:
		return redirect("error:forbidden", origin=origin)
	elif auth_user.is_authenticated:
		auth_user_account = BaseAccount.objects.get(username=auth_user.username)
		if request.method == "GET":
			search_query = request.GET.get("q")
			if len(search_query) > 0:
				try:
					contents = Content.objects.filter(is_active=True, draft=False, title__icontains=search_query, text__icontains=search_query).order_by('-timestamp').distinct()
				except Exception as e:
					return redirect("error:does_not_exist", origin=origin)

		contents_list = []

		for content in contents:
			is_friend = False
			is_mine = False
			friends = FriendList.objects.get(user=content.author).friends.all()
			if auth_user_account in friends:

				is_friend = True
			if content.author == auth_user_account:
				is_mine = True

			if is_friend or content.visibility == "Public":
				if content.kind == "Poll":
					poll_values = Choice.objects.filter(is_active=True, poll=content.poll).order_by('value')
					contents_list.append((content, is_mine, is_friend, poll_values))
				else:
					contents_list.append((content, is_mine, is_friend))

		print(contents_list)
		p = Paginator(contents_list, 5)
		page = request.GET.get('page')
		content_paginated = p.get_page(page)
		context['contents'] = content_paginated

		if len(contents_list) > 0:
			try:
				featured = random.choice(Content.objects.filter(is_active=True, draft=False, visibility="Public", kind="Post").order_by('-timestamp'))
			except:
				pass
			context['featured'] = featured

	context["con_general"] = True
	return render(request, "blog/search.html", context)

