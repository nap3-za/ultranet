from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from account.models import Account, AccountSettings

class AccountAdmin(UserAdmin):
	list_display = ('username',)
	search_fields = ('email','username', 'name', 'surname')
	readonly_fields=('id', 'date_joined', 'last_login')
	filter_horizontal = ()
	list_filter = ()
	fieldsets = ()

admin.site.register(Account, AccountAdmin)

class AccountSettingsAdmin(admin.ModelAdmin):
	list_display = ('account',)
	search_fields = ('account',)
	readonly_fields=('id',)
	filter_horizontal = ()
	list_filter = ()
	fieldsets = ()

admin.site.register(AccountSettings, AccountSettingsAdmin)
