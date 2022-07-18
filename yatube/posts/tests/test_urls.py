from http import HTTPStatus
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.test import TestCase, Client
from posts.models import Group, Post


User = get_user_model()


class StaticUrlTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='Dmitry')

        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Тестовое описание',
        )

        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый текст',
            group=cls.group,
        )

        cls.public_urls = [
            ('/', 'posts/index.html'),
            (f'/group/{StaticUrlTests.group.slug}/', 'posts/group_list.html'),
            (f'/profile/{StaticUrlTests.user.username}/',
                'posts/profile.html'),
            (f'/posts/{StaticUrlTests.post.pk}/', 'posts/post_detail.html'),
        ]

        cls.private_urls = [
            ('/create/', '/auth/login/?next=/create/'),
            (f'/posts/{StaticUrlTests.post.pk}/edit/',
                f'/auth/login/?next=/posts/{StaticUrlTests.post.pk}/edit/'),
        ]

    def setUp(self):
        self.guest_client = Client()
        self.auth_client = Client()
        self.auth_client.force_login(StaticUrlTests.user)
        cache.clear()

    def test_public_urls_used_correct_template(self):
        """Проверяем, что вызываеются нужные html файлы"""
        for url, template in StaticUrlTests.public_urls:
            with self.subTest(url=url, template=template):
                response = self.guest_client.get(url)
                self.assertTemplateUsed(response, template)

    def test_public_urls_exists(self):
        """Проверяем, что страницы имеют статус 200"""
        for url, _ in StaticUrlTests.public_urls:
            with self.subTest(url=url):
                response = self.guest_client.get(url)
                self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_urls_non_exists(self):
        """
        Проверим, что при вызове несуществующей страницы,
        получаем ошибку 404
        """

        response = self.guest_client.get('/non-exists-page/')
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)

    def test_urls_available_for_auth_user(self):
        """
        Проверка доступности создания поста
        только для авторизированного пользователя
        """

        response = self.auth_client.get('/create/')
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_available_edit_post_only_for_author(self):
        """Проверка доступности редактировать пост только автору"""
        response = self.auth_client.get(
            f'/posts/{StaticUrlTests.post.pk}/edit/'
        )
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_redirect_guest_user(self):
        """Проверка редиректа неавторизованного пользователя на страницу"""
        for url, redirect_url in StaticUrlTests.private_urls:
            with self.subTest(url=url, redirect_url=redirect_url):
                response = self.guest_client.get(url)
                self.assertRedirects(response, redirect_url)
