import datetime

from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager
from django.conf import settings
from django.db.models.signals import post_save,pre_save
from django.db.models import Q
from django.utils import timezone

from blog.models import Content
from .field_choices import visibility_options_primary, visibility_options_secondary, genders

# Create your models here.

class AccountManager(BaseUserManager):
	
	def create_user(self, email, username, name, surname, dob, gender, accept, password=None):
		if not email:
			raise ValueError('Please enter a valid email address')
		if not username:
			raise ValueError('Please enter a unique username')
		if not accept:
			raise ValueError('You cannot continue without accepting our privacy policy and terms of use')
		if dob>timezone.now().date()-datetime.timedelta(days=6570):
			raise ValueError('You must be 18 years or older to register to Ultranet')

		user = self.model(
			email=self.normalize_email(email),
			username=username,
			name=name,
			surname=surname,
			dob=dob,
			gender=gender,
			accept=accept,
		)
		user.set_password(password)
		user.save(using=self._db)
		return user

	def create_superuser(self, email, username, password, name, surname, dob, gender, accept):
		user = self.create_user(
			email=self.normalize_email(email),
			password=password,
			username=username,
			name=name,
			surname=surname,
			dob=dob,
			gender=gender,
			accept=accept,
		)
		user.is_admin = True
		user.is_staff = True
		user.is_superuser = True
		user.save(using=self._db)
		return user

def get_profile_image_filepath(self, filename):
	return 'account/profile_images/' + str(self.pk) +  '/profile_image.png'

class Account(AbstractBaseUser):
	email 					= models.EmailField(verbose_name="email", max_length=60, unique=True, null=False, blank=False)
	username 				= models.CharField(verbose_name="username", max_length=30, unique=True, null=False, blank=False)
	
	name 					= models.CharField(verbose_name="name", max_length=30, unique=False, null=True, blank=True)
	surname 				= models.CharField(verbose_name="surname", max_length=30, unique=False, null=True, blank=True)
	dob						= models.DateField(blank=False)
	gender 					= models.CharField(verbose_name="gender",choices=genders, max_length=25, default="Female")

	profile_image 			= models.ImageField(max_length=255, upload_to=get_profile_image_filepath, null=True, blank=True, default="account/profile_images/default.jpg")
	bio 					= models.TextField(blank=True, null=True, default="""</>""")

	github  				= models.CharField(verbose_name="github", max_length=80, null=True, blank=True)
	stack  					= models.CharField(verbose_name="stack", max_length=80, null=True, blank=True)
	youtube					= models.CharField(verbose_name="youtube", max_length=80, null=True, blank=True)
	insta	  				= models.CharField(verbose_name="insta", max_length=80, null=True, blank=True)
	facebook  				= models.CharField(verbose_name="facebook", max_length=80, null=True, blank=True)

	is_online			 	= models.BooleanField(verbose_name="is_online", default=False)
	is_active 				= models.BooleanField(default=True)
	date_joined				= models.DateTimeField(verbose_name='date joined', auto_now_add=True)
	last_login				= models.DateTimeField(verbose_name='last login', auto_now=True)	
	is_admin				= models.BooleanField(verbose_name="is_admin", default=False)
	is_staff				= models.BooleanField(verbose_name="is_staff", default=False)
	is_superuser			= models.BooleanField(verbose_name="is_superuser", default=False)
	
	# Accepts the Ts&Cs of Ultranet
	accept 					= models.BooleanField(verbose_name="accept", default=False)

	USERNAME_FIELD = 'email'
	REQUIRED_FIELDS = ['username', 'name', 'surname', 'dob', 'gender', 'accept']

	objects = AccountManager()

	def __str__(self):
		return self.username


	def connect(self):
		self.is_online = True 
		self.save()

	def disconnect(self):
		self.is_online = False
		self.save()

	def get_profile_image_filename(self):
		return str(self.profile_image)[str(self.profile_image).index('account/profile_images/' + str(self.pk) + "/"):]

	@property
	def channel_name(self):
		"""
		Returns the Channels Group name that sockets should subscribe to to get sent
		messages as they are generated.
		"""
		return f"UC-{self.id}-UC"

	# For checking permissions. to keep it simple all admin have ALL permissons
	def has_perm(self, perm, obj=None):
		return self.is_admin

	# Does this user have permission to view this app? (ALWAYS YES FOR SIMPLICITY)
	def has_module_perms(self, app_label):
		return True


class AccountSettings(models.Model):

	account 					= models.OneToOneField('Account', on_delete=models.CASCADE, related_name="settings", null=False)
	
	visibility_email			= models.CharField(verbose_name="visibility_email", choices=visibility_options_primary, max_length=15, default="No One")
	visibility_timeline			= models.CharField(verbose_name="visibility_timeline",choices=visibility_options_secondary, max_length=15, default="Friends")
	visibility_personal_info	= models.CharField(verbose_name="visibility_personal_info",choices=visibility_options_secondary, max_length=15, default="Friends")
	visibility_friend_list		= models.CharField(verbose_name="visibility_friend_list", choices=visibility_options_primary, max_length=15, default="Friends")
	visibility_social_links		= models.CharField(verbose_name="visibility_social_links", choices=(('Anyone', 'Anyone'), ('Friends of friends', 'Friends of Friends'), ('Friends', 'Friends'), ('No One', 'No One')), max_length=20, default="Friends")
	visibility_dob				= models.CharField(verbose_name="visibility_dob", choices=visibility_options_primary, max_length=20, default="No One")
	visibility_gender			= models.CharField(verbose_name="visibility_gender", choices=visibility_options_primary, max_length=15, default="No One")
	visibility_bio				= models.CharField(verbose_name="visibility_bio", choices=visibility_options_secondary, max_length=15, default="Friends")
	friendship 					= models.CharField(verbose_name="friendship", choices=(('Anyone', 'Anyone'), ('Mutual Friends', 'Mutual Friends'), ('Friends', 'Friends')), max_length=20, default="Friends")
	private_chat_perm 			= models.CharField(verbose_name="private_chat_perm", choices=(('Anyone', 'Anyone'), ('Mutual Friends', 'Mutual Friends'), ('Friends', 'Friends')), max_length=20, default="Friends")
	public_chat_perm 			= models.CharField(verbose_name="public_chat_perm", choices=visibility_options_primary, max_length=10, default="Friends")

	like_notifications			= models.BooleanField(default=True)
	comment_notifications		= models.BooleanField(default=True)
	message_notifications		= models.BooleanField(default=True)
	group_message_notifications	= models.BooleanField(default=True)
	friend_request_notifications= models.BooleanField(default=True)
	push_notifications			= models.BooleanField(default=True)

	def __str__(self):
		return self.account.username

def account_post_save(sender, instance, created, *args, **kwargs):
	if created:
		try:
			user_settings = instance.settings
		except:
			instance.settings = AccountSettings(account=instance)
			instance.settings.save()

post_save.connect(account_post_save, sender=Account)



