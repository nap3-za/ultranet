from django.urls import path
from .views import (
    friend_requests_view,
    send_friend_request_view,
    accept_friend_request_view,
    decline_friend_request_view,
    unfriend_view,
    cancel_friend_request_view,
    friend_list_view,
    accounts_view,
)

app_name = "friend"

urlpatterns = [
    path('friend_request/', send_friend_request_view, name="send"),
    path('friend_requests/<user_id>/', friend_requests_view, name="friend_requests"),
    path('accept_friend_request/<friend_request_id>/', accept_friend_request_view, name="accept"),
    path('remove/', unfriend_view, name="unfriend"),
    path('decline_friend_request/<friend_request_id>/', decline_friend_request_view, name="decline"),
    path('cancel_friend_request/', cancel_friend_request_view, name='cancel'),
    path('friend_list_view/<user_id>/', friend_list_view, name="friend_list"),
    path('mingle/<int:user_id>/', accounts_view, name="accounts"),
]
