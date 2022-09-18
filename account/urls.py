from django.urls import path

from . import views

app_name="account"

urlpatterns = [
	path('redirect/', views.redirect_view, name="redirect"),
	path('update_profile/', views.update_profile_view, name="update_profile"),
	path('settings/<str:page>/', views.settings_view, name="settings"),
	path('details/<str:subject_username>/', views.details_view, name="details"),
	path('delete/', views.delete_account_view, name="delete"),
	path('<user_id>/edit/cropImage/', views.crop_image_view, name="crop_image"),
]