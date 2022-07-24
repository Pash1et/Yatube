import shutil
import tempfile

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from ..forms import PostForm
from ..models import Group, Post

User = get_user_model()


TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostsPageTest(TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        cls.user = User.objects.create(username='Dmitry')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Тестовое описание',
        )

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

        cls.post = Post.objects.create(
            text='Тестовый текст поста',
            author=PostsPageTest.user,
            group=PostsPageTest.group,
            image=uploaded,
        )
        cls.form = PostForm()

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self) -> None:
        super().setUp()
        self.auth_user = Client()
        self.auth_user.force_login(PostsPageTest.user)
        cache.clear()

    def check_correct_context(self, context, object):
        result = {
            context.get('post').author: object.author,
            context.get('post').text: object.text,
            context.get('post').group: object.group,
            context.get('post').image: object.image,
        }
        for context, object in result.items():
            with self.subTest(context=context, object=object):
                self.assertEqual(context, object)

    def test_pages_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        templates_page_names = {
            reverse('posts:index'): 'posts/index.html',
            reverse(
                'posts:group_list',
                kwargs={
                    'slug': PostsPageTest.group.slug
                }): 'posts/group_list.html',
            reverse(
                'posts:profile',
                kwargs={
                    'username': PostsPageTest.user.username
                }): 'posts/profile.html',
            reverse(
                'posts:post_detail',
                kwargs={
                    'post_id': PostsPageTest.group.pk
                }): 'posts/post_detail.html',
            reverse(
                'posts:post_edit',
                kwargs={
                    'post_id': PostsPageTest.group.pk
                }): 'posts/create_posts.html',
            reverse('posts:post_create'): 'posts/create_posts.html',
        }

        for reverse_name, template in templates_page_names.items():
            with self.subTest(reverse_name=reverse_name):
                response = self.auth_user.get(reverse_name)
                self.assertTemplateUsed(response, template)

    def test_index_page_show_correct_context(self):
        """Шаблон index сформирован с правильным контекстом."""
        response = self.auth_user.get(reverse('posts:index'))
        self.check_correct_context(
            response.context,
            PostsPageTest.post
        )

    def test_group_page_show_correct_context(self):
        """Шаблон group_list сформирован с правильным контекстом."""
        response = self.auth_user.get(
            reverse('posts:group_list', kwargs={
                'slug': PostsPageTest.group.slug
            })
        )
        self.check_correct_context(
            response.context,
            PostsPageTest.post
        )
        object_group = response.context['group']
        group_title = object_group.title
        group_description = object_group.description
        self.assertEqual(group_title, PostsPageTest.group.title)
        self.assertEqual(group_description, PostsPageTest.group.description)

    def test_profile_page_show_correct_context(self):
        """Шаблон profile сформирован с правильным контекстом."""
        response = self.auth_user.get(
            reverse('posts:profile', kwargs={
                'username': PostsPageTest.user.username
            })
        )
        self.check_correct_context(
            response.context,
            PostsPageTest.post
        )
        object_author = response.context['author']
        author = object_author.username
        self.assertEqual(author, PostsPageTest.user.username)

    def test_post_detail_show_correct_context(self):
        """Шаблон post_detail сформирован с правильным контекстом."""
        response = self.auth_user.get(
            reverse('posts:post_detail', kwargs={
                'post_id': PostsPageTest.post.pk
            })
        )
        self.check_correct_context(
            response.context,
            PostsPageTest.post
        )

    def test_create_post_show_correct_form(self):
        """Проверка страницы создания поста на корректность форм"""
        response = self.auth_user.get(reverse('posts:post_create'))
        form_field = response.context.get('form')
        self.assertIsInstance(form_field, PostForm)


class PaginatorViewsTest(TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        cls.user = User.objects.create(username='Dmitry')

        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Тестовое описание',
        )

        for i in range(13):
            model_post = [Post(
                text=f'Тестовый текст поста {i}',
                author=PaginatorViewsTest.user,
                group=PaginatorViewsTest.group,
            )]
            cls.post = Post.objects.bulk_create(model_post)

    def setUp(self) -> None:
        super().setUp()
        self.auth_user = Client()
        self.auth_user.force_login(PaginatorViewsTest.user)
        cache.clear()

    def test_first_index_page_contains_ten_records(self):
        """Количество постов на первой странице index равно 10."""
        response = self.auth_user.get(reverse('posts:index'))
        self.assertEqual(len(response.context['page_obj']), 10)

    def test_second_index_page_contains_three_records(self):
        """На второй странице index должно быть три поста."""
        response = self.auth_user.get(reverse('posts:index') + '?page=2')
        self.assertEqual(len(response.context['page_obj']), 3)

    def test_first_group_list_page_contains_ten_records(self):
        """Количесвто постов на первой странице group_list равно 10."""
        response = self.auth_user.get(
            reverse('posts:group_list', kwargs={
                'slug': PaginatorViewsTest.group.slug
            })
        )
        self.assertEqual(len(response.context['page_obj']), 10)

    def test_second_group_list_page_contains_three_records(self):
        """Количесвто постов на второй странице group_list равно 3."""
        response = self.auth_user.get(
            reverse('posts:group_list', kwargs={
                'slug': PaginatorViewsTest.group.slug
            }) + '?page=2'
        )
        self.assertEqual(len(response.context['page_obj']), 3)

    def test_first_profile_page_contains_ten_records(self):
        """Количесвто постов на первой странице profile равно 10."""
        response = self.auth_user.get(
            reverse('posts:profile', kwargs={
                'username': PaginatorViewsTest.user.username
            })
        )
        self.assertEqual(len(response.context['page_obj']), 10)

    def test_second_profile_page_contains_three_records(self):
        """Количесвто постов на второй странице profile равно 3."""
        response = self.auth_user.get(
            reverse('posts:profile', kwargs={
                'username': PaginatorViewsTest.user.username
            }) + '?page=2'
        )
        self.assertEqual(len(response.context['page_obj']), 3)


class TestCache(TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        cls.user = User.objects.create(username='Dmitry')

    def setUp(self) -> None:
        super().setUp()
        self.auth_user = Client()
        self.auth_user.force_login(TestCache.user)
        cache.clear()

    def test_index_page_cache(self):
        """Проверка кэширования главной страницы"""
        response = self.auth_user.get(
            reverse('posts:index')
        )
        context_before = response.context
        Post.objects.create(
            author=TestCache.user,
            text='Текст',
        )
        self.assertEqual(context_before, response.context)
        cache.clear()
        response = self.auth_user.get(
            reverse('posts:index')
        )
        self.assertNotEqual(context_before, response.context)


class TestFollow(TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        cls.user = User.objects.create(username='Dmitry')
        cls.user2 = User.objects.create(username='Lev')
        cls.post = Post.objects.create(
            author=cls.user2,
            text='Тестовый текст для проверки подписок',
        )

    def setUp(self) -> None:
        super().setUp()
        self.auth_user = Client()
        self.auth_user.force_login(TestCache.user)
        cache.clear()

    def test_subscribe(self):
        """Проверка возможности подписываться и отписываться"""
        self.assertEqual(TestCache.user.follower.count(), 0)
        self.auth_user.get(
            reverse(
                'posts:profile_follow',
                kwargs={'username': TestFollow.user2}
            )
        )
        self.assertEqual(TestCache.user.follower.count(), 1)
        self.auth_user.get(
            reverse(
                'posts:profile_unfollow',
                kwargs={'username': TestFollow.user2}
            )
        )
        self.assertEqual(TestCache.user.follower.count(), 0)

    def test_display_post_from_a_subscribe_user(self):
        """
        Проверка отображения поста у подписанного
        пользователя в follow_index
        """
        self.auth_user.get(
            reverse(
                'posts:profile_follow',
                kwargs={'username': TestFollow.user2}
            )
        )
        response = self.auth_user.get(reverse('posts:follow_index'))
        self.assertIn(TestFollow.post, response.context['page_obj'])

        self.auth_user.get(
            reverse(
                'posts:profile_unfollow',
                kwargs={'username': TestFollow.user2}
            )
        )
        response = self.auth_user.get(reverse('posts:follow_index'))
        self.assertNotIn(TestFollow.post, response.context['page_obj'])
