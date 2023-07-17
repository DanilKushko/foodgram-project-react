from django.contrib import admin
from django.conf import settings
from recipes.models import Follow, User


class UserAdmin(admin.ModelAdmin):
    list_display = (
        'username', 'first_name', 'last_name', 'email',
    )
    search_fields = ('username',)
    list_filter = ('username', 'email')
    empty_value_display = settings.EMPTY_VALUE

    class Meta:
        model = User
        ordering = ('username',)


class FollowAdmin(admin.ModelAdmin):
    list_display = (
        'user', 'author'
    )
    search_fields = ('user',)
    list_filter = ('user', 'author')
    empty_value_display = settings.EMPTY_VALUE

    class Meta:
        model = Follow
        ordering = ('user',)


admin.site.register(User, UserAdmin)
admin.site.register(Follow, FollowAdmin)