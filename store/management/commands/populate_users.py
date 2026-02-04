from django.core.management.base import BaseCommand
from django.contrib.auth.models import User


class Command(BaseCommand):
    help = 'Populate database with 10 realistic users'

    def handle(self, *args, **kwargs):
        # Clear existing users (except superuser)
        User.objects.filter(is_superuser=False).delete()
        
        users_data = [
            {
                'username': 'john.smith',
                'email': 'john.smith@email.com',
                'first_name': 'John',
                'last_name': 'Smith',
            },
            {
                'username': 'sarah.johnson',
                'email': 'sarah.johnson@email.com',
                'first_name': 'Sarah',
                'last_name': 'Johnson',
            },
            {
                'username': 'michael.williams',
                'email': 'michael.williams@email.com',
                'first_name': 'Michael',
                'last_name': 'Williams',
            },
            {
                'username': 'emily.brown',
                'email': 'emily.brown@email.com',
                'first_name': 'Emily',
                'last_name': 'Brown',
            },
            {
                'username': 'david.jones',
                'email': 'david.jones@email.com',
                'first_name': 'David',
                'last_name': 'Jones',
            },
            {
                'username': 'jessica.garcia',
                'email': 'jessica.garcia@email.com',
                'first_name': 'Jessica',
                'last_name': 'Garcia',
            },
            {
                'username': 'james.miller',
                'email': 'james.miller@email.com',
                'first_name': 'James',
                'last_name': 'Miller',
            },
            {
                'username': 'linda.davis',
                'email': 'linda.davis@email.com',
                'first_name': 'Linda',
                'last_name': 'Davis',
            },
            {
                'username': 'robert.martinez',
                'email': 'robert.martinez@email.com',
                'first_name': 'Robert',
                'last_name': 'Martinez',
            },
            {
                'username': 'maria.rodriguez',
                'email': 'maria.rodriguez@email.com',
                'first_name': 'Maria',
                'last_name': 'Rodriguez',
            },
        ]
        
        created_count = 0
        for user_data in users_data:
            user = User.objects.create_user(
                username=user_data['username'],
                email=user_data['email'],
                password='12345678',
                first_name=user_data['first_name'],
                last_name=user_data['last_name'],
                is_active=True,
                is_staff=False,
                is_superuser=False
            )
            created_count += 1
            self.stdout.write(
                self.style.SUCCESS(f'Created user: {user.username} ({user.email})')
            )
        
        self.stdout.write(
            self.style.SUCCESS(f'\nSuccessfully created {created_count} users')
        )
        self.stdout.write(
            self.style.SUCCESS('All accounts are active with password: 12345678')
        )
