from django.test import TestCase, Client
from django.urls import reverse
from django.core.cache import cache
from http import HTTPStatus

from ..models import Post, Group, User


class PostURLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='HasNoName')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            group=cls.group,
            text='Тестовый пост',
        )

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        self.index_url = reverse('posts:index')
        self.group_list_url = reverse(
            'posts:group_list', args=[PostURLTests.post.group.slug]
        )
        self.profile_url = reverse(
            'posts:profile', args=[PostURLTests.post.author]
        )
        self.post_detail_url = reverse(
            'posts:post_detail', args=[PostURLTests.post.pk]
        )
        self.post_create_url = reverse('posts:post_create')
        self.post_edit_url = reverse(
            'posts:post_edit', args=[PostURLTests.post.pk]
        )
        cache.clear()

    def test_reverse_correct(self):
        """Проверка реверс возвращает верный URL"""
        response_reverse_and_url = {
            self.index_url: '/',
            self.group_list_url: '/group/test-slug/',
            self.profile_url: '/profile/HasNoName/',
            self.post_detail_url: '/posts/1/',
            self.post_create_url: '/create/',
            self.post_edit_url: '/posts/1/edit/'
        }
        for url_name, addres in response_reverse_and_url.items():
            with self.subTest(url_name=url_name):
                self.assertEqual(url_name, addres)

    def test_url_available_for_guest_client(self):
        """Гостевому пользователю доступны страницы и вызваны верные шаблоны"""
        response_page_and_templates = {
            self.index_url: 'posts/index.html',
            self.group_list_url: 'posts/group_list.html',
            self.profile_url: 'posts/profile.html',
            self.post_detail_url: 'posts/post_detail.html',
        }
        for url_page in response_page_and_templates.keys():
            with self.subTest(url_page=url_page):
                response = self.guest_client.get(url_page)
                self.assertEqual(
                    response.status_code, HTTPStatus.OK,
                    f'Ошибка доступа к странице {url_page}'
                )

        cache.clear()

        for url_page, templates in response_page_and_templates.items():
            with self.subTest(url_page=url_page):
                response = self.guest_client.get(url_page)
                self.assertTemplateUsed(
                    response, templates,
                    f'Шаблон для страницы {url_page} некорректный'
                )

    def test_redirect_guest_client_post_create_url(self):
        """Редирект гостя со страницы создания поста на страницу регистрацию"""
        response_create = self.guest_client.get(
            self.post_create_url, follow=True
        )
        self.assertRedirects(
            response_create, '/auth/login/?next=/create/'
        )

    def test_404_not_found(self):
        """При посещение несуществующей страницы ошибка 404"""
        """Выдает кастомный шаблон"""
        response = self.guest_client.get('/unexisting_page/')
        self.assertEqual(
            response.status_code, HTTPStatus.NOT_FOUND,
            'При входе на неизвестную страницу должен быть вывод 404')
        self.assertTemplateUsed(
            response, 'core/404.html'
        )

    def test_create_post_available_only_auth_user(self):
        """Создание поста доступно только зарегестрированному пользователю"""
        """Проверка шаблона"""
        response = self.authorized_client.get(self.post_create_url)
        self.assertEqual(
            response.status_code, HTTPStatus.OK,
            'Что бы создать пост, нужно зарегестрироваться'
        )
        self.assertTemplateUsed(
            response, 'posts/create_post.html',
            f'Шаблон для страницы {self.post_create_url} некорректный'
        )

    def test_edit_post_available_only_user(self):
        """Редактирование поста доступно только автору"""
        """Проверка шаблона"""
        response = self.authorized_client.get(self.post_edit_url)
        self.assertEqual(
            response.status_code, HTTPStatus.OK,
            'Что бы редактировать пост, требуется авторизоваться,'
            ' как создатель поста'
        )
        self.assertTemplateUsed(
            response, 'posts/create_post.html',
            f'Шаблон для страницы {self.post_create_url} некорректный'
        )
