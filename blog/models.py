from django.db import models
from django.contrib.postgres.fields import ArrayField
from django.conf import settings
from django.utils import timezone
from django.db.models.signals import pre_save, post_save

import datetime

# Create your models here.

visibility_options = [
	('Anyone', 'Anyone'),
	('Friends', 'Friends'),
]

content_types = [
	('Post', 'Post'),
	('Poll', 'Poll'),
]


class Choice(models.Model):

	content		= models.ForeignKey('Content', on_delete=models.CASCADE, null=True)
	value 		= models.CharField(verbose_name="value", max_length=100, unique=False)
	votes  		= models.ManyToManyField(settings.AUTH_USER_MODEL, blank=True, related_name="votes")
	timestamp 	= models.DateTimeField(verbose_name="timestamp", auto_now_add=True)
	
	
	def __str__(self):
		return self.value

	def add_vote(self, user):
		if not user in self.votes.all():
			self.votes.add(user)
			self.save()
		else:
			return False

	def remove_vote(self, user):
		if user in self.votes.all():
			self.votes.remove(user)
			self.save()
			return True
		else:
			return False

	def change_vote(self, user, value):

		if user in self.votes() and not user in value.votes():
			self.votes.remove_vote(user)
			value.add_vote(user)
			value.save()
			return True
		else:
			return False

	def clean_values(self, user):
		choices = self.content.choice_set.all()
		for choice in choices:
			if user in choice.votes.all():
				choice.remove_vote(user=user)

	@property
	def total_votes(self):
		vote_count=0
		for choice in self.content.choice_set.all():
			vote_count+=len(choice.votes.all())
		return vote_count
	


class ContentQuerySet(models.QuerySet):
    def search(self, query=None):
        if query is None or query == "":
            return self.none()
        lookups = Q(username__icontains=query)
        return self.filter(lookups) 

tag_choices = [
	"Operating Systems",
	"Competetive Programming",
	"Software",
	"Programming Languages",
	"Hardware",
]

class ContentManager(models.Manager):

	def create_content(self, author, text, content_type, draft, visibility, title, tags):
		if author==None:
			raise ValueError("Invalid author")
		if content_type!="Post" and content_type!="Poll":
			raise ValueError("Invalid content type")
		if len(tags)>=1:
			for tag in tags:
				if not tag in tag_choices:
					raise ValueError("Invalid tag")
				

		content = self.model(
				author=author,
				content_type=content_type,
				title=title,
				tags=tags,
				visibility=visibility,
				draft=draft,
		)
		if content_type=="Post" and len(text)>=3:
			content.text=text
			content.save(using=self._db)
			return content 
		elif content_type=="Poll":
			content.save(using=self._db)
			choices = text.replace('\r','').split('\n')
			if len(choices)<=1:
				raise ValueError("A poll must have 2 or more choices")
			content_text=""
			for choice in set(choices):
				poll_choice = Choice.objects.create(content=content, value=choice.lower().replace(' ','').replace('\r',''))
				poll_choice.save()
				content_text+='\n'+choice.lower()

			content.text=content_text[1:]
			content.save(using=self._db)
			return content

	def get_queryset(self):
		return ContentQuerySet(self.model, using=self._db)

	def search(self, query=None):
		return self.get_queryset().search(query=query)
		


class Content(models.Model):

	author 		= models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
	title 		= models.CharField(verbose_name="title", max_length=70, null=True, blank=True, unique=False)
	content_type= models.CharField(choices=content_types, verbose_name="content_type", max_length=50, default="default")
	tags	 	= ArrayField(models.CharField(max_length=30, blank=True), size=5, blank=True)

	text  		= models.TextField(blank=True, null=True)

	comments 	= models.ManyToManyField('Comment', related_name="comments", blank=True)
	views 		= models.ManyToManyField(settings.AUTH_USER_MODEL, blank=True, related_name="views")
	likes 		= models.ManyToManyField(settings.AUTH_USER_MODEL, blank=True, related_name="likes")
	dislikes 	= models.ManyToManyField(settings.AUTH_USER_MODEL, blank=True, related_name="dislikes")

	draft 		= models.BooleanField(verbose_name="draft", default=True)
	visibility 	= models.CharField(verbose_name="visibility", choices=visibility_options, default="Friends", max_length=100)

	timestamp 	= models.DateTimeField(verbose_name="timestamp", auto_now_add=True)	

	objects=ContentManager()

	def __str__(self):
		return self.content_type + ' | '

	def add_like(self, user):
		if user in self.dislikes.all():
			self.dislikes.remove(user)
			self.save()
			return True 
		else:
			if user in self.likes.all():
				return True
			self.likes.add(user)
			self.save()
			return True 
	
	def add_dislike(self, user):
		if user in self.likes.all():
			self.likes.remove(user)
			self.save()
			return True
		else:
			if user in self.dislikes.all():
				return True 
			self.dislikes.add(user)
			self.save()
			return True 

	def unlike(self, user):
		if user in self.likes.all(): 
			self.likes.remove(user)
			self.save()
			return True

	def undislike(self, user):
		if user in self.dislikes.all():
			self.dislikes.remove(user)
			self.save()
			return True

	@property
	def recent(self):
		now = timezone.now()
		return now - datetime.timedelta(days=14) <= self.pub_date <= now


class Comment(models.Model):

	author  		= models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
	text 	 		= models.CharField(verbose_name="text", max_length=750, null=False, blank=True)
	content			= models.ForeignKey('Content', verbose_name="content", on_delete=models.CASCADE, blank=False, null=True)

	reply 			= models.ForeignKey('Comment', related_name="reply_obj", null=True, blank=True, on_delete=models.CASCADE)
	timestamp 		= models.DateTimeField(verbose_name="timestamp", auto_now_add=True)

	def __str__(self):
		return self.author.username

	def add_reply(self, comment):
		if not comment in self.replies.all():
			self.replies.add(comment)
			self.save()
			return True
		else:
			return False
