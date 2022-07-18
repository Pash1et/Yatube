import shutil
import tempfile
from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse
from django.contrib.auth import get_user_model
from ..models import Comment, Follow, Post


User = get_user_model()


TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostCreateFormTests(TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        cls.user = User.objects.create_user(username='Dmitry')
        cls.user2 = User.objects.create_user(username='Lev')
        cls.user3 = User.objects.create_user(username='Ilya')

        cls.post = Post.objects.create(
            author=PostCreateFormTests.user,
            text='Тестовый пост',
        )
        cls.post2 = Post.objects.create(
            author=PostCreateFormTests.user2,
            text='Тестовый пост',
        )
        cls.comment = Comment.objects.create(
            author=PostCreateFormTests.user,
            post=PostCreateFormTests.post,
            text='Тестовый комментарий'
        )

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self) -> None:
        super().setUp()
        self.auth_client = Client()
        self.auth_client.force_login(PostCreateFormTests.user)

    def test_create_post(self):
        """Проверка создания нового поста"""
        post_count = Post.objects.count()

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
            'author': PostCreateFormTests.user,
            'text': 'Новый пост',
            'image': uploaded,
        }
        response = self.auth_client.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True
        )
        self.assertRedirects(
            response,
            reverse('posts:profile', kwargs={
                'username': PostCreateFormTests.user.username
            })
        )
        self.assertEqual(Post.objects.count(), post_count + 1)

    def test_edit_post(self):
        """Проверка редактирования поста"""
        form_data = {
            'text': 'Редактированный текст',
        }
        response = self.auth_client.post(
            reverse('posts:post_edit', kwargs={
                'post_id': PostCreateFormTests.post.pk
            }),
            data=form_data,
            follow=True,
        )
        self.assertRedirects(
            response,
            reverse('posts:post_detail', kwargs={
                'post_id': PostCreateFormTests.post.pk
            })
        )
        self.assertEqual(response.context['post'].text, form_data['text'])

    def test_add_comment_for_auth_user(self):
        """
        Проверка возможности комментировать пост
        авторизированному пользователю
        """

        comment_count = Comment.objects.count()
        form_data = {
            'author': PostCreateFormTests.user,
            'post': PostCreateFormTests.post,
            'text': 'Второй коммент'
        }
        response = self.auth_client.post(
            reverse('posts:add_comment', kwargs={
                'post_id': PostCreateFormTests.post.pk
            }),
            data=form_data,
            follow=True,
        )
        self.assertRedirects(
            response,
            reverse('posts:post_detail', kwargs={
                'post_id': PostCreateFormTests.post.pk
            })
        )
        self.assertEqual(
            Comment.objects.count(),
            comment_count + 1
        )

    def test_subscribe(self):
        """Проверка возможности подписываться и отписываться"""
        subscribe_count_before = Follow.objects.count()
        following = Follow.objects.create(user=PostCreateFormTests.user,
                                          author=PostCreateFormTests.user2)
        self.assertEqual(Follow.objects.count(), subscribe_count_before + 1)

        following.delete()
        self.assertEqual(Follow.objects.count(), subscribe_count_before)

    def test_display_post_from_a_subscribe_user(self):
        """
        Проверка отображения поста у подписанного
        пользователя в follow_index
        """
        Follow.objects.create(user=PostCreateFormTests.user,
                              author=PostCreateFormTests.user2)
        posts = Post.objects.filter(
            author__following__user=PostCreateFormTests.user
        )
        self.assertEqual(posts.count(), 1)

        Post.objects.create(
            author=PostCreateFormTests.user3,
            text='Тестовый пост',
        )

        self.assertEqual(posts.count(), 1)
