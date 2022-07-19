from django.contrib import admin
from .models import Post, Group, Comment


class PostAdmin(admin.ModelAdmin):
    class CommentInline(admin.TabularInline):
        model = Comment

    list_display = (
        'pk',
        'text',
        'pub_date',
        'author',
        'group'
    )
    search_fields = ('text',)
    list_filter = ('pub_date',)
    list_editable = ('group',)
    empty_value_display = '-пусто-'

    inlines = [
        CommentInline,
    ]


admin.site.register(Post, PostAdmin)
admin.site.register(Group)
