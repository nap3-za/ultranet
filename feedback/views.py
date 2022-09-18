import json

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from .models import Report
from .forms import ReportCreationForm, QuestionCreationForm, FeedbackCreationForm
from account.models import Account
from blog.models import Content , Comment
from django.http import HttpResponse

# Create your views here.

@login_required(login_url="login")
def create_report_view(request, *args, **kwargs):
	payload = {}
	auth_user = request.user

	if not auth_user.is_authenticated:
		return redirect('login')
	elif auth_user.is_authenticated:
		auth_user_account = get_object_or_404(Account, pk=auth_user.pk)

		if request.method == "POST" and request.POST:	
			form = ReportCreationForm(request.POST)
			if form.is_valid():
				report = form.save(user=auth_user_account)
				obj_type = form.cleaned_data['obj']
				obj_id = form.cleaned_data['obj_id']
				obj = None
				if report:
					if obj_type == 'Account':
						obj = Account.objects.get(id=obj_id)
					elif obj_type == 'Content':
						obj = Content.objects.get(id=obj_id)
					elif obj_type == 'Comment':
						obj = Comment.objects.get(id=obj_id)

					if obj and len(Report.objects.filter(obj_id=obj_id)) >= 50:
						obj.delete()
						payload['response'] = "redirect"
					else:
						payload['response'] = "Successful"
				else:
					payload['response'] = "Inconsistent data"
			else:
				payload['response'] = "Inconsistent data"
		else:				
			pass

	return HttpResponse(json.dumps(payload), content_type="application/json")

# Done
@login_required(login_url="login")
def send_feedback_view(request, *args, **kwargs):
	context = {}
	auth_user = request.user

	if not auth_user.is_authenticated:
		return redirect('login')

	elif auth_user.is_authenticated:
		auth_user_account = get_object_or_404(Account, id=auth_user.id)
		if request.method == "POST" and request.POST:
			form = FeedbackForm(request.POST)
			if form.is_valid():
				feedback = form.save(commit=False)
				feedback.author = auth_user_account
				feedback.save()
				return redirect("200")
			else:
				context['form'] = form
		else:
			pass
	else:
		return redirect("login")

	context["connect_general"] = True
	context["channel"] = get_object_or_404(Account, id=auth_user.id).channel_name
	return render(request, "feedback/send_feedback.html", context)

# Done
@login_required(login_url="login")
def send_question_view(request, *args, **kwargs):

	context = {}
	auth_user = request.user

	if not auth_user.is_authenticated:
		return redirect('login')

	elif auth_user.is_authenticated:
		auth_user_account = get_object_or_404(Account, id=auth_user.id)
		if request.method == "POST" and request.POST:
			form = QuestionForm(request.POST)
			if form.is_valid():
				question = form.save(commit=False)
				question.author = auth_user_account
				question.save()
				return redirect("200")
			else:
				context['form'] = form
		else:
			pass
	else:
		return redirect("login")

	context["connect_general"] = True
	context["channel"] = get_object_or_404(Account, id=auth_user.id).channel_name
	return render(request, "feedback/send_question.html", context)