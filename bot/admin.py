from django.contrib import admin
from bot.models import User


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ('username', 'created')
    fields = ('username', ('user_text', 'bot_text'), 'created')
    readonly_fields = ('created',)
    search_fields = ('username',)
    list_filter = ('username', 'created')
