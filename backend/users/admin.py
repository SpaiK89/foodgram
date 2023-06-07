from django.contrib import admin
from foodgram.settings import VALUE_DISPLAY
from .models import Follow, User


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    """Отображает пользователей в панели администратора."""
    list_display = ('username', 'first_name', 'last_name', 'email')
    list_filter = ('email', 'username', )
    empty_value_display = VALUE_DISPLAY


@admin.register(Follow)
class FollowAdmin(admin.ModelAdmin):
    """Отображает подписки на авторов в панели администратора."""
    list_display = ('user', 'author')
    search_fields = ('user',)
    list_filter = ('user', )
    empty_value_display = VALUE_DISPLAY
