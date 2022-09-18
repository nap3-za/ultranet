from django.urls import path

from .notifications_views import(
	notifications_home_view,
	delete_notification_view,
	clear_notifications_view
	)

app_name = 'notifications'

urlpatterns = [
	path('notifications/home/',  notifications_home_view, name="home"),
	path('notification/delete/', delete_notification_view, name="delete"),
	path("notifications/clear/", clear_notifications_view, name="clear"),
]