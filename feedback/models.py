from django.db import models
from django.conf import settings
from django.contrib.postgres.fields import ArrayField
# Create your models here.

class Feedback(models.Model):

    author              = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    content             = models.TextField(blank=True, null=True)
    timestamp           = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.content[:20]

class Question(models.Model):
    author              = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    question            = models.TextField()
    answer              = models.TextField()
    is_answered         = models.BooleanField(default=False)
    timestamp           = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.question[:20]



# Create your models here.
# Create your models here.
report_types = [
	('Account', 'Account'),
	('Content', 'Content'),
	('Comment', 'Comment'),
]
report_reasons = [
	('Contains sensetive/inappropriate content', 'Contains sensetive/inappropriate content'),
	('Racist', 'Racist'),
	('False facts', 'False facts'),
	('default', 'default')
	# ...
]

class Report(models.Model):

	# Obj refers to the model class being reported , account/content/resource etc.
	repotee 			= models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, null=True, blank=False)
	obj 				= models.CharField(verbose_name="obj", max_length=500, choices=report_types, default="default")
	obj_id 				= models.IntegerField(verbose_name="obj_id", default=0, null=False, blank=False)
	reason 				= models.CharField(verbose_name="reason", max_length=1000, choices=report_reasons, blank=False, null=False, default="default")
	timestamp 			= models.DateTimeField(auto_now_add=True)

	def __str__(self):
		return self.subject