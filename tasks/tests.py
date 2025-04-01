from django.test import TestCase, RequestFactory
from django.contrib.auth.models import User
from rest_framework import status
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken
from .models import Task
from .views import TaskViewSet, RegisterView, LoginView, LogoutView

class RegisterViewTest(TestCase):
    def setUp(self):
        self.client = APIClient()

    def test_register_success(self):
        data = {
            'username': 'newuser',
            'password': 'newpass123',
            'email': 'new@example.com'
        }
        response = self.client.post('/api/register/', data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(User.objects.filter(username='newuser').exists())

    def test_register_invalid_data(self):
        data = {
            'username': '',
            'password': 'short',
            'email': 'invalid'
        }
        response = self.client.post('/api/register/', data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('username', response.data)

class LoginViewTest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )

    def test_login_success(self):
        data = {
            'username': 'testuser',
            'password': 'testpass123'
        }
        response = self.client.post('/api/login/', data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.data)
        self.assertIn('refresh', response.data)
        self.assertIn('id', response.data)

    def test_login_invalid_credentials(self):
        data = {
            'username': 'wronguser',
            'password': 'wrongpass'
        }
        response = self.client.post('/api/login/', data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('error', response.data)

class LogoutViewTest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.refresh = RefreshToken.for_user(self.user)

    def test_logout_success(self):
        data = {
            'refresh_token': str(self.refresh)
        }
        response = self.client.post('/api/logout/', data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('message', response.data)

    def test_logout_missing_token(self):
        response = self.client.post('/api/logout/', {})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('error', response.data)

    def test_logout_invalid_token(self):
        data = {
            'refresh_token': 'invalidtoken'
        }
        response = self.client.post('/api/logout/', data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('error', response.data)

class TaskViewSetTest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.task = Task.objects.create(
            title='Test Task',
            description='Test Description',
            user=self.user
        )
        refresh = RefreshToken.for_user(self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {refresh.access_token}')

    def test_get_queryset(self):
        response = self.client.get('/api/tasks/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['title'], 'Test Task')

    def test_perform_create(self):
        data = {
            'title': 'New Task',
            'description': 'New Description',
            'completed':'false',
            'user':self.user.id
        }
        response = self.client.post('/api/tasks/', data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Task.objects.count(), 2)
        self.assertEqual(Task.objects.last().title, 'New Task')

    def test_unauthenticated_access(self):
        client = APIClient()  # Unauthenticated client
        response = client.get('/api/tasks/')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
