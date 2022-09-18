from django import forms
from .models import PublicChatRoom
from friend.models import FriendList 
from account.models import Account as BaseAccount


options = [
('All Friends', 'All Friends'),
('Selected Friends', 'Selected Friends'),
('Everyone', 'Everyone')
]

users = []
# for user in BaseAccount.objects.all():
# 	users.append((user.username, user.username))



class PubChatCreationForm(forms.Form):
	title  				= forms.CharField(max_length=255, required=True, label="Room Title")
	room_name			= forms.CharField(max_length=255, required=True, label="Room name")
	accessibility 		= forms.ChoiceField(choices=options, label="Accessibility")
	allowed_friends		= forms.MultipleChoiceField(choices=users, required=False, label="Allowed Friends")

	def clean(self):
		accessibility = self.cleaned_data["accessibility"]
		if accessibility == "All Friends":
			pass
		elif accessibility == "Selected Friends":
			allowed_friends = self.cleaned_data['allowed_friends']
			if accessibility == "Selected Friends" and len(allowed_friends) <= 0:
				raise forms.ValidationError("Please check the Select friends checkox and select friends")



class PubChatUpdateForm(forms.Form):
	
	title  				= forms.CharField(max_length=255, required=True, label="Room Title")
	room_name			= forms.CharField(max_length=255, required=True, label="Room name")
	accessibility 		= forms.ChoiceField(choices=options, label="Accessibility")
	allowed_friends		= forms.MultipleChoiceField(choices=users, required=False, label="Allowed Friends")


	def clean(self):
		print(self.cleaned_data)
		allowed_friends = self.cleaned_data["allowed_friends"]
		accessibility = self.cleaned_data["accessibility"]
		if accessibility == "Selected Friends" and len(allowed_friends) <= 0:
			raise forms.ValidationError("Please check the Select friends checkox and select friends")

