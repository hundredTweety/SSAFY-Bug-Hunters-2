"""Run every startup maintenance step in a single Django process.

Render's free instances have a small CPU share and are restarted after idling,
so booting Django four times in start.sh noticeably slowed each cold start.
Each step is idempotent and keeps its own safety rules:
  migrate          applies only pending migrations
  clearsessions    deletes expired Django sessions only
  seed_questions   adds missing questions, never overwrites admin edits
  bootstrap_admin  creates the first admin only when explicitly configured
"""
from django.core.management import call_command
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Startup maintenance in one process: migrate, clearsessions, seed_questions, bootstrap_admin."

    def handle(self, *args, **options):
        call_command("migrate", interactive=False, verbosity=options["verbosity"])
        call_command("clearsessions")
        call_command("seed_questions")
        call_command("bootstrap_admin")
