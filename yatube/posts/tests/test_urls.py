from django.contrib.auth import get_user_model
from django.test import TestCase
from django.test import Client
from django.urls import reverse

from posts.models import Group
from posts.models import Post

User = get_user_model()


class PostURLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # Создаем неавторизованный клиент
        cls.guest_client = Client()
        # Создаем пользователя
        cls.user = User.objects.create_user(username='userok')
        # Создаем второй клиент
        cls.authorized_client = Client()
        # Авторизуем пользователя
        cls.authorized_client.force_login(cls.user)
        # Создадим запись в БД для проверки доступности адреса group/test-slug/
        cls.group = Group.objects.create(
            slug='test-slug'
        )
        # Создадим запись в БД для проверки доступности адреса post/post_id/
        cls.post = Post.objects.create(
            author=cls.user,
            pk='100',
        )

    # Проверяем доступность адресов (status_code)
    #
    # Неавторизованный пользователь - Страница видна Всем
    def test_url_exists_at_desired_location(self):
        """Список страниц доступен любому пользователю."""
        response_list = {
            reverse('posts:index'): 200,
            reverse('posts:group_list', kwargs={'slug': 'test-slug'}): 200,
            reverse('posts:profile', kwargs={'username': 'userok'}): 200,
            reverse('posts:post_detail', kwargs={'post_id': '100'}): 200,
            '/unexisting_page/': 404,
        }
        for address, code in response_list.items():
            with self.subTest(address=address):
                response = PostURLTests.guest_client.get(address)
                self.assertEqual(response.status_code, code)

    # Авторизованный пользователь
    def test_task_list_url_exists_at_desired_location(self):
        """
        Страница редактирования поста доступна авторизованному пользователю.
        """
        response = PostURLTests.authorized_client.get(
            reverse('posts:post_edit', kwargs={'post_id': '100'})
        )
        self.assertEqual(response.status_code, 200)

    def test_task_list_url_exists_at_desired_location(self):
        """
        Страница создания нового поста доступна авторизованному пользователю.
        """
        response = PostURLTests.authorized_client.get(
            reverse('posts:post_create')
        )
        self.assertEqual(response.status_code, 200)

    # Проверяем редиректы для неавторизованного пользователя (Redirects)
    def test_task_list_url_redirect_anonymous_on_auth_login(self):
        """Страница по адресу /posts/100/edit/ перенаправит анонимного
        пользователя на страницу логина.
        """
        reverse_page = reverse('posts:post_edit', kwargs={'post_id': '100'})
        response = self.guest_client.get(reverse_page, follow=True)
        self.assertRedirects(
            response, '/auth/login/?next=' + reverse_page
        )

    def test_task_detail_url_redirect_anonymous_on_auth_login(self):
        """Страница по адресу /create/ перенаправит анонимного
        пользователя на страницу логина.
        """
        reverse_page = reverse('posts:post_create')
        response = self.client.get(reverse_page, follow=True)
        self.assertRedirects(
            response, '/auth/login/?next=' + reverse_page
        )

    # Проверяем используемые шаблоны (templates)
    def test_urls_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        post = int(PostURLTests.post.pk)
        templates_url_names = {
            reverse('posts:index'): 'posts/index.html',
            reverse(
                'posts:group_list', kwargs={'slug': PostURLTests.group.slug}
            ): 'posts/group_list.html',
            reverse(
                'posts:profile', kwargs={'username': PostURLTests.user}
            ): 'posts/profile.html',
            reverse(
                'posts:post_detail', kwargs={'post_id': post}
            ): 'posts/post_detail.html',
            reverse(
                'posts:post_edit', kwargs={'post_id': post}
            ): 'posts/create_post.html',
            reverse('posts:post_create'): 'posts/create_post.html',
        }
        for address, template in templates_url_names.items():
            with self.subTest(address=address):
                response = self.authorized_client.get(address)
                self.assertTemplateUsed(response, template)
