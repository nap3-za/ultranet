"""Itranet URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/3.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.conf.urls.static import static
from django.conf import settings
from django.contrib.auth import views as auth_views


from account import views as account_views
from nomad import views as nomad_views
from blog.views import feed_view
from feedback import views as feedback_views

urlpatterns = [
    path('admin/', admin.site.urls),

    path('', nomad_views.HomeView.as_view(), name="home"),
    path('about/', nomad_views.AboutView.as_view(), name="about_page"),
    path('get_in_touch/', nomad_views.ContactView.as_view(), name="contact_page"),
    path('legal-docs/', nomad_views.LegalDocsView.as_view(), name="legal_docs_page"),

    path('register/', account_views.register_view, name="register"),
    path('login/', account_views.login_view, name="login"),
    path('logout/', account_views.logout_view, name="logout"),
    path('account/', include('account.urls', namespace="account")),
    path('friend/', include('friend.urls', namespace="friend")),
    path('', include('main_asgi.urls', namespace="main_asgi")),
    path('feedback/', include('feedback.urls', namespace="feedback")),
    path('notifications/', include('main_asgi.chat_urls', namespace="notifications")),
    path('blog/', include('blog.urls', namespace="blog")),
    path('', include('nomad.urls', namespace="nomad")),
    
    path('report/', feedback_views.create_report_view, name="report"),
    path('lobby/', feed_view, name="feed"),
    
    path('chat/', include('main_asgi.chat_urls', namespace="chat")),
    path('notifications/', include('main_asgi.notifications_urls', namespace="notification")),

    path('password-reset/', auth_views.PasswordResetView.as_view(template_name="account/password-reset/reset.html"), name="password_reset"),
    path('password-reset/done/', auth_views.PasswordResetDoneView.as_view(template_name='account/password-reset/reset_done.html'), name="password_reset_done"),
    path('password-reset/complete/', auth_views.PasswordResetCompleteView.as_view(template_name='account/password-reset/reset_complete.html'), name="password_reset_complete"),    
    path('password-reset/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(template_name="account/password-reset/reset_confirm.html"), name='password_reset_confirm'),

    path('password_change/done/', auth_views.PasswordChangeDoneView.as_view(template_name='account/password-reset/change_done.html'),name='password_change_done'),
    path('password_change/', auth_views.PasswordChangeView.as_view(template_name='account/password-reset/change.html'),name='password_change'),

    path('server_error/', nomad_views.server_error_view, name="500"),
    path('page_not_found/', nomad_views.page_not_found_view, name="404"),
    path('bad_request', nomad_views.bad_request_view, name="400"),
    path('permision_denied/', nomad_views.perm_denied_view, name="403"),
]

if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

handler404 = nomad_views.page_not_found_view
handler500 = nomad_views.server_error_view
handler403 = nomad_views.perm_denied_view
handler400 = nomad_views.bad_request_view
