import shutil
import tempfile

from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.cache import cache
from django.test import Client, TestCase, override_settings
from django.urls import reverse
from django import forms

from ..models import Comment, Follow, Post, Group, User


TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostViewsTests(TestCase):
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
        cls.uploaded = SimpleUploadedFile(
            name='small.gif',
            content=small_gif,
            content_type='image/gif'
        )
        cls.user = User.objects.create_user(username='HasNoName')
        cls.user2 = User.objects.create_user(username='NoName')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Тестовое описание',
        )
        posts = [
            Post(
                author=cls.user, group=cls.group,
                text=f'{n} Текстовый пост'
            )
            for n in range(2, 14)
        ]
        (Post.objects.bulk_create(posts))
        cls.post = Post.objects.create(
            author=cls.user,
            group=cls.group,
            text='Текстовый пост',
            image=cls.uploaded
        )
        print(Post.objects.all())

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        self.authorized_client2 = Client()
        self.authorized_client2.force_login(self.user2)
        self.index_url = reverse('posts:index')
        self.group_list_url = reverse(
            'posts:group_list', args=[PostViewsTests.post.group.slug]
        )
        self.profile_url = reverse(
            'posts:profile', args=[PostViewsTests.post.author]
        )
        self.post_detail_url = reverse(
            'posts:post_detail', args=[PostViewsTests.post.pk]
        )
        self.post_create_url = reverse('posts:post_create')
        self.post_edit_url = reverse(
            'posts:post_edit', args=[PostViewsTests.post.pk]
        )
        self.add_comment_url = reverse(
            'posts:add_comment', args=[PostViewsTests.post.pk]
        )
        self.profile_follow_url = reverse(
            'posts:profile_follow', args=[PostViewsTests.post.author]
        )
        self.unprofile_follow_url = reverse(
            'posts:profile_unfollow', args=[PostViewsTests.post.author]
        )
        self.follow_index_url = reverse('posts:follow_index')

        cache.clear()

    def test_cache_index_page(self):
        """Проверка кэширования главной страницы"""
        response = self.authorized_client.get(self.index_url)
        Post.objects.all().delete()
        response_2 = self.authorized_client.get(self.index_url)
        self.assertEqual(response.content, response_2.content)

    def test_index_page_show_correct_context(self):
        """"Шаблон index сформирован с правильным контекстом """
        response = self.authorized_client.get(self.index_url)
        self.assertEqual(
            response.context['page_obj'][0].text, PostViewsTests.post.text
        )
        self.assertEqual(
            response.context['page_obj'][0].author, PostViewsTests.post.author)
        self.assertEqual(
            response.context['page_obj'][0].group, PostViewsTests.post.group)
        self.assertEqual(
            response.context['page_obj'][0].image, PostViewsTests.post.image
        )

    def test_page_index_paginator(self):
        """Проверка паджинатора страницы index"""
        response = self.authorized_client.get(self.index_url)
        self.assertEqual(len(response.context['page_obj']), 10)
        response = self.authorized_client.get(self.index_url + '?page=2')
        self.assertEqual(len(response.context['page_obj']), 3)

    def test_group_list_page_show_correct_context(self):
        """"Шаблон group_list сформирован с правильным контекстом"""
        """Список постов отфильтрованных по группе"""
        response = self.authorized_client.get(self.group_list_url)
        self.assertEqual(
            response.context['page_obj'][0].text, PostViewsTests.post.text
        )
        self.assertEqual(
            response.context['page_obj'][0].author, PostViewsTests.post.author)
        self.assertEqual(
            response.context['page_obj'][0].group, PostViewsTests.post.group)
        self.assertEqual(
            response.context['page_obj'][0].image, PostViewsTests.post.image
        )

    def test_group_list_page_paginator(self):
        """Проверка паджинатора страницы group_list"""
        response = self.authorized_client.get(self.group_list_url)
        self.assertEqual(len(response.context['page_obj']), 10)
        response = self.authorized_client.get(self.group_list_url + '?page=2')
        self.assertEqual(len(response.context['page_obj']), 3)

    def test_profile_url_page_show_correct_context(self):
        """"Шаблон profile_url сформирован с правильным контекстом """
        """Список постов отфильтрованных по пользователю"""
        response = self.authorized_client.get(self.profile_url)
        self.assertEqual(
            response.context['page_obj'][0].text, PostViewsTests.post.text
        )
        self.assertEqual(
            response.context['page_obj'][0].author, PostViewsTests.post.author)
        self.assertEqual(
            response.context['page_obj'][0].group, PostViewsTests.post.group)
        self.assertEqual(
            response.context['page_obj'][0].image, PostViewsTests.post.image
        )

    def test_profile_url_page_paginator(self):
        """Проверка паджинатора страницы profile_url"""
        response = self.authorized_client.get(self.profile_url)
        self.assertEqual(len(response.context['page_obj']), 10)
        response = self.authorized_client.get(self.profile_url + '?page=2')
        self.assertEqual(len(response.context['page_obj']), 3)

    def test_post_detail_url_page(self):
        """Один пост отфильтрованный по pk. Страница поста"""
        response = self.authorized_client.get(self.post_detail_url)
        self.assertEqual(response.context['post'].pk, self.post.pk)
        self.assertEqual(
            response.context['post'].text, PostViewsTests.post.text
        )
        self.assertEqual(
            response.context['post'].author, PostViewsTests.post.author)
        self.assertEqual(
            response.context['post'].group, PostViewsTests.post.group)
        self.assertEqual(
            response.context['post'].image, PostViewsTests.post.image
        )

    def test_post_create_url_form_page(self):
        """Форма создания поста"""
        response = self.authorized_client.get(self.post_create_url)
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField,
            'image': forms.fields.ImageField
        }

        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context.get('form').fields.get(value)
                self.assertIsInstance(form_field, expected)

    def test_post_edit_url_show_correct_context(self):
        """"Шаблон post_edit_url выводит форму редактрования поста"""
        """с текстом поста"""
        response = self.authorized_client.get(self.post_edit_url)
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField,
            'image': forms.fields.ImageField
        }

        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context.get('form').fields.get(value)
                self.assertIsInstance(form_field, expected)

    def test_comments_only_authorized_client(self):
        """Комментировать посты может только авторизованный пользователь"""
        response = self.guest_client.get(self.add_comment_url)
        self.assertEqual(response.status_code, 302)

    def test_comments_add_on_the_page_post(self):
        """"После отправки комментария, он появляется на странице поста."""
        count_comment = Comment.objects.all().count()
        form_data = {
            'text': 'Комментарий',
            'post': self.post.pk,
            'author': self.user
        }
        self.authorized_client.post(
            self.add_comment_url,
            data=form_data,
            follow=True
        )
        self.assertEqual(
            Comment.objects.all().count(), count_comment + 1)
        response = self.authorized_client.get(self.post_detail_url)
        self.assertEqual(
            response.context['comments'].count(), count_comment + 1
        )

    def test_profile_follow(self):
        """Авторизованный пользователь может подписываться на других"""
        self.authorized_client2.get(self.profile_follow_url)
        self.assertTrue(
            Follow.objects.filter(
                user=PostViewsTests.user2,
                author=PostViewsTests.user).exists()
        )

    def test_profile_unfollow(self):
        """Авторизованный пользователь может отписываться"""
        self.authorized_client2.get(self.unprofile_follow_url)
        self.assertFalse(
            Follow.objects.filter(
                user=PostViewsTests.user2,
                author=PostViewsTests.user).exists()
        )

    def test_cant_follow_youself(self):
        """Нельзя подписаться на самого себя"""
        self.authorized_client.get(self.profile_follow_url)
        self.assertFalse(
            Follow.objects.filter(
                user=PostViewsTests.user,
                author=PostViewsTests.user).exists()
        )

    def test_follow_index_not_show_for_unauth(self):
        """Новая запись не появляется в ленте тех, кто на него не подписан"""
        response = self.authorized_client2.get(self.follow_index_url)
        self.assertEqual(len(response.context['page_obj']), 0)

    def test_follow_show_for_auth(self):
        """Новая запись появляется в ленте тех, кто на него подписан"""
        response = self.authorized_client2.get(self.follow_index_url)
        self.assertEqual(len(response.context['page_obj']), 0)
