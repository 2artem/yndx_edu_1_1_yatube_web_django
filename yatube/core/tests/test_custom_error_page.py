from django.test import TestCase
from django.test import Client


class CustomErrorPagesTestClass(TestCase):
    def setUp(self):
        # Создаём экземпляр клиента. Он неавторизован.
        self.guest_client = Client()

    def test_error_page(self):
        response = self.guest_client.get('/nonexist-page/')
        # Проверяем, что статус ответа сервера - 404
        self.assertEqual(response.status_code, 404)
        # Проверяем, что используется шаблон core/404.html
        self.assertTemplateUsed(response, 'core/404.html')
