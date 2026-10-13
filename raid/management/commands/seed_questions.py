import json
from pathlib import Path
from django.core.management.base import BaseCommand
from raid.models import Question, RaidState
from django.conf import settings

class Command(BaseCommand):
    help='Load the raid question bank once (safe to repeat; edited questions preserved).'
    def handle(self,*args,**kwargs):
        bank=json.loads((Path(__file__).resolve().parents[2]/'question_bank.json').read_text(encoding='utf-8'))
        count=0
        for item in bank:
            _,created=Question.objects.get_or_create(code=item['code'],defaults={k:v for k,v in item.items() if k!='code'})
            count+=created
        RaidState.objects.get_or_create(pk=1, defaults={
            'max_hp':settings.RAID_MAX_HP,'remaining_hp':settings.RAID_MAX_HP,
            'damage_per_clear':settings.RAID_DAMAGE,
        })
        self.stdout.write(self.style.SUCCESS(f'{count} new question(s); total {Question.objects.count()}'))
