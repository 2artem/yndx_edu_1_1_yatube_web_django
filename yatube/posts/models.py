from django.db import models
from django.contrib.auth import get_user_model


User = get_user_model()


class Group(models.Model):
    title = models.CharField('Название группы', max_length=200)
    slug = models.SlugField(
        'URL группы',
        max_length=40,
        unique=True
    )
    description = models.TextField('Описание группы')

    def __str__(self):
        return self.title


class Post(models.Model):
    text = models.TextField('Текст поста')
    pub_date = models.DateTimeField('Дата создания поста', auto_now_add=True)
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='posts',
        verbose_name='Автор поста'
    )
    group = models.ForeignKey(
        Group,
        on_delete=models.SET_NULL,
        related_name='posts',
        blank=True,
        null=True,
        verbose_name='Группа к которой принадлежит пост',
    )
    image = models.ImageField(
        'Картинка',
        upload_to='posts/',
        blank=True,
    )

    class Meta:
        ordering = ['-pub_date']
        verbose_name = 'Пост'

    def __str__(self):
        return self.text[:15]


class Comment(models.Model):
    post = models.ForeignKey(
        Post,
        on_delete=models.CASCADE,
        related_name='comments',
        verbose_name='Cсылка на пост',
        blank=False,
        null=False,
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='comments',
        verbose_name='Cсылка на автора комментария',
        blank=False,
        null=False,
    )
    text = models.TextField(
        max_length=20000,
        verbose_name='Tекст комментария',
        blank=False,
        null=False,
    )
    created = models.DateTimeField(
        'Дата публикации комментария',
        auto_now_add=True
    )

    class Meta:
        ordering = ['-created']
        verbose_name = 'Комментарий'

    def __str__(self):
        return 'Комментарий {}: {}'.format(
            self.author,
            self.text[:15]
        )


class Follow(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='follower',
        verbose_name='Подписывающийся пользователь',
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='following',
        verbose_name='Пользователь на которого подписываются',
    )

    class Meta:
        verbose_name = 'Связь автора и подписавшегося'

    def __str__(self):
        return 'Пользователь {} подписан на {}'.format(
            self.user,
            self.author
        )
