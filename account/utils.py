from django.core.serializers.python import Serializer
from .models import AccountSettings
from friend.models import FriendList
from friend.utils import get_friend_request_or_false
from .relation import RelationStatus as relation

class LazyAccountEncoder(Serializer):
    def get_dump_object(self, obj):
        dump_object = {}
        dump_object.update({'id': str(obj.id)})
        dump_object.update({'email': str(obj.email)})
        dump_object.update({'username': str(obj.username)})
        dump_object.update({'profile_image': str(obj.profile_image.url)})
        return dump_object

def get_account_settings(auth_user, other_user, is_friend, is_mutual_friend):
	settings = {
		"personal_info":False,
		"email":False,
		"links":False,
		"friends":False,
		"dob":False,
		"gender":False,
		"chat":False,
		"timeline":False,
		"no_social_links":False,
	}
	if auth_user == other_user:
		settings = {
			"personal_info":True,
			"email":True,
			"social_links":True,
			"bio": True,
			"friendship": False,
			"friends":True,
			"dob":True,
			"gender":True,
			"chat_perm":False,
			"timeline":True,
			"no_social_links":False,
		}	

		if not auth_user.insta and not auth_user.youtube and not auth_user.github and not auth_user.stack and not auth_user.facebook:
			settings["no_social_links"] = True

		return settings

	elif auth_user != other_user:
		if other_user.settings.visibility_personal_info=="Anyone" or (other_user.settings.visibility_personal_info=="Friends" and is_friend):
			settings["personal_info"] = True

		if other_user.settings.visibility_email=="Anyone" or (other_user.settings.visibility_email=="Friends" and is_friend):
			settings["email"] = True

		if (other_user.insta or other_user.youtube or other_user.github or other_user.stack) and ((other_user.settings.visibility_social_links=="Anyone") or (other_user.settings.visibility_social_links=="Friends" and is_friend)):
			settings["social_links"] = True	

		if (other_user.settings.visibility_friend_list=="Anyone" or (other_user.settings.visibility_friend_list=="Friends" and is_friend)):
			settings["friends"] = True
		
		if other_user.settings.visibility_dob=="Anyone" or (other_user.settings.visibility_dob=="Friends" and is_friend):
			settings["dob"] = True	
		
		if other_user.settings.visibility_gender=="Anyone" or (other_user.settings.visibility_gender=="Friends" and is_friend):
			settings["gender"] = True
		

		if other_user.settings.private_chat_perm=="Anyone" or (other_user.settings.private_chat_perm=="Friends" and is_friend):
			settings["chat_perm"] = True

		if other_user.settings.visibility_timeline=="Anyone" or (other_user.settings.visibility_timeline=="Friends" and is_friend):
			settings["timeline"] = True

		if other_user.settings.friendship=="Anyone" or is_mutual_friend:
			settings["friendship"] = True

		if other_user.settings.visibility_bio=="Anyone" or (other_user.settings.visibility_bio=="Friends" and is_friend):
			settings["bio"] = True

	return settings

def get_relation(user1, user2):

	if user1 in user2.friend_list.friends.all():
		return relation.FRIENDS
	elif get_friend_request_or_false(sender=user1, receiver=user2) != False:
		return relation.USER1_TO_USER2
	elif get_friend_request_or_false(sender=user2, receiver=user1) != False:
		return relation.USER2_TO_USER1

	mutual_friends=False
	try:
		for friend in user1.friend_list.friends.all():
			if friend in user2.friend_list.friends.all():
				mutual_friends=True
	except:
		return None
	if mutual_friends:
		return relation.MUTUAL_FRIEND
	else:
		return relation.NOT_FRIENDS

def get_or_create_friend_list(user):
	try:
		return FriendList.objects.get(user=user)
	except:
		friend_list = FriendList.objects.create(user=user)
		friend_list.save()
		return friend_list
