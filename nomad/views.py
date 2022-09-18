import random

from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required
from django.views import generic
from django.conf import settings

from account.models import Account
# from main_asgi.models import Notification, PrivateChatMessage, PrivateChatRoom
# from friend.utils import get_friend_request_or_false
# from blog.utils import get_content
# from feature.utils import get_resources

class HomeView(generic.TemplateView):
	template_name = "nomad/home.html"
	def get(self, request, *args, **kwargs):
		context = {}
		if request.user.is_authenticated:
			context = {}
			context["channel"] = get_object_or_404(Account, pk=request.user.id).channel_name
			context["con_general"] = True			
			context['welcome_msg'] = random.choice([
				'Welcome back ',
				'We\'ve missed you ',
				'Good to have you back ',
				'Now that you\'re back ',
				'Thanks for gracing us with your precense ',
				'Sup ',
			])
		return render(request, self.template_name, context)

class AboutView(generic.TemplateView):
	template_name = "nomad/about.html"
	def get(self, request, *args, **kwargs):
		context = {}
		if request.user.is_authenticated:
			context = {}
			context["con_general"] = True
			context["channel"] = get_object_or_404(Account, pk=request.user.id).channel_name
		return render(request, self.template_name, context)

class ContactView(generic.TemplateView):	
	template_name = "nomad/contact.html"
	def get(self, request, *args, **kwargs):
		context = {}
		context["whatsapp_link"] = settings.WHATSAPP_LINK
		context["telegram_link"] = settings.TELEGRAM_LINK
		context["phone_number"] = settings.PHONE_NUMBER
		context["email"] = settings.EMAIL_HOST
		context["physical_address"] = settings.PHYSICAL_ADDRESS
		if request.user.is_authenticated:
			context["con_general"] = True
			context["channel"] = get_object_or_404(Account, pk=request.user.id).channel_name
		return render(request, self.template_name, context)

class LegalDocsView(generic.TemplateView):
	template_name = "nomad/legal_docs.html"
	def get(self, request, *args, **kwargs):
		context = {}
		if request.user.is_authenticated:
			context = {}
			context["con_general"] = True
			context["channel"] = get_object_or_404(Account, pk=request.user.id).channel_name
		return render(request, self.template_name, context)

def page_not_found_view(request, *args, **kwargs):
	return render(request, "errors/404.html")	

def perm_denied_view(request, *args, **kwargs):
	return render(request, "errors/403.html")	

def server_error_view(request, *args, **kwargs):
	return render(request, "errors/500.html")	

def bad_request_view(request, *args, **kwargs):
	return render(request, "errors/400.html")	

def dummy_view(request, *args, **kwargs):
	return render(request, "dummies/bs5_profile_content.html")
