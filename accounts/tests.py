from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
from .forms import UserRegistrationForm, UserUpdateForm


class UserRegistrationFormTest(TestCase):
    """Test cases for UserRegistrationForm"""
    
    def test_valid_registration_form(self):
        """Test form with valid data"""
        form_data = {
            'username': 'testuser',
            'email': 'test@example.com',
            'first_name': 'Test',
            'last_name': 'User',
            'password': 'securepassword123',
            'password_confirm': 'securepassword123',
        }
        form = UserRegistrationForm(data=form_data)
        self.assertTrue(form.is_valid())
    
    def test_password_mismatch(self):
        """Test form with mismatched passwords"""
        form_data = {
            'username': 'testuser',
            'email': 'test@example.com',
            'first_name': 'Test',
            'last_name': 'User',
            'password': 'securepassword123',
            'password_confirm': 'differentpassword',
        }
        form = UserRegistrationForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('password_confirm', form.errors)
    
    def test_short_password(self):
        """Test form with password less than 8 characters"""
        form_data = {
            'username': 'testuser',
            'email': 'test@example.com',
            'first_name': 'Test',
            'last_name': 'User',
            'password': 'short',
            'password_confirm': 'short',
        }
        form = UserRegistrationForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('password', form.errors)
    
    def test_duplicate_email(self):
        """Test form with already registered email"""
        User.objects.create_user(
            username='existinguser',
            email='test@example.com',
            password='password123'
        )
        form_data = {
            'username': 'newuser',
            'email': 'test@example.com',
            'first_name': 'New',
            'last_name': 'User',
            'password': 'securepassword123',
            'password_confirm': 'securepassword123',
        }
        form = UserRegistrationForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('email', form.errors)


class UserUpdateFormTest(TestCase):
    """Test cases for UserUpdateForm"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='password123'
        )
    
    def test_valid_update_form(self):
        """Test form with valid update data"""
        form_data = {
            'first_name': 'Updated',
            'last_name': 'Name',
            'email': 'newemail@example.com',
        }
        form = UserUpdateForm(data=form_data, instance=self.user)
        self.assertTrue(form.is_valid())
    
    def test_update_with_existing_email(self):
        """Test updating with email used by another user"""
        User.objects.create_user(
            username='anotheruser',
            email='another@example.com',
            password='password123'
        )
        form_data = {
            'first_name': 'Test',
            'last_name': 'User',
            'email': 'another@example.com',
        }
        form = UserUpdateForm(data=form_data, instance=self.user)
        self.assertFalse(form.is_valid())
        self.assertIn('email', form.errors)


class UserRegistrationViewTest(TestCase):
    """Test cases for user registration view"""
    
    def setUp(self):
        self.client = Client()
        self.register_url = reverse('accounts:register')
    
    def test_registration_page_loads(self):
        """Test registration page loads successfully"""
        response = self.client.get(self.register_url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'accounts/register.html')
    
    def test_successful_registration(self):
        """Test successful user registration"""
        form_data = {
            'username': 'newuser',
            'email': 'newuser@example.com',
            'first_name': 'New',
            'last_name': 'User',
            'password': 'securepassword123',
            'password_confirm': 'securepassword123',
        }
        response = self.client.post(self.register_url, form_data)
        self.assertEqual(response.status_code, 302)  # Redirect after success
        self.assertTrue(User.objects.filter(username='newuser').exists())
        
        # Check user is logged in
        user = User.objects.get(username='newuser')
        self.assertTrue(user.check_password('securepassword123'))
    
    def test_registration_with_invalid_data(self):
        """Test registration with invalid data"""
        form_data = {
            'username': 'newuser',
            'email': 'invalid-email',
            'first_name': 'New',
            'last_name': 'User',
            'password': 'securepassword123',
            'password_confirm': 'differentpassword',
        }
        response = self.client.post(self.register_url, form_data)
        self.assertEqual(response.status_code, 200)
        self.assertFalse(User.objects.filter(username='newuser').exists())
    
    def test_authenticated_user_redirect(self):
        """Test that authenticated users are redirected from registration"""
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='password123'
        )
        self.client.login(username='testuser', password='password123')
        response = self.client.get(self.register_url)
        self.assertEqual(response.status_code, 302)  # Redirect


class UserLoginViewTest(TestCase):
    """Test cases for user login view"""
    
    def setUp(self):
        self.client = Client()
        self.login_url = reverse('accounts:login')
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='password123'
        )
    
    def test_login_page_loads(self):
        """Test login page loads successfully"""
        response = self.client.get(self.login_url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'accounts/login.html')
    
    def test_successful_login(self):
        """Test successful user login"""
        response = self.client.post(self.login_url, {
            'username': 'testuser',
            'password': 'password123',
        })
        self.assertEqual(response.status_code, 302)  # Redirect after success
    
    def test_login_with_invalid_credentials(self):
        """Test login with invalid credentials"""
        response = self.client.post(self.login_url, {
            'username': 'testuser',
            'password': 'wrongpassword',
        })
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Invalid username or password')
    
    def test_authenticated_user_redirect(self):
        """Test that authenticated users are redirected from login"""
        self.client.login(username='testuser', password='password123')
        response = self.client.get(self.login_url)
        self.assertEqual(response.status_code, 302)


class UserLogoutViewTest(TestCase):
    """Test cases for user logout view"""
    
    def setUp(self):
        self.client = Client()
        self.logout_url = reverse('accounts:logout')
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='password123'
        )
    
    def test_logout(self):
        """Test user logout"""
        self.client.login(username='testuser', password='password123')
        response = self.client.get(self.logout_url)
        self.assertEqual(response.status_code, 302)  # Redirect after logout


class UserProfileViewTest(TestCase):
    """Test cases for user profile view"""
    
    def setUp(self):
        self.client = Client()
        self.profile_url = reverse('accounts:profile')
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='password123'
        )
    
    def test_profile_requires_login(self):
        """Test that profile page requires login"""
        response = self.client.get(self.profile_url)
        self.assertEqual(response.status_code, 302)  # Redirect to login
    
    def test_profile_page_loads_for_authenticated_user(self):
        """Test profile page loads for logged in user"""
        self.client.login(username='testuser', password='password123')
        response = self.client.get(self.profile_url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'accounts/profile.html')
    
    def test_profile_update(self):
        """Test successful profile update"""
        self.client.login(username='testuser', password='password123')
        form_data = {
            'first_name': 'Updated',
            'last_name': 'Name',
            'email': 'updated@example.com',
        }
        response = self.client.post(self.profile_url, form_data)
        self.user.refresh_from_db()
        self.assertEqual(self.user.first_name, 'Updated')
        self.assertEqual(self.user.last_name, 'Name')
        self.assertEqual(self.user.email, 'updated@example.com')
