from django.contrib import admin

from .models import Post
from .models import Group
from .models import Follow


class PostAdmin(admin.ModelAdmin):
    # Перечисляем поля, которые должны отображаться в админке
    list_display = ('pk', 'text', 'pub_date', 'author', 'group')
    list_editable = ('group',)
    # Добавляем интерфейс для поиска по тексту постов
    search_fields = ('text',)
    # Добавляем возможность фильтрации по дате
    list_filter = ('pub_date',)
    empty_value_display = '-пусто-'


class Group_app(admin.ModelAdmin):
    list_display = ('title', 'slug', 'description')
    empty_value_display = '-пусто-'


class Follow_app(admin.ModelAdmin):
    list_display = ('user', 'author')


admin.site.register(Post, PostAdmin)
admin.site.register(Group, Group_app)
admin.site.register(Follow, Follow_app)
