from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.conf import settings
from raid.models import Attempt, Clear, RaidState

class Command(BaseCommand):
    help='DANGEROUS: delete all attempts and clears and reset boss. Must use --confirm.'
    def add_arguments(self,parser):
        parser.add_argument('--confirm',action='store_true')
    def handle(self,*args,**options):
        if not options['confirm']:
            raise CommandError('Will erase game progress. Re-run with --confirm if intended.')
        with transaction.atomic():
            Attempt.objects.all().delete()
            Clear.objects.all().delete()
            RaidState.objects.update(max_hp=settings.RAID_MAX_HP,
                                     remaining_hp=settings.RAID_MAX_HP,
                                     damage_per_clear=settings.RAID_DAMAGE)
        self.stdout.write(self.style.WARNING('Raid cleared. Players and questions retained.'))
