from django.contrib.auth import get_user_model
from django.test import Client
from django.test import TestCase
from django.urls import reverse
from django.core.cache import cache
from django import forms

from posts.models import Group
from posts.models import Post
from posts.models import Follow
from posts.models import Comment
from posts.forms import PostForm

User = get_user_model()


class PostViewsTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # Создаем неавторизованный клиент
        cls.guest_client = Client()
        # Создаем пользователей
        cls.user = User.objects.create_user(username='userok')
        cls.user_two = User.objects.create_user(username='userok_two')
        # Создаем клиент
        cls.authorized_client = Client()
        cls.authorized_client_two = Client()
        # Авторизуем пользователя
        cls.authorized_client.force_login(cls.user)
        cls.authorized_client_two.force_login(cls.user)
        # Создадим запись в БД с двумя группами для проверки, что пост
        # при создании не попал в группу, для которой не был предназначен
        cls.group_cats = Group.objects.create(
            slug='test-slug-cats',
            title='Котики',
            description='Группа про котов',
        )
        cls.group_dogs = Group.objects.create(
            slug='test-slug-dogs',
            title='Собачки',
            description='Группа про собак',
        )
        # Создадим 20 уникальных записей в БД для проверки паджинатора
        bulk_create_list = []
        for cycle_unit in range(1, 21):
            if cycle_unit % 2 == 0 and cycle_unit != 19 and cycle_unit != 1:
                cycle_group = cls.group_cats
            elif cycle_unit == 19:
                cycle_group = cls.group_dogs
            elif cycle_unit == 1:
                cycle_group = cls.group_cats
            else:
                cycle_group = None
            bulk_create_list.append(
                Post(
                    author=cls.user,
                    text=f'{cycle_unit} пост - текст',
                    group=cycle_group,
                )
            )
        Post.objects.bulk_create(bulk_create_list)
        cls.posts = Post.objects.all()

    # Проверяем правильность создания 20ти тестовых постов:
    # 19-ой пост принадлежит к группе title='Собачки'
    # 1-й пост -группа title='Котики', итого 11 постов в группе будет
    # далее, для каждого нечетного - группа не присвоена
    # для каждого четного- группа title='Котики'
    def test_posts_correctly_created(self):
        """Проверка целостности тестовых данных."""
        # Всего постов 20 штук
        self.assertEqual(len(PostViewsTests.posts), 20)
        # Группы тестовых постов верны
        for i in range(1, 21):
            if i % 2 == 0 and i != 19 and i != 1:
                self.assertEqual(
                    PostViewsTests.posts.get(pk=i).group,
                    PostViewsTests.group_cats
                )
            elif i == 19:
                self.assertEqual(
                    PostViewsTests.posts.get(pk=19).group,
                    PostViewsTests.group_dogs
                )
            elif i == 1:
                self.assertEqual(
                    PostViewsTests.posts.get(pk=1).group,
                    PostViewsTests.group_cats
                )
            else:
                self.assertEqual(PostViewsTests.posts.get(pk=i).group, None)
        # Проверка текста постов
        for i in range(1, 21):
            self.assertEqual(
                PostViewsTests.posts.get(pk=i).text, f'{i} пост - текст'
            )

    # Проверяем, что словарь context страниц содержит ожидаемые значения
    #
    # Главная страница - передает список постов:
    def test_index_page_show_correct_context(self):
        """Шаблон index сформирован с правильным контекстом."""
        response = self.authorized_client.get(reverse('posts:index'))
        # Тестируем паджинатор для первой страницы, из двух для 20ти постов
        self.assertEqual(len(response.context['page_obj']), 10)
        # Тестируем что 19тый пост принадлежит к группе Собачек
        for i in response.context['page_obj']:
            if i.group == PostViewsTests.group_dogs:
                self.assertEqual(i.group.slug, 'test-slug-dogs')
                self.assertEqual(i.group.title, 'Собачки')
                self.assertEqual(i.group.description, 'Группа про собак')
                self.assertEqual(i.text, '19 пост - текст')
                self.assertEqual(i.pk, 19)
        # Тестируем паджинатор для второй страницы,
        # должно быть 10 - при выводе по 10
        response = self.authorized_client.get(
            reverse('posts:index') + '?page=2'
        )
        self.assertEqual(len(response.context['page_obj']), 10)

    # Страница сообщества передает список постов отфильтрованных по группе
    def test_group_list_page_show_correct_context(self):
        """Шаблон group_list сформирован с правильным контекстом."""
        response = self.authorized_client.get(
            reverse('posts:group_list', kwargs={'slug': 'test-slug-cats'})
        )
        # Считаем количество постов сообщества group_cats
        calc = 0
        for i in PostViewsTests.posts:
            if i.group == PostViewsTests.group_cats:
                calc += 1
        self.assertEqual(calc, 11)
        # Тестируем паджинатор первой старницы
        self.assertEqual(len(response.context['page_obj']), 10)
        # Тестируем что опередана верная группа
        self.assertEqual(response.context['group'], PostViewsTests.group_cats)
        # Тестируем что опередан верный slug
        self.assertEqual(response.context['slug'], 'test-slug-cats')
        # Тестируем паджинаторп второй старницы, будет 1 пост на 2ой странице
        revrs_app = 'posts:group_list'
        response = self.authorized_client.get(
            reverse(revrs_app, kwargs={'slug': 'test-slug-cats'}) + '?page=2'
        )
        self.assertEqual(len(response.context['page_obj']), 1)

    # Страница Профайла передает список постов отфильтрованных по пользователю
    def test_profile_page_show_correct_context(self):
        """Шаблон profile сформирован с правильным контекстом."""
        response = self.authorized_client.get(
            reverse('posts:profile', kwargs={'username': 'userok'})
        )
        # Считаем количество постов автора 'userok'
        calc_usr_posts = 0
        for i in PostViewsTests.posts:
            if i.author == PostViewsTests.user:
                calc_usr_posts += 1
        self.assertEqual(calc_usr_posts, 20)
        # Тестируем паджинатор первой старницы
        self.assertEqual(len(response.context['page_obj']), 10)
        # Тестируем что передан правильный пользователь
        self.assertEqual(response.context['username'], PostViewsTests.user)
        # Тестируем что передано верное количество постов пользователя
        self.assertEqual(response.context['count_user_posts'], calc_usr_posts)
        # Тестируем паджинаторп второй старницы, будет 1 пост на 2ой странице
        revrs_app = 'posts:profile'
        response = self.authorized_client.get(
            reverse(revrs_app, kwargs={'username': 'userok'}) + '?page=2'
        )
        self.assertEqual(len(response.context['page_obj']), 10)

    # Страница Поста передает один пост отфильтрованный по id
    def test_post_detail_page_show_correct_context(self):
        """Шаблон post_detail сформирован с правильным контекстом."""
        response = self.authorized_client.get(
            reverse('posts:post_detail', kwargs={'post_id': '1'})
        )
        # Тестируем что передан объект класса Post
        self.assertEqual(type(response.context['post']), Post)
        # Тестируем что 1ый пост принадлежит к группе Кошек
        first_post = response.context['post']
        self.assertEqual(first_post.group.slug, 'test-slug-cats')
        self.assertEqual(first_post.group.title, 'Котики')
        self.assertEqual(first_post.group.description, 'Группа про котов')
        self.assertEqual(first_post.text, '1 пост - текст')
        self.assertEqual(first_post.pk, 1)
        # Тестируем что передано правильное имя пользователя
        self.assertEqual(response.context['username'], first_post.author)
        # Тестируем что передано верное количество постов пользователя
        calc_usr_posts = 0
        for i in PostViewsTests.posts:
            if i.author == PostViewsTests.user:
                calc_usr_posts += 1
        self.assertEqual(response.context['count_user_posts'], calc_usr_posts)

    # Тестируем создание комментариев
    def test_comment_creation(self):
        """Размещение комментариев доступно авторизованному пользователю."""
        comment_count = Comment.objects.count()
        # Формируем тестовые данные для формы
        post_id = PostViewsTests.posts.get(pk=1).pk
        form_data_comment = {
            'text': 'Коммент мой!',
            'post': post_id,
        }
        clients = [
            PostViewsTests.authorized_client,
            PostViewsTests.guest_client
        ]
        # Отправляем запрос авторизованным пользователем и неавторизованным
        for i in clients:
            response = i.post(
                reverse('posts:add_comment', kwargs={'post_id': '1'}),
                data=form_data_comment,
                follow=True,
            )
            if i == PostViewsTests.guest_client:
                self.assertRedirects(
                    response,
                    reverse('users:login')
                    + '?next='
                    + reverse('posts:add_comment', kwargs={'post_id': '1'})
                )
            else:
                self.assertRedirects(response, reverse(
                    'posts:post_detail', kwargs={'post_id': '1'})
                )
                # Проверяем, увеличилось ли число комментариев
                self.assertEqual(Comment.objects.count(), comment_count + 1)
                # Проверяем что комментарий создан и относится к посту
                self.assertTrue(
                    Comment.objects.filter(
                        post_id=post_id,
                        text='Коммент мой!',
                    ).exists()
                )

    # Страница редактирвоания Поста передает форму редактирования поста,
    # отфильтрованного по id
    def test_post_edit_page_show_correct_context(self):
        """Шаблон post_edit сформирован с правильным контекстом."""
        response = self.authorized_client.get(
            reverse('posts:post_edit', kwargs={'post_id': '3'})
        )
        # Тестируем что передана форма PostForm
        self.assertEqual(type(response.context.get('form')), PostForm)
        # Проверяет, что поля формы являются экземплярами указанных классов
        self.assertIsInstance(
            response.context.get('form').fields.get('text'),
            forms.fields.CharField
        )
        self.assertIsInstance(
            response.context.get('form').fields.get('group'),
            forms.ModelChoiceField
        )
        # Проверяем, что Пост принадлежит к экземпляру класса Post
        self.assertEqual(type(response.context.get('post')), Post)
        # Проверяем контекст  3го поста не имеющего группы
        post = response.context['post']
        self.assertEqual(post.group, None)
        self.assertEqual(post.text, '3 пост - текст')
        self.assertEqual(post.pk, 3)
        # Проверяем что контекст 'is_edit'
        # передает информацию о редактировании поста
        self.assertEqual(response.context.get('is_edit'), True)

    # Страница создания Поста передает форму создания поста
    def test_post_create_page_show_correct_context(self):
        """Шаблон post_create сформирован с правильным контекстом."""
        response = self.authorized_client.get(reverse('posts:post_create'))
        # Тестируем что передана форма PostForm
        self.assertEqual(type(response.context.get('form')), PostForm)
        # Проверяет, что поле формы является экземпляром указанного класса
        self.assertIsInstance(
            response.context.get('form').fields.get('text'),
            forms.fields.CharField
        )

    # Дополнительная проверка при создании поста при выводе на страницы
    def test_checking_post_creation_on_pages(self):
        """
        При создании поста(в составе группы), он верно выводится на страницы.
        """
        # Пост 19, принадлежащий к группе 'Группа про собак':
        # Пост выводится на главную страницу сайта,
        # пост выводится на страницу выбранной группы,
        # пост выводится на профайл пользователя
        response_tuple = (
            self.authorized_client.get(reverse('posts:index')),
            self.authorized_client.get(
                reverse('posts:group_list', kwargs={'slug': 'test-slug-dogs'})
            ),
            self.authorized_client.get(
                reverse('posts:profile', kwargs={'username': 'userok'})
            ),
        )
        for response in response_tuple:
            post_output = False
            for i in response.context['page_obj']:
                if i.pk == 19 and i.group == PostViewsTests.group_dogs:
                    post_output = True
            self.assertEqual(post_output, True)
        # Пост не выводится в другие группы
        post_not_output = True
        response = self.authorized_client.get(
            reverse('posts:group_list', kwargs={'slug': 'test-slug-cats'})
        )
        for i in response.context['page_obj']:
            if i.pk == 19 and i.group == PostViewsTests.group_dogs:
                post_not_output = False
        self.assertEqual(post_not_output, True)

    # Тест, который проверяет работу кеша
    def test_cache_index(self):
        """Тест для проверки кеширования главной страницы."""
        # Всего 20 тестовых постов
        object_count = Post.objects.count()
        # Запоминаем контент страницы который останется в кэше
        first_cache = self.authorized_client.get(reverse(
            'posts:index')
        ).content
        # Удаляем крайний пост
        self.authorized_client.get(reverse(
            'posts:index')
        ).context['page_obj'][0].delete()
        # Убеждаемся что количество постов уменьшилось
        self.assertEqual(Post.objects.count(), object_count - 1)
        # Cравниваем получаемый контент, зная что крайнего поста уже нет в БД
        self.assertEqual(first_cache, self.authorized_client.get(reverse(
            'posts:index')
        ).content)
        # Чистим Кэш
        cache.clear()
        # Теперь содержимое контента не должно быть равно первоначальному
        self.assertNotEqual(first_cache, self.authorized_client.get(reverse(
            'posts:index')
        ).content)

    # Тесты, которые проверяют видимость постов по подписке на автора:
    def test_ability_subscribe_to_author(self):
        """Подписка на автора возможна."""
        self.authorized_client.get(reverse(
            'posts:profile_follow', kwargs={'username': 'userok_two'})
        )
        self.assertTrue(Follow.objects.filter(
            user=PostViewsTests.user,
            author=PostViewsTests.user_two
        ).exists())

    def test_post_visible_in_subscription(self):
        """Юзер видит пост автора, на которого подписан, у себя в ленте."""
        self.authorized_client.get(reverse(
            'posts:profile_follow', kwargs={'username': 'userok_two'})
        )
        Post.objects.create(
            author=PostViewsTests.user_two,
            text='Текст по подписке',
            group=None,
        )
        response = self.authorized_client.get(reverse('posts:follow_index'))
        self.assertEqual(
            response.context['page_obj'][0].text,
            'Текст по подписке'
        )

    def test_ability_unsubscribe_to_author(self):
        """Юзер может отписаться от Автора, на которого был подписан."""
        self.authorized_client.get(reverse(
            'posts:profile_follow', kwargs={'username': 'userok_two'})
        )
        self.assertTrue(Follow.objects.filter(
            user=PostViewsTests.user,
            author=PostViewsTests.user_two
        ).exists())
        self.authorized_client.get(reverse(
            'posts:profile_unfollow', kwargs={'username': 'userok_two'})
        )
        self.assertFalse(Follow.objects.filter(
            user=PostViewsTests.user,
            author=PostViewsTests.user_two
        ).exists())

    def test_3(self):
        """
        Юзер, после отписки, больше не увидит посты автора у себя в ленте.
        """
        # Проверяем что usr1 не увидит больше в своей ленте пост usr2
        self.authorized_client.get(reverse(
            'posts:profile_follow', kwargs={'username': 'userok_two'})
        )
        Post.objects.create(
            author=PostViewsTests.user_two,
            text='Текст по подписке',
            group=None,
        )
        response = self.authorized_client.get(reverse('posts:follow_index'))
        self.assertEqual(
            response.context['page_obj'][0].text,
            'Текст по подписке'
        )
        self.authorized_client.get(reverse(
            'posts:profile_unfollow', kwargs={'username': 'userok_two'})
        )
        cache.clear()
        response = self.authorized_client.get(reverse('posts:follow_index'))
        self.assertEqual(
            response.context['subscription'],
            'zero_authors'
        )
        self.assertEqual(len(response.context['page_obj']), 0)
