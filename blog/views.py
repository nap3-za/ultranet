import json
from django.core.paginator import Paginator
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.utils import timezone
from friend.models import FriendList
from .models import Comment, Choice, Content
import random
from .forms import (
	ContentCreationForm,
	ContentUpdateForm,
	CommentUpdateForm,
	CommentCreationForm,
	)
from account.models import AccountSettings, Account
from main_asgi.models import Notification
from .utils import get_trending

# fixing needed
@login_required(login_url="login")
def feed_view(request, *args, **kwargs):
	context = {}
	auth_user = request.user

	if not auth_user.is_authenticated:
		return redirect('login')
	elif auth_user.is_authenticated:
		auth_user_account = get_object_or_404(Account, pk=auth_user.pk)
		try:
			contents = Content.objects.filter(draft=False).order_by('-timestamp')
		except Exception as e:
			return redirect("404")

		contents_list = []
		for content in contents:
			is_friend = True
			is_mine = False
			if content.author in auth_user_account.friend_list.friends.all():
				is_friend = True
			if content.author == auth_user_account:
				is_mine = True

			if is_mine or is_friend or content.visibility == "Anyone":
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
					if len(Choice.objects.filter(content=content))<=1:
						content.delete()
					else:
						vote_count=Choice.objects.filter(content=content)[0].total_votes
						contents_list.append((content, is_mine, comments, vote_count))
				else:
					contents_list.append((content, is_mine, comments))

		p = Paginator(contents_list, 10)
		page = request.GET.get('page')
		content_paginated = p.get_page(page)
		context['contents'] = content_paginated

		context['trending'] = get_trending()
	else:
		return redirect("403")

	context["channel"] = get_object_or_404(Account, pk=auth_user.pk).channel_name
	context["connect_general"] = True
	return render(request, "blog/feed.html", context)

"""
Creates post objects and links them to content objs
"""

tag_options = [
	"Operating Systems",
	"Competetive Programming",
	"Software",
	"Programming Languages",
	"Hardware",
]

@login_required(login_url="login")
def create_content_view(request, *args, **kwargs):
	context = {}
	auth_user = request.user
	if not auth_user.is_authenticated:
		return redirect('login')
	elif auth_user.is_authenticated:
		auth_user_account = get_object_or_404(Account, pk=auth_user.pk)

		if request.method == "POST" and request.POST:	
			form = ContentCreationForm(request.POST)
			if form.is_valid():
				content = form.save(user=auth_user_account)
				tags = []
				if request.POST.get('tags'):
					tags = dict(request.POST)['tags']
					for tag in tags:
						if not tag in tag_options:
							return redirect("blog:content", content_id=content.id)
				content.tags = tags
				content.save()
				return redirect(f"blog:content", content_id=content.id)
			else:
				context['form'] = ContentCreationForm(request.POST)
		else:				
			context['form'] = ContentCreationForm()
	else:
		return redirect('home')

	context["content_type"] = kwargs.get("content_type")		
	context["connect_general"] = True
	return render(request, "blog/create.html", context)


@login_required(login_url="login")
def update_content_view(request, *args, **kwargs):
	context = {}
	auth_user = request.user
	if not auth_user.is_authenticated:
		return redirect('login')
	elif auth_user.is_authenticated:
		auth_user_account = get_object_or_404(Account, pk=auth_user.pk)
		try:
			content = get_object_or_404(Content, id=kwargs.get("content_id"))
			context["content"] = content
			context["content_type"] = content.content_type
		except:
			return redirect("404")

		if request.method == "POST" and request.POST:	
			form = ContentUpdateForm(request.POST, instance=content)
			if form.is_valid():
				title = form.cleaned_data["title"]
				text = form.cleaned_data["text"]
				visibility = form.cleaned_data["visibility"]
				draft = form.cleaned_data["draft"]
				tags = []
				if request.POST.get('tags'):
					tags = dict(request.POST)['tags']
					for tag in tags:
						if not tag in tag_options:
							return redirect("blog:content", content_id=content.id)
				content.title = title
				content.visibility = visibility
				content.draft = draft
				content.tags = tags

				if content.content_type=="Poll":
					updated_choices_raw = text.replace('\r','').split('\n')
					updated_choices = []
					for choice in updated_choices_raw:
						choice = choice.lower().replace(' ','').replace('\r','')
						if not choice in updated_choices:
							updated_choices.append(choice)

					old_choices = []
					for old_choice in Choice.objects.filter(content=content):
						old_choice = old_choice.value.lower().replace(' ','').replace('\r','')
						if not old_choice in old_choices:
							old_choices.append(old_choice)

					new_choices = []
					print(f"old_choices : {old_choices}")

					old_objs = Choice.objects.filter(content=content)
					for choice in updated_choices:
						choice = choice.lower().replace(' ','').replace('\r','')
						if choice in old_choices:
							print(choice)
							old_obj = old_objs.get(value=choice)
							new_choices.append(old_obj)
							old_objs = old_objs.exclude(id=old_obj.id)
						else:
							new_choice = Choice.objects.create(content=content, value=choice)
							new_choice.save()
							new_choices.append(new_choice)

					for old_obj in old_objs:
						if not old_obj in new_choices:
							old_obj.delete()

					
					print(f"new choices : {new_choices}")
					print(f"updated choices : {updated_choices}")

					content_text=""
					for choice in updated_choices:
						content_text+='\n'+choice

					content.text=content_text[1:]
					content.save()
				else:
					content.text = text
					content.save()

				return redirect(f"blog:content", content_id=content.id)
			else:
				context['form'] = ContentUpdateForm(request.POST, instance=content)
		else:
			context['form'] = ContentUpdateForm(instance=content)
	else:
		return redirect('home')


		
	context["connect_general"] = True
	return render(request, "blog/update.html", context)

@login_required(login_url="login")
def create_comment_view(request, *args, **kwargs):
	auth_user = request.user

	if not auth_user.is_authenticated:
		return redirect("404")
	elif auth_user.is_authenticated:
		auth_user_account = get_object_or_404(Account, pk=auth_user.pk)
		if request.method == "POST" and request.POST:
			form = CommentCreationForm(request.POST)
			if form.is_valid():
				content_id = kwargs.get("content_id")
				content = get_object_or_404(Content, id=content_id)
				form.save(user=auth_user_account, content=content, reply=kwargs.get("reply"))
				return redirect("blog:content", content_id=content_id)
			else:
				return redirect("400")
		else:
			return redirect("403")
	else:
		return redirect("login")

@login_required(login_url="login")
def update_comment_view(request, *args, **kwargs):
	auth_user = request.user

	if not auth_user.is_authenticated:
		return redirect("404")
	elif auth_user.is_authenticated:
		auth_user_account = get_object_or_404(Account, pk=auth_user.pk)
		if request.method == "POST" and request.POST:
			form = CommentUpdateForm(request.POST)
			if form.is_valid():
				comment = get_object_or_404(Comment, id=kwargs.get("comment_id"))
				form.save(comment=comment)
				return redirect("blog:content", content_id=content_id)
			else:
				return redirect("400")
		else:
			return redirect("403")
	else:
		return redirect("login")
"""
Deactivates content
"""
@login_required(login_url="login")
def delete_content_view(request, *args, **kwargs):
	context = {}
	auth_user = request.user
	content_id = kwargs.get("content_id")

	if not auth_user.is_authenticated:
		return redirect('login')

	elif auth_user.is_authenticated:

		try:
			content = Content.objects.get(id=content_id)
			content.delete()
			return redirect('feed')
		except:
			return redirect("404")

@login_required(login_url="login")
def content_view(request, *args, **kwargs):
	context = {}
	auth_user = request.user

	if not auth_user.is_authenticated:
		return redirect("login")
	elif auth_user.is_authenticated:
		auth_user_account = get_object_or_404(Account, id=auth_user.id)
		content = get_object_or_404(Content, id=kwargs.get("content_id"))
		if content.draft==True and content.author!=auth_user_account:
			return redirect("404")

		if content.content_type=="Poll":
			context["content_type"]="Poll"
			poll_values_raw = Choice.objects.filter(content=content).order_by('-timestamp')
			poll_values = []
			if len(poll_values_raw) <= 1:
				return redirect("404")
			else:
				all_votes=0
				for poll_value in poll_values_raw:
					votes = len(poll_value.votes.all())
					all_votes+=votes
					poll_values.append((poll_value, votes))

			context['poll_values'] = poll_values
			context['all_votes'] = all_votes

		elif content.content_type=="Post":
			context["content_type"]="Post"

		if content.author == auth_user_account:
			context['is_mine'] = True
		else:
			context['is_mine'] = False
			if content.visibility=="Friends" and not auth_user_account in content.author.friends.all():
				return redirect("404")

			content.views.add(auth_user_account)
			content.save()

		context["content"]=content

		comments = []
		for comment in Comment.objects.filter(content=content, reply=None).order_by('-timestamp'):
			c_is_mine = False
			if comment.author == auth_user:
				c_is_mine = True
			replies = Comment.objects.filter(content=content, reply=comment)
			comments.append((comment, c_is_mine, replies))
		context['comments'] = comments	
			
	else:
		return redirect("404")

	context["connect_general"] = True
	return render(request, "blog/details.html", context)

"""
Selects poll values on polls using AJAX
"""
@login_required(login_url="login")
def select_view(request, *args, **kwargs):
	payload = {}
	auth_user = request.user

	if not auth_user.is_authenticated:
		return redirect('login')

	elif auth_user.is_authenticated:
		auth_user_account = get_object_or_404(Account, id=auth_user.id)
		choice = get_object_or_404(Choice, id=kwargs.get("value_id"))

		action = None
		if auth_user_account in choice.votes.all():
			choice.clean_values(user=auth_user_account)
			choice.save()
			action = "unselect"
		else:
			choice.clean_values(user=auth_user_account)
			choice.save()
			choice.add_vote(user=auth_user_account)
			choice.save()
			action = "select"
		payload["action"] = action

	return HttpResponse(json.dumps(payload), content_type="application/json")

"""
Likes , Dislikes , Unlikes , Undislikes
"""
@login_required(login_url="login")
def interact_view(request, *args, **kwargs):
	payload = {}
	auth_user = request.user

	if not auth_user.is_authenticated:
		return redirect('login')

	elif auth_user.is_authenticated:
		auth_user_account = get_object_or_404(Account, id=auth_user.id)
		content = get_object_or_404(Content, id=request.GET.get("content_id"))
		if content.draft==True and content.author!=auth_user_account:
			return redirect("404")
		
		try:
			func = request.GET.get("function")
		except:
			return redirect("404")

		if func == "like":
			content.undislike(user=auth_user_account)
			content.save()
			if auth_user_account in content.likes.all():
				content.unlike(user=auth_user_account)
				content.save()
			elif auth_user_account not in content.likes.all():
				content.add_like(user=auth_user_account)
				content.save()

		elif func == "dislike":
			content.unlike(user=auth_user_account)
			content.save()
			if auth_user_account in content.dislikes.all():
				content.undislike(user=auth_user_account)
				content.save()
			elif auth_user_account not in content.likes.all():
				content.add_dislike(user=auth_user_account)
				content.save()
		else:
			return redirect("404")
	
	payload['new_count'] = content.likes.count
	return HttpResponse(json.dumps(payload), content_type="application/json")

"""
Deletes comments using content id
"""
@login_required(login_url="login")
def delete_comment_view(request, *args, **kwargs):

	auth_user = request.user
	context = {}

	if not auth_user.is_authenticated:
		return redirect("login")

	if auth_user.is_authenticated:
		auth_user_account = get_object_or_404(Account, pk=auth_user.pk)
		comment = get_object_or_404(Comment, id=kwargs.get("comment_id"), author=auth_user_account)
		content_id = comment.content.id
		comment.delete()
		return redirect("blog:content", content_id=content_id)

	return redirect("403")

