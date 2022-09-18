from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from friend.models import FriendRequest
from .models import Notification
from account.models import Account as BaseAccount
# Create your views here.


@login_required(login_url="login")
def notifications_home_view(request, *args, **kwargs):
	context = {}
	auth_user = request.user

	if not auth_user.is_authenticated:
		return redirect("error:forbidden", origin=origin)
	elif auth_user.is_authenticated:
		auth_user_account = BaseAccount.objects.get(username=auth_user.username)
		try:
			notifications_container = []
			unread_notifications = Notification.objects.filter(target=auth_user_account).order_by('-timestamp')
			for noti in unread_notifications:
				if not noti.read:
					noti.read=True
					noti.save()

			context["notifications"] = unread_notifications
		except Exception as e:
			print(str(e))

	context["con_general"] = False
	channel = get_create_update_channel(user=auth_user_account, view="notifications_home")
	context["channel"] = channel
	return render(request, "notifications/home.html", context)


@login_required(login_url="login")
def clear_notifications_view(request, *args, **kwargs):
	context = {}
	auth_user = request.user

	if not auth_user.is_authenticated:
		return redirect("error:forbidden", origin=origin)
	elif auth_user.is_authenticated:
		auth_user_account = BaseAccount.objects.get(username=auth_user.username)
		try:
			notifications = Notification.objects.filter(target=auth_user_account)
			for noti in notifications:
				noti.delete()
			return redirect("notifications:noti_home")
		except Exception as e:
			print(str(e))

	context["notifications"] = []
	context["con_general"] = False
	channel = get_create_update_channel(user=auth_user_account, view="notifications")
	context["channel"] = channel
	return render(request, "notifications/home.html", context)


@login_required(login_url="login")
def delete_notification_view(request, *args, **kwargs):
	context = {}
	auth_user = request.user

	if not auth_user.is_authenticated:
		return redirect("error:forbidden", origin=origin)
	elif auth_user.is_authenticated:
		auth_user_account = BaseAccount.objects.get(username=auth_user.username)
		noti_id = request.GET.get("noti_id")
		try:
			
			notification = Notification.objects.get(target=auth_user_account, id=int(noti_id))
			notification.delete()
			return redirect("notifications:noti_home")
		except Exception as e:
			print(str(e))

	context["notifications"] = []
	context["con_general"] = False
	channel = get_create_update_channel(user=auth_user_account, view="notifications")
	context["channel"] = channel
	return render(request, "notifications/home.html", context)