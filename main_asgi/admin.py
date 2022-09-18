from django.contrib import admin
from django.core.cache import cache
from django.db import models
from django.core.paginator import Paginator
from .models import PrivateChatRoom, PrivateChatMessage, PublicChatRoom, PublicChatMessage, Notification
# Register your models here.

class NotificationAdmin(admin.ModelAdmin):
    list_filter = []
    list_display = ['target', 'timestamp']
    search_fields = ['target__username',]
    readonly_fields = []

    class Meta:
        model = Notification

admin.site.register(Notification, NotificationAdmin)


class PrivateChatRoomAdmin(admin.ModelAdmin):
	list_display = ['id','user1', 'user2', ]
	search_fields = ['id', 'user1__username', 'user2__username','user1__email', 'user2__email', ]
	readonly_fields = ['id',]

	class Meta:
		model = PrivateChatRoom

admin.site.register(PrivateChatRoom, PrivateChatRoomAdmin)


# Resource: http://masnun.rocks/2017/03/20/django-admin-expensive-count-all-queries/
class CachingPaginator(Paginator):
	def _get_count(self):
		if not hasattr(self, "_count"):
			self._count = None
		if self._count is None:
			try:
				key = "adm:{0}:count".format(hash(self.object_list.query.__str__()))
				self._count = cache.get(key, -1)
				if self._count == -1:
					self._count = super().count
					cache.set(key, self._count, 3600)
			except:
				self._count = len(self.object_list)
			return self._count

	count = property(_get_count)


class PrivateChatMessageAdmin(admin.ModelAdmin):
	list_filter = ['room',  'user', "timestamp"]
	list_display = ['room',  'user', 'content',"timestamp"]
	search_fields = ['user__username','content']
	readonly_fields = ['id', "user", "room", "timestamp"]

	show_full_result_count = False
	paginator = CachingPaginator

	class Meta:
		model = PrivateChatMessage

admin.site.register(PrivateChatMessage, PrivateChatMessageAdmin)


class PublicChatRoomAdmin(admin.ModelAdmin):
    list_display = ['id','title', ]
    search_fields = ['id', 'title', ]
    readonly_fields = ['id',]

    class Meta:
        model = PublicChatRoom

admin.site.register(PublicChatRoom, PublicChatRoomAdmin)

# Resource: http://masnun.rocks/2017/03/20/django-admin-expensive-count-all-queries/
class CachingPaginator(Paginator):
    def _get_count(self):

        if not hasattr(self, "_count"):
            self._count = None

        if self._count is None:
            try:
                key = "adm:{0}:count".format(hash(self.object_list.query.__str__()))
                self._count = cache.get(key, -1)
                if self._count == -1:
                    self._count = super().count
                    cache.set(key, self._count, 3600)

            except:
                self._count = len(self.object_list)
        return self._count

    count = property(_get_count)


class PublicChatMessageAdmin(admin.ModelAdmin):
    list_filter = ['room',  'user', "timestamp"]
    list_display = ['room',  'user', 'content',"timestamp"]
    search_fields = ['room__title', 'user__username','content']
    readonly_fields = ['id', "user", "room", "timestamp"]

    show_full_result_count = False
    paginator = CachingPaginator

    class Meta:
        model = PublicChatMessage

admin.site.register(PublicChatMessage, PublicChatMessageAdmin)