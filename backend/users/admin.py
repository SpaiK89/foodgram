import os

from django.contrib import admin

from dotenv import load_dotenv

from .models import Follow, User

load_dotenv()


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    """Отображает пользователей в панели администратора."""
    list_display = ('username', 'first_name', 'last_name', 'email',
                    'role')
    list_filter = ('email', 'username', )
    empty_value_display = os.getenv('VALUE_DISPLAY', '---')


@admin.register(Follow)
class FollowAdmin(admin.ModelAdmin):
    """Отображает подписки на авторов в панели администратора."""
    list_display = ('id', 'user', 'author')
    list_editable = ('user', 'author')
    empty_value_display = os.getenv('VALUE_DISPLAY', '---')
