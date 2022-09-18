from django.urls import path

from .chat_views import(
	private_chat_room_view,
	private_chats_view,
	create_or_return_private_chat,
	delete_private_chat_view,

	public_chat_home_view,
    public_chat_create_view,
    public_chat_room_view,
    delete_pub_room_view,
    reset_view,
    public_chat_update_view,
)

app_name = 'chat'

urlpatterns = [
	path('', private_chat_room_view, name='private_room'),
	path('chats/', private_chats_view, name="chats"),
	path('create_or_return_private_chat/', create_or_return_private_chat, name='create-or-return-private-chat'),
	path('delete_prv/<int:room_id>/', delete_private_chat_view, name="private_delete"),
    path('create/', public_chat_create_view, name="public_create"),
    path('home/', public_chat_home_view, name="public_home"),
    path('room/<str:room_name>/', public_chat_room_view, name="public_room"),
    path('delete_pub/<int:room_id>/', delete_pub_room_view, name="public_delete"),
    path('reset/<str:room_name>/', reset_view, name="public_reset"),
    path('update/<str:room_name>/', public_chat_update_view, name="public_update"),

]
