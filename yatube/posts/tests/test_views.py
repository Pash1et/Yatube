import shutil
import tempfile
from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.cache import cache
from django.test import TestCase, Client, override_settings
from django.contrib.auth import get_user_model
from django.urls import reverse
from django import forms
from ..models import Post, Group


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

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self) -> None:
        super().setUp()
        self.auth_user = Client()
        self.auth_user.force_login(PostsPageTest.user)
        cache.clear()

    def test_pages_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        index = 'posts/index.html'
        group_list = 'posts/group_list.html'
        profile = 'posts/profile.html'
        post_detail = 'posts/post_detail.html'
        create_posts = 'posts/create_posts.html'
        edit_posts = 'posts/create_posts.html'
        templates_page_names = {
            index: reverse('posts:index'),
            group_list: reverse(
                'posts:group_list',
                kwargs={'slug': PostsPageTest.group.slug}
            ),
            profile: reverse(
                'posts:profile',
                kwargs={'username': PostsPageTest.user.username}
            ),
            post_detail: reverse(
                'posts:post_detail',
                kwargs={'post_id': PostsPageTest.group.pk}
            ),
            create_posts: reverse(
                'posts:post_edit',
                kwargs={'post_id': PostsPageTest.group.pk}
            ),
            edit_posts: reverse('posts:post_create'),
        }

        for template, reverse_name in templates_page_names.items():
            with self.subTest(reverse_name=reverse_name):
                response = self.auth_user.get(reverse_name)
                self.assertTemplateUsed(response, template)

    def test_index_page_show_correct_context(self):
        """Шаблон index сформирован с правильным контекстом."""
        response = self.auth_user.get(reverse('posts:index'))
        first_object = response.context['page_obj'][0]
        post_text = first_object.text
        post_author = first_object.author
        post_group = first_object.group
        post_image = first_object.image
        self.assertEqual(post_text, PostsPageTest.post.text)
        self.assertEqual(post_author, PostsPageTest.post.author)
        self.assertEqual(post_group, PostsPageTest.post.group)
        self.assertEqual(post_image, PostsPageTest.post.image)

    def test_group_page_show_correct_context(self):
        """Шаблон group_list сформирован с правильным контекстом."""
        response = self.auth_user.get(
            reverse('posts:group_list', kwargs={
                'slug': PostsPageTest.group.slug
            })
        )
        first_object = response.context['group']
        second_object = response.context['page_obj'][0]
        group_title = first_object.title
        group_description = first_object.description
        group_text = second_object.text
        group_image = second_object.image
        self.assertEqual(group_title, PostsPageTest.group.title)
        self.assertEqual(group_description, PostsPageTest.group.description)
        self.assertEqual(group_text, PostsPageTest.post.text)
        self.assertEqual(group_image, PostsPageTest.post.image)

    def test_profile_page_show_correct_context(self):
        """Шаблон profile сформирован с правильным контекстом."""
        response = self.auth_user.get(
            reverse('posts:profile', kwargs={
                'username': PostsPageTest.user.username
            })
        )
        first_object = response.context['author']
        second_object = response.context['page_obj'][0]
        author = first_object.username
        user_text = second_object.text
        post_image = second_object.image
        self.assertEqual(author, PostsPageTest.user.username)
        self.assertEqual(user_text, PostsPageTest.post.text)
        self.assertEqual(post_image, PostsPageTest.post.image)

    def test_post_detail_show_correct_context(self):
        """Проверка контекста страницы поста"""
        response = self.auth_user.get(
            reverse('posts:post_detail', kwargs={
                'post_id': PostsPageTest.post.pk
            })
        )
        self.assertEqual(
            response.context.get('post').author,
            PostsPageTest.post.author
        )
        self.assertEqual(
            response.context.get('post').text,
            PostsPageTest.post.text
        )
        self.assertEqual(
            response.context.get('post').group,
            PostsPageTest.post.group
        )
        self.assertEqual(
            response.context.get('post').image,
            PostsPageTest.post.image
        )

    def test_create_post_show_correct_form(self):
        """Проверка страницы создания поста на корректность форм"""
        response = self.auth_user.get(reverse('posts:post_create'))
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField,
        }
        for field, expected in form_fields.items():
            with self.subTest(field=field):
                form_field = response.context.get('form').fields.get(field)
                is_edit = response.context.get('is_edit')
                self.assertIsInstance(form_field, expected)
                self.assertFalse(is_edit)

    def test_create_post_show_correct_form(self):
        """Проверка страницы редактирования поста на корректность форм"""
        response = self.auth_user.get(
            reverse('posts:post_edit', kwargs={
                'post_id': PostsPageTest.post.pk
            })
        )
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField,
        }
        for field, expected in form_fields.items():
            with self.subTest(field=field):
                form_field = response.context.get('form').fields.get(field)
                is_edit = response.context.get('is_edit')
                self.assertIsInstance(form_field, expected)
                self.assertTrue(is_edit)


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

    def test_first_index_page_contains_ten_records(self):
        """
        Количество постов на первой странице index равно 10.
        """

        response = self.auth_user.get(reverse('posts:index'))
        self.assertEqual(len(response.context['page_obj']), 10)

    def test_second_index_page_contains_three_records(self):
        """
        На второй странице index должно быть три поста.
        """

        response = self.auth_user.get(reverse('posts:index') + '?page=2')
        self.assertEqual(len(response.context['page_obj']), 3)

    def test_first_group_list_page_contains_ten_records(self):
        """
        Количесвто постов на первой странице group_list равно 10.
        """

        response = self.auth_user.get(
            reverse('posts:group_list', kwargs={
                'slug': PaginatorViewsTest.group.slug
            })
        )
        self.assertEqual(len(response.context['page_obj']), 10)

    def test_second_group_list_page_contains_three_records(self):
        """
        Количесвто постов на второй странице group_list равно 3.
        """

        response = self.auth_user.get(
            reverse('posts:group_list', kwargs={
                'slug': PaginatorViewsTest.group.slug
            }) + '?page=2'
        )
        self.assertEqual(len(response.context['page_obj']), 3)

    def test_first_profile_page_contains_ten_records(self):
        """
        Количесвто постов на первой странице profile равно 10.
        """

        response = self.auth_user.get(
            reverse('posts:profile', kwargs={
                'username': PaginatorViewsTest.user.username
            })
        )
        self.assertEqual(len(response.context['page_obj']), 10)

    def test_second_profile_page_contains_three_records(self):
        """
        Количесвто постов на второй странице profile равно 3.
        """

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

        cls.post = Post.objects.create(
            author=TestCache.user,
            text='Текст'
        )

    def setUp(self) -> None:
        super().setUp()
        self.auth_user = Client()
        self.auth_user.force_login(TestCache.user)
        cache.clear()

    def test_index_page_cache(self):
        """Проверка кэширования главной страницы"""
        post = Post.objects.create(
            author=TestCache.user,
            text='Текст'
        )
        response = self.auth_user.get(
            reverse('posts:index')
        )
        content = response.content
        post.delete()
        cache.clear()
        response_after = self.auth_user.get(
            reverse('posts:index')
        )
        content_after = response_after.content
        self.assertNotEqual(content_after, content)
