from django.test import TestCase
from django.test import Client
from django.urls import reverse


class StaticURLTests(TestCase):
    def setUp(self):
        # Устанавливаем данные для тестирования
        # Создаём экземпляр клиента. Он неавторизован.
        self.guest_client = Client()

    def test_author(self):
        """Страница автора доступна любому пользователю."""
        # Отправляем запрос через client, созданный в setUp()
        response = self.guest_client.get(reverse('about:author'))
        self.assertEqual(response.status_code, 200)

    def test_tech(self):
        """Страница технологий доступна любому пользователю."""
        response = self.guest_client.get(reverse('about:tech'))
        self.assertEqual(response.status_code, 200)
