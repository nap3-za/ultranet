from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import authenticate
from django.utils import timezone 

import datetime
from .models import Account, AccountSettings, visibility_options_primary, visibility_options_secondary


class RegistrationForm(UserCreationForm):

	email = forms.EmailField(max_length=254, help_text='Add a valid email address.')

	class Meta:
		model = Account
		fields = (
			'accept',
			'email',
			'username',
			'name',
			'dob',
			'gender',
			'surname',
			'password1',
			'password2',
			)

	def clean_email(self):
		email = self.cleaned_data['email'].lower()
		accounts = Account.objects.filter(email=email)
		if len(accounts) >= 1:
			raise forms.ValidationError(f'Email {email} is already in use.')
		else:
			return email
		
	def clean_username(self):
		username = self.cleaned_data['username']
		accounts = Account.objects.filter(username=username)
		if len(accounts) >= 1:
			raise forms.ValidationError(f'Username {username} is already in use , try another one.')
		else:
			return username


	def clean_accept(self):
		accept = self.cleaned_data['accept']
		if not accept:
			raise forms.ValidationError('You must accept Ultranet\'s privacy policy and terms of use to continue')
		elif accept:
			return accept
	
class AuthenticationForm(forms.ModelForm):

	password = forms.CharField(label='Password', widget=forms.PasswordInput)

	class Meta:
		model = Account
		fields = ('email', 'password')

	def clean(self):
		email = self.cleaned_data['email']
		password = self.cleaned_data['password']
		try:
			account = Account.objects.get(email=email)
			auth_user_account = authenticate(email=email, password=password)
		except:
			raise forms.ValidationError("Invalid login")

class SettingsAccountForm(forms.ModelForm):

	class Meta:
		model = Account
		fields = (
			'email',
			'username',
			'name',
			'surname',
			'gender',
		)

	def clean_email(self):
		email = self.cleaned_data['email'].lower()
		accounts = Account.objects.filter(email=email)
		if len(accounts) > 1:
			return forms.ValidationError(f"Email {email} already in use")
		elif len(accounts) <= 1:
			return email
		else:
			raise forms.ValidationError("Invalid email")

	def clean_username(self):
		username = self.cleaned_data['username']
		accounts = Account.objects.filter(username=username)
		if len(accounts) > 1:
			return forms.ValidationError(f"Username {username} already in use")
		elif len(accounts) <= 1:
			return username
		else:
			raise forms.ValidationError("Invalid username")

	def clean_gender(self):
		gender = self.cleaned_data["gender"]
		if gender != 'Male' and gender != 'Female' and gender != 'Other':
			raise forms.ValidationError("Please select a valid gender")
		else:
			return gender

	def save(self, instance, commit=True):
		account = instance
		username = self.cleaned_data['username']
		email = self.cleaned_data['email']

		if email != account.email and len(Account.objects.filter(email=email))==1:
			raise forms.ValidationError("Email provided is already in use")

		if username != account.username and len(Account.objects.filter(username=username))==1:
			raise forms.ValidationError("Username provided is already in use")
		account.email = email
		account.username = username

		account.name = self.cleaned_data['name']
		account.surname = self.cleaned_data['surname']
		account.gender = self.cleaned_data['gender']
		if commit:
			account.save()
		return account

class SettingsPrivacyForm(forms.ModelForm):

	class Meta:
		model = AccountSettings
		fields = (
		'visibility_email',
		'visibility_personal_info',
		'visibility_bio',
		'visibility_social_links',
		'visibility_timeline',
		'visibility_friend_list',
		'visibility_dob',
		'visibility_gender',
		'friendship',
		'public_chat_perm',
		'private_chat_perm',
		)

	def save(self, instance, commit=True):
		settings = instance
		settings.visibility_email = self.cleaned_data['visibility_email']
		settings.visibility_personal_info = self.cleaned_data['visibility_personal_info']
		settings.visibility_bio = self.cleaned_data['visibility_bio']
		settings.visibility_social_links = self.cleaned_data['visibility_social_links']
		settings.visibility_timeline = self.cleaned_data['visibility_timeline']
		settings.visibility_friend_list = self.cleaned_data['visibility_friend_list']
		settings.visibility_gender = self.cleaned_data['visibility_gender']
		settings.visibility_dob = self.cleaned_data['visibility_dob']
		settings.friendship = self.cleaned_data['friendship']
		settings.private_chat_perm = self.cleaned_data['private_chat_perm']
		settings.public_chat_perm = self.cleaned_data['public_chat_perm']
		if commit:
			settings.save()
		return settings

class SettingsNotificationsForm(forms.ModelForm):

	class Meta:
		
		model = AccountSettings
		fields = (
			'like_notifications',
			'comment_notifications',
			'message_notifications',
			'friend_request_notifications',
			'push_notifications',
			'group_message_notifications',
		)
	
	def save(self, instance, commit=True):
		settings = instance
		settings.like_notifications = self.cleaned_data['like_notifications']
		settings.comment_notifications = self.cleaned_data['comment_notifications']
		settings.message_notifications = self.cleaned_data['message_notifications']
		settings.friend_request_notifications = self.cleaned_data['friend_request_notifications']
		settings.push_notifications = self.cleaned_data['push_notifications']
		settings.group_message_notifications = self.cleaned_data['group_message_notifications']

		if commit:
			settings.save()
		return settings

class UpdateProfileForm(forms.ModelForm):
	pass
	class Meta:
		model = Account
		fields = (
			'bio',
			'github',
			'stack',
			'youtube',
			'insta',
		)


	def save(self, instance, commit=True):
		account = instance
		account.bio = self.cleaned_data['bio']
		account.github = self.cleaned_data["github"]
		account.stack = self.cleaned_data["stack"]
		account.youtube = self.cleaned_data["youtube"]
		account.insta = self.cleaned_data["insta"]
		if commit:
			account.save()
		return account

class DeleteAccountForm(forms.Form):

	email = forms.EmailField()

	def clean_email(self):
		email = self.cleaned_data['email'].lower()
		try:
			account = Account.objects.get(email=email)
			return email
		except:
			raise forms.ValidationError("Invalid email")

	def save(self, instance, commit=True):
		instance.delete()


