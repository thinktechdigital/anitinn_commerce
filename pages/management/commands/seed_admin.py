from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from pages.models import UserProfile


class Command(BaseCommand):
    help = 'Create or reset the default admin superuser (admin / P@sswo1d)'

    def handle(self, *args, **options):
        username = 'admin'
        password = 'P@sswo1d'

        user, created = User.objects.get_or_create(
            username=username,
            defaults={
                'is_staff': True,
                'is_superuser': True,
            },
        )

        if not created:
            user.is_staff = True
            user.is_superuser = True

        user.set_password(password)
        user.save()

        profile, _ = UserProfile.objects.get_or_create(user=user)
        profile.role = 'ADMIN'
        profile.verified = True
        profile.tier = 'Platform Admin'
        profile.save()

        status = 'Created' if created else 'Updated'
        self.stdout.write(self.style.SUCCESS(
            f'{status} admin user  →  username: {username}  /  password: {password}'
        ))
