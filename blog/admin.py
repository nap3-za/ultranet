from django.contrib import admin

# Register your models here.
from .models import Comment, Choice, Content



class ContentAdmin(admin.ModelAdmin):
    list_filter = []
    list_display = ['content_type', 'id']
    search_fields = ['author', 'timestamp', 'content_type']
    readonly_fields = ['timestamp']

    class Meta:
        model = Content
admin.site.register(Content, ContentAdmin)

class CommentAdmin(admin.ModelAdmin):
    list_filter = []
    list_display = ['author', 'content']
    search_fields = ['author', 'content']
    readonly_fields = ['timestamp']

    ordering = ['-timestamp']

    class Meta:
        model = Comment
admin.site.register(Comment, CommentAdmin)


class ChoiceAdmin(admin.ModelAdmin):
    list_filter = []
    list_display = ['content', 'value', 'id']
    search_fields = ['content', 'value']
    readonly_fields = []

    class Meta:
        model = Choice

admin.site.register(Choice, ChoiceAdmin)


