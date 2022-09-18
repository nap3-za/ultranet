from django.db import models
from django.conf import settings

# Create your models here.

class Search(models.Model):

	user 				= models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
	search_query 		= models.CharField(verbose_name="search_query", max_length=255, null=False, blank=False, default="default")
	timestamp 			= models.DateTimeField(verbose_name="timestamp", auto_now_add=True)

	def __str__(self):
		return self.search_query