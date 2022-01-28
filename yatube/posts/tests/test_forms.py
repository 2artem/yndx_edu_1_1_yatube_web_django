import shutil
import tempfile

from django.contrib.auth import get_user_model
from django.urls import reverse
from django.test import Client
from django.test import TestCase
from django.test import override_settings
from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile

from posts.forms import PostForm
from posts.models import Post
from posts.models import Group

User = get_user_model()

# Создаем временную папку для медиа-файлов;
# на момент теста медиа папка будет переопределена
TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


# Для сохранения media-файлов в тестах будет использоваться
# временная папка TEMP_MEDIA_ROOT, а потом мы ее удалим
@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostFormTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # Создаем пользователя
        cls.user = User.objects.create_user(username='userok')
        # Создаем клиент
        cls.authorized_client = Client()
        # Авторизуем пользователя
        cls.authorized_client.force_login(cls.user)
        # Создадим записи в БД
        cls.group = Group.objects.create(
            slug='test-slug-cats',
            title='Котики',
            description='Группа про котов',
        )
        # group_2 - создается для проверки изменения поста
        cls.group_2 = Group.objects.create(
            slug='test2',
            title='Группа 2',
            description='Группа 2 - описание',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Текст поста для теста про котов',
            group=cls.group,
        )
        cls.form = PostForm()

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        # Модуль shutil - библиотека Python с удобными инструментами
        # для управления файлами и директориями:создание,
        # удаление, копирование, перемещение, изменение папок и файлов
        # Метод shutil.rmtree удаляет директорию и всё её содержимое
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def test_create_post(self):
        """Валидная форма создает запись в Post."""
        # Подсчитаем количество записей в Post
        posts_count = Post.objects.count()
        # Для тестирования загрузки изображений
        # берём байт-последовательность картинки,
        # состоящей из двух пикселей: белого и чёрного
        small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        uploaded = SimpleUploadedFile(
            name='small.gif',
            content=small_gif,
            content_type='image/gif'
        )
        form_data = {
            'text': 'Текст поста 2 для теста',
            'group': PostFormTests.group.pk,
            'image': uploaded,
        }
        # Отправляем POST-запрос
        response = self.authorized_client.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True,
        )
        # Проверяем, сработал ли редирект
        self.assertRedirects(response, reverse(
            'posts:profile', kwargs={'username': 'userok'})
        )
        # Проверяем, увеличилось ли число постов
        self.assertEqual(Post.objects.count(), posts_count + 1)
        # Проверяем, что пост сохранился в бд (включая изображение)
        self.assertTrue(
            Post.objects.filter(
                text='Текст поста 2 для теста',
                group=PostFormTests.group,
                image='posts/small.gif',
            ).exists()
        )
        # Проверяем, что при выводе поста с картинкой
        # изображение передаётся в словаре context
        # на страницу: главную, профайла, группы, поста
        packages = [
            ('posts:index', []),
            ('posts:profile', ['username', 'userok']),
            ('posts:group_list', ['slug', 'test-slug-cats']),
            ('posts:post_detail', ['post_id', '2']),
        ]
        for page, param in packages:
            if page == 'posts:index':
                kwargs = {}
            else:
                kwargs = {param[0]: param[1]}
            response = self.authorized_client.get(
                reverse(page, kwargs=kwargs)
            )
            if page == 'posts:post_detail':
                self.assertEqual(
                    response.context['post'].image, 'posts/small.gif'
                )
            else:
                self.assertEqual(
                    response.context['page_obj'][0].image, 'posts/small.gif'
                )

    def test_post_edit(self):
        """Валидная форма редактирует запись в Post."""
        form_data = {
            'text': 'Текст поста для теста при изменении',
            'group': PostFormTests.group_2.pk,
        }
        # Отправили POST-запрос
        response = self.authorized_client.post(
            reverse('posts:post_edit', kwargs={'post_id': '1'}),
            data=form_data,
            follow=True,
            is_edit=True,
        )
        # Проверили редирект
        self.assertRedirects(response, reverse(
            'posts:post_detail', kwargs={'post_id': '1'})
        )
        # Проверили, что пост обновлен
        self.assertTrue(
            Post.objects.filter(
                text='Текст поста для теста при изменении',
                group=PostFormTests.group_2
            ).exists()
        )
