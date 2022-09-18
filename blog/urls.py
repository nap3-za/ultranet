from django.contrib import admin
from django.urls import path, include


from . import views

from account import views as account_views

from .views import (
	# CRUD
	create_content_view,
	create_comment_view,

	update_content_view,
	update_comment_view,

	delete_content_view,
	delete_comment_view,

	feed_view,
	content_view,
	select_view,
	interact_view,
	)

app_name="blog"

urlpatterns = [

	path('create/<str:content_type>/', create_content_view, name="create_content"),
	path('<int:content_id>/', content_view, name="content"),
	path('poll/select/<int:value_id>/', select_view, name="select"),
	path('<int:content_id>/update/', update_content_view, name="update_content"),
	path('<int:content_id>/delete/', delete_content_view, name="delete_content"),

	path('<int:content_id>/<int:reply>/comments/create/', create_comment_view, name="create_comment"),
	path('content/<comment_id>/edit/', update_comment_view, name="update_comment"),
	path('content/<comment_id>/delete/', delete_comment_view, name="delete_comment"),

	path('interact/', interact_view, name="interact"),
]