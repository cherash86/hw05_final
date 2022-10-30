import shutil
# создает времееный файл
import tempfile

from django import forms
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse
from posts.models import Follow, Group, Post

User = get_user_model()

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostViewTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        cls.image_name = 'small.gif'
        cls.uploaded = SimpleUploadedFile(
            name=cls.image_name,
            content=small_gif,
            content_type='image/gif'
        )
        cls.user = User.objects.create_user(username='test_user')
        cls.user_no_post = User.objects.create_user(
            username='test_user_2'
        )
        cls.group = Group.objects.create(
            title='Заголовок для 1 тестовой группы',
            slug='test_slug'
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовая запись для создания 1 поста',
            group=cls.group,
            image=cls.uploaded
        )
        cls.urls = {
            reverse('posts:index'): 'posts/index.html',
            reverse('posts:group_list',
                    kwargs={'slug': cls.group.slug}): 'posts/group_list.html',
            reverse('posts:profile', kwargs={'username':
                                             cls.post.author.username}):
            'posts/profile.html',
        }
        cls.group_posts = Group.objects.create(
            title='Второй тестовый заголовок',
            slug='test_slug3',
        )

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client_2 = Client()
        self.authorized_client.force_login(self.user)
        self.authorized_client_2.force_login(self.user_no_post)
        cache.clear()

    def _assert_post_has_attribs(self, post):
        self.assertEqual(post.id, self.post.id)
        self.assertEqual(post.text, self.post.text)
        self.assertEqual(post.author, self.post.author)
        self.assertEqual(post.group, self.group)
        self.assertEqual(post.image, f'posts/{self.uploaded}')

    def test_index_pages_show_correct_context(self):
        """Шаблон index сформирован с правильным контекстом."""
        response = self.authorized_client.get(reverse('posts:index'))
        post = response.context['page_obj'][0]
        self._assert_post_has_attribs(post)

    def test_group_list_show_correct_context(self):
        """Шаблон group_list сформирован с правильным контекстом."""
        response = self.authorized_client.get(
            reverse('posts:group_list', kwargs={'slug': self.group.slug})
        )
        group = response.context['group']
        self.assertEqual(group.title, self.group.title)
        self.assertEqual(group.slug, self.group.slug)

    def test_post_another_group(self):
        """Пост не попал в другую группу где этого поста нет"""
        response = self.authorized_client.get(
            reverse(
                'posts:group_list',
                kwargs={'slug': self.group_posts.slug})
        )
        self.assertEqual(len(response.context['page_obj']), 0)

    def test_profile_correct_context(self):
        """Шаблон profile сформирован с правильным контекстом"""
        response = self.authorized_client.get(
            reverse('posts:profile', kwargs={'username':
                                             self.post.author.username})
        )
        post = response.context['page_obj'][0]
        self._assert_post_has_attribs(post)

    def test_post_create_show_correct_context(self):
        """Шаблон post_create сформирован с правильным контекстом."""
        response = self.authorized_client.get(reverse('posts:post_create'))
        form_fields = {
            'group': forms.fields.ChoiceField,
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context['form'].fields[value]
                self.assertIsInstance(form_field, expected)

    def test_post_edit_show_correct_context(self):
        """Шаблон post_edit сформирован с правильным контекстом."""
        response = self.authorized_client.get(
            reverse('posts:post_edit', kwargs={'post_id': self.post.pk})
        )
        form_fields = {
            'group': forms.fields.ChoiceField,
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context['form'].fields[value]
                self.assertIsInstance(form_field, expected)

    def test_add_comment(self):
        """Авторизированный пользователь может оставить коментарий"""

        coments = {'text': 'тестовый комментарий'}
        self.authorized_client_2.post(
            reverse('posts:add_comment', kwargs={'post_id': self.post.pk}),
            data=coments, follow=True
        )
        response = self.authorized_client_2.get(f'/posts/{self.post.id}/')
        self.assertContains(response, coments['text'])

    def test_anonym_cannot_add_comments(self):
        """НЕ Авторизированный пользователь не может оставить коментарий"""
        coments = {'text': 'комент не пройдет'}
        self.guest_client.post(
            reverse('posts:add_comment', kwargs={'post_id': self.post.pk}),
            data=coments, follow=True
        )
        response = self.guest_client.get(f'/posts/{self.post.id}/')
        self.assertNotContains(response, coments['text'])

    def test_cache_index(self):
        """Проверка хранения и очищения кэша для index."""
        response = self.authorized_client.get(reverse('posts:index'))
        posts = response.content
        Post.objects.create(
            text='новейший пост',
            author=self.post.author,
        )
        response_old = self.authorized_client.get(reverse('posts:index'))
        old_posts = response_old.content
        self.assertEqual(old_posts, posts)
        cache.clear()
        response_new = self.authorized_client.get(reverse('posts:index'))
        new_posts = response_new.content
        self.assertNotEqual(old_posts, new_posts)


class FollowTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.user = User.objects.create_user(username='test_user')
        cls.user_following = User.objects.create_user(username='test_user2')
        cls.user_no_post = User.objects.create_user(
            username='test_user_2'
        )
        cls.group = Group.objects.create(
            title='Заголовок для 1 тестовой группы',
            slug='test_slug'
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовая запись для создания 1 поста',
            group=cls.group,
        )

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.client_auth_following = Client()
        self.authorized_client.force_login(self.user)
        self.client_auth_following.force_login(self.user_following)

    def test_follow_authorized(self):
        """ Авторизованный пользователь может подписываться"""
        self.client_auth_following.get(
            reverse('posts:profile_follow',
                    kwargs={'username': self.user.username})
        )
        self.assertEqual(Follow.objects.all().count(), 1)

    def test_follow_guest(self):
        """ не Авторизованный пользователь  не может подписываться"""
        self.guest_client.get(
            reverse('posts:profile_follow',
                    kwargs={'username': self.user.username})
        )
        self.assertEqual(Follow.objects.all().count(), 0)

    def test_unfollow(self):
        """
        Авторизованный пользователь может подписываться и отписаться от автора
        """
        self.client_auth_following.get(
            reverse('posts:profile_follow', kwargs={'username':
                                                    self.user.username})
        )

        self.client_auth_following.get(
            reverse('posts:profile_unfollow', kwargs={'username':
                                                      self.user.username})
        )
        self.assertEqual(Follow.objects.all().count(), 0)

    def test_subscription_feed(self):
        """запись появляется в ленте подписчиков"""
        response = self.client_auth_following.get(
            reverse('posts:follow_index')
        )
        post = response.context['page_obj'][0].text
        self.assertEqual(post, self.post.text)

    def test_subscription_feed(self):
        """Запись не появляется у неподписанных пользователей"""
        response = self.authorized_client.get(reverse('posts:follow_index'))
        self.assertNotContains(response, self.post.text)


class PaginatorViewsTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test_slug',
            description='Тестовое описание',
        )
        cls.page_list = [
            reverse(
                'posts:index'
            ),
            reverse(
                'posts:group_list',
                kwargs={'slug': 'test_slug'}
            ),
            reverse(
                'posts:profile',
                kwargs={'username': cls.user.username}
            )
        ]
        obj = [
            Post(
                author=cls.user,
                text='Тестовый пост Тестовый',
                group=cls.group
            )
            for i in range(13)
        ]
        # bulk_create возвращает созданные объекты в виде списка,
        #  взял из документации(увидев у человека)
        cls.post = Post.objects.bulk_create(obj)

    def test_first_page_contains_ten_records(self):
        """По 10 постов на первой странице у index, group_list и profile"""
        for url in self.page_list:
            response = self.client.get(url)
            self.assertEqual(len(response.context['page_obj']), 10)

    def test_second_page_contains_three_records(self):
        """По 3 поста на второй странице index, group_list и profile"""
        for url in self.page_list:
            response = self.client.get(url + '?page=2')
            self.assertEqual(len(response.context['page_obj']), 3)
