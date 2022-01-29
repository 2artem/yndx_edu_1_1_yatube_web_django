from django.contrib.auth import get_user_model
from django.db import IntegrityError
from django.db import transaction
from django.test import TestCase

from posts.models import Follow
from posts.models import Group
from posts.models import Post

User = get_user_model()


class PostModelTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='Тестовый слаг',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовая группа',
        )

    def test_models_have_correct_object_names(self):
        """Проверяем, что у моделей корректно работает __str__."""
        self.assertEqual(str(PostModelTest.post), 'Тестовая группа')
        self.assertEqual(str(PostModelTest.group), 'Тестовая группа')


class FollowModelTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user1 = User.objects.create_user(username='Author1')
        cls.user2 = User.objects.create_user(username='Author2')
        # Подписываемся Автором1 на Автора2
        Follow.objects.create(
            user=FollowModelTest.user1,
            author=FollowModelTest.user2
        )

    def test_models_prevent_self_follow(self):
        """Проверяем, что подписаться на себя невозможно"""
        calc_relationships = Follow.objects.all().count()
        try:
            with transaction.atomic():
                Follow.objects.create(
                    user=FollowModelTest.user1,
                    author=FollowModelTest.user1
                )
        except IntegrityError:
            pass
        self.assertEqual(Follow.objects.all().count(), calc_relationships)

    def test_models_unique_relationships(self):
        """Проверяем, что подписка существует в единственном экземпляре."""
        calc_relationships = Follow.objects.all().count()
        try:
            with transaction.atomic():
                Follow.objects.create(
                    user=FollowModelTest.user1,
                    author=FollowModelTest.user2
                )
        except IntegrityError:
            pass
        self.assertEqual(Follow.objects.all().count(), calc_relationships)
