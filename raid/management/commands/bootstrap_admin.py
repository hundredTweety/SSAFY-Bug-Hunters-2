"""Create the initial administrator from Render-only environment variables.

Never prints the password and never modifies an existing user.
Remove ADMIN_BOOTSTRAP_PASSWORD from Render after first success.
"""
import os

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError


class Command(BaseCommand):
    help = "Create a one-time initial admin when ADMIN_BOOTSTRAP_PASSWORD is set."

    def handle(self, *args, **options):
        password = os.environ.get("ADMIN_BOOTSTRAP_PASSWORD", "")
        if not password:
            return
        if len(password) < 16:
            raise CommandError("ADMIN_BOOTSTRAP_PASSWORD must have at least 16 characters.")
        username = "bughunters_admin"
        User = get_user_model()
        if User.objects.filter(username=username).exists():
            self.stdout.write("Initial administrator already exists; no changes made.")
            return
        User.objects.create_superuser(username=username, email="", password=password)
        self.stdout.write(self.style.SUCCESS("Initial administrator created. Remove ADMIN_BOOTSTRAP_PASSWORD from Render."))
