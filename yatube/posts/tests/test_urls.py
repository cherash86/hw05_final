from http import HTTPStatus

from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse
from posts.models import Group, Post

User = get_user_model()


class PostURLTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='test_user')
        cls.user_no_post = User.objects.create_user(
            username='test_user_2'
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовая запись для создания нового поста',
        )

        cls. group = Group.objects.create(
            title=('Заголовок для тестовой группы'),
            slug='test_slug'
        )
        cls.url_names = (
            '/',
            '/group/test_slug/',
            '/profile/test_user/',
            '/posts/1/',
        )
        cls.templates_page_names = {
            reverse('posts:index'): 'posts/index.html',
            reverse('posts:post_create'): 'posts/post_create.html',
            reverse('posts:profile',
                    kwargs={'username':
                            cls.post.author.username}): 'posts/profile.html',
            reverse('posts:post_detail',
                    kwargs={'post_id':
                            cls.post.pk}): 'posts/post_detail.html',
            reverse('posts:group_list',
                    kwargs={'slug':
                            cls.group.slug}): 'posts/group_list.html',
            reverse('posts:post_edit',
                    kwargs={'post_id':
                            cls.post.pk}): 'posts/post_create.html',
        }

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        self.authorized_client_2 = Client()
        self.authorized_client_2.force_login(
            self.user_no_post
        )

    def test_page_404(self):
        response = self.guest_client.get('/Sanec/')
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)

    # если нужно вставлю отсольные тесты просто
    # толка в них сейчас нет
    # def test_task_list_url_redirect_anonymous_on_admin_login(self):
    # def test_create_url_exists_at_desired_location(self):
    # def test_urls_edit_author(self):
    # def test_urls_edit_non_authorized(self):
    # def test_urls_edit__authorized(self):
