from django.test import TestCase, Client
from django.utils import timezone

# Create your tests here.
import datetime
import random

from .models import Account, AccountSettings

class AccountModelTestCase(TestCase):
	
	def test_account_registration(self):
		gender = random.choice(['Male', 'Female', 'Other'])
		dob = timezone.now().date() - datetime.timedelta(days=7110)

		client_one = Client(follow=False)
		client_two = Client(follow=False)
		client_three = Client(follow=False)

		client_one.post("/register/", {
			"username": "user1",
			"email": "user1@email.com",
			"name":"user",
			"surname": "user",
			"password1": "root.1352",
			"password2": "root.1352",
			"dob": dob,
			"gender": gender,
			"accept": True,
		})
		client_two.post("/register/", {
			"username": "user2",
			"email": "user2@email.com",
			"name":"user",
			"surname": "user",
			"password1": "root.1352",
			"password2": "root.1352",
			"dob": dob,
			"gender": gender,
			"accept": True,
		})
		client_three.post("/register/", {
			"username": "user3",
			"email": "user3@email.com",
			"name":"user",
			"surname": "user",
			"password1": "root.1352",
			"password2": "root.1352",
			"dob": dob,
			"gender": gender,
			"accept": True,
		})


		accounts = Account.objects.all()
		user1 = accounts[0]
		user2 = accounts[1]
		user3 = accounts[2]

		for acc in accounts:
			print(f"Username:{acc.username}\nFriendList:{hasattr(acc,'friend_list')}\nAccountSettings:{hasattr(acc,'settings')}")

		client_one.post("/account/setup_profile/", {
			"bio": "The quick brown fox jumped over the lazy dog",	
			"stack": "user",
			"youtube": "user",
			"github": "user",
			"stack": "user",
			"insta": "user",
			"facebook":"user",	
		})
		client_two.post("/account/setup_profile/", {
			"bio": "The quick brown fox jumped over the lazy dog",	
			"stack": "user",
			"youtube": "user",
			"github": "user",
			"stack": "user",
			"insta": "user",
			"facebook":"user",	
		})
		client_three.post("/account/setup_profile/", {
			"bio": "The quick brown fox jumped over the lazy dog",	
			"stack": "user",
			"youtube": "user",
			"github": "user",
			"stack": "user",
			"insta": "user",
			"facebook":"user",	
		})


		# client.post('/account/update_settings/', {
		# 	"email_visi": "Friends",
		# 	"personal_info_visi": "Friends",
		# 	"chat_perm": "Friends",
		# 	"nationality_visi": "Friends",
		# 	"friend_list_visi": "Friends",
		# 	"timeline_visi": "Friends",
		# 	"social_links_visi": "Friends",
		# 	"passphrase": "Friends",
		# })

		# client.post("/register/", {
		# 	"username": "user1Updated",
		# 	"email": "userUpdated@email.com",
		# 	"name":"user1Updated",
		# 	"surname": "user1Updated",
		# 	"nationality": nationality,
		# 	"accept": True,
		# 	"bio": "Updated fox jump baby",
		# })

		# print(f"[+] Updated user : | {account.username} | {account.email_visi} | {account.bio}")
