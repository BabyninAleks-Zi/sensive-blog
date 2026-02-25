from django.contrib import admin
from blog.models import Post, Tag, Comment


@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    raw_id_fields = ('author', 'likes', 'tags')


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    raw_id_fields = ('author', 'post')
    list_display = ('id', 'author', 'post', 'published_at')
    list_select_related = ('author', 'post')


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    pass
