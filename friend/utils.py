from friend.models import FriendRequest, FriendList

def get_friend_request_or_false(sender, receiver):
	try:
		friend_requests = FriendRequest.objects.filter(sender=sender, receiver=receiver)
		if len(friend_requests) == 1:
			return friend_requests[0]

		elif len(friend_requests) > 1:
			friend_request = list(friend_requests).pop()
			for fr in friend_requests:
				fr.delete()
			return friend_request

		else:
			return False
			

	except:
		return False 

def get_mutual_friends(user1, user2):
	mutual_friends = []
	for friend in user1.friends.all():
		if friend in user2.friends.all():
			mutual_friends.append(friend)

	if len(mutual_friends) > 0:
		return mutual_friends
	return None
