from django.db import models
from django.urls import reverse
from django.contrib.auth.models import User
from django.db.models import Prefetch


class PostQuerySet(models.QuerySet):
    def year(self, year):
        return self.filter(published_at__year=year).order_by("published_at")

    def popular(self):
        return self.annotate(likes_count=models.Count('likes', distinct=True)).order_by('-likes_count')

    def fetch_with_comments_count(self):
        posts = list(self)
        post_ids = [post.id for post in posts]

        # В каналах с несколькими связями кастомный менеджер позволяет избежать большого количества запросов,
        # связанных с объединением с несколькими аннотациями и часто выполняется заметно быстрее.
        comments_count_by_post_id = {
            item['id']: item['comments_count']
            for item in self.model.objects
            .filter(id__in=post_ids)
            .annotate(comments_count=models.Count('comments', distinct=True))
            .values('id', 'comments_count')
        }

        for post in posts:
            post.comments_count = comments_count_by_post_id.get(post.id, 0)
        return posts

    def fetch_with_author_and_tags(self):
        tag_model = self.model._meta.get_field('tags').remote_field.model
        tags_with_posts_count = tag_model.objects.with_posts_count()
        return self.select_related('author').prefetch_related(
            Prefetch('tags', queryset=tags_with_posts_count)
        )


class TagQuerySet(models.QuerySet):
    def with_posts_count(self):
        return self.annotate(posts_count=models.Count('posts'))

    def popular(self):
        return self.with_posts_count().order_by('-posts_count')


class Post(models.Model):
    title = models.CharField('Заголовок', max_length=200)
    text = models.TextField('Текст')
    slug = models.SlugField('Название в виде url', max_length=200)
    image = models.ImageField('Картинка')
    published_at = models.DateTimeField("Дата и время публикации")
    objects = PostQuerySet.as_manager()

    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name='Автор',
        limit_choices_to={'is_staff': True})
    likes = models.ManyToManyField(
        User,
        related_name='liked_posts',
        verbose_name='Кто лайкнул',
        blank=True)
    tags = models.ManyToManyField(
        'Tag',
        related_name='posts',
        verbose_name='Теги')

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse('post_detail', args={'slug': self.slug})

    class Meta:
        ordering = ['-published_at']
        verbose_name = 'пост'
        verbose_name_plural = 'посты'


class Tag(models.Model):
    title = models.CharField('Тег', max_length=20, unique=True)
    objects = TagQuerySet.as_manager()

    def __str__(self):
        return self.title

    def clean(self):
        self.title = self.title.lower()

    def get_absolute_url(self):
        return reverse('tag_filter', args={'tag_title': self.slug})

    class Meta:
        ordering = ['title']
        verbose_name = 'тег'
        verbose_name_plural = 'теги'


class Comment(models.Model):
    post = models.ForeignKey(
        'Post',
        related_name='comments',
        on_delete=models.CASCADE,
        verbose_name='Пост, к которому написан')
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name='Автор')

    text = models.TextField('Текст комментария')
    published_at = models.DateTimeField('Дата и время публикации')

    def __str__(self):
        return f'{self.author.username} under {self.post.title}'

    class Meta:
        ordering = ['published_at']
        verbose_name = 'комментарий'
        verbose_name_plural = 'комментарии'
