import json
from pathlib import Path
from django.test import Client,TestCase,override_settings
from django.urls import reverse
from raid.logic import check_patch,target_line
from raid.models import Player,Question,RaidState,Attempt,Clear
from raid.stats import confusion_stats

BANK = json.loads((Path(__file__).resolve().parents[1]/'question_bank.json').read_text(encoding='utf-8'))

class BugHuntersTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        for entry in BANK:
            Question.objects.create(**entry)
        RaidState.objects.create(pk=1,max_hp=1000,remaining_hp=1000,damage_per_clear=20)

    def join(self,name='헌터'):
        return self.client.post(reverse('join'),{'nickname':name,'consent':'yes'})

    def submit(self,code,patch_ok=True,case_ok=True):
        q=Question.objects.get(code=code)
        return self.client.post(reverse('submit',args=[q.pk]),{
            'line':str(target_line(q) if patch_ok else 1 if target_line(q)!=1 else 2),
            'patch':q.accepted_patches[0] if patch_ok else 'print(999)',
            'counterexample':str(q.counterexample_index if case_ok else (q.counterexample_index+1)%3),
        })

    def test_two_independent_players_share_boss_hp(self):
        # Each client has its own session, but both must affect the same shared boss.
        question = Question.objects.get(code='A01')
        for nickname in ('헌터가', '헌터나'):
            client = Client()
            joined = client.post(reverse('join'), {
                'nickname': nickname, 'consent': 'yes',
            })
            self.assertEqual(joined.status_code, 302)
            attack = client.post(reverse('submit', args=[question.pk]), {
                'line': str(target_line(question)),
                'patch': question.accepted_patches[0],
            })
            self.assertEqual(attack.status_code, 302)
            self.assertEqual(client.get(reverse('api_status')).json()['hp'],
                             1000 - 20 * (1 if nickname == '헌터가' else 2))
        self.assertEqual(Player.objects.count(), 2)
        self.assertEqual(Clear.objects.filter(damage=20).count(), 2)
        self.assertEqual(RaidState.objects.get(pk=1).remaining_hp, 960)

    def test_first_clear_damage_only_once(self):
        self.join()
        self.submit('A01')
        self.submit('A01')
        self.assertEqual(Clear.objects.count(),1)
        self.assertEqual(Attempt.objects.count(),1)
        self.assertEqual(RaidState.objects.get(pk=1).remaining_hp,980)

    @override_settings(RAID_MAX_CLEARS_PER_PLAYER=1)
    def test_damage_per_player_is_capped(self):
        self.join()
        self.submit('A01')
        self.submit('A02')
        self.assertEqual(list(Clear.objects.order_by('id').values_list('damage',flat=True)),[20,0])
        self.assertEqual(RaidState.objects.get(pk=1).remaining_hp,980)

    def test_hard_requires_counterexample(self):
        self.join()
        self.submit('A06',patch_ok=True,case_ok=False)
        self.assertEqual(Clear.objects.count(),0)
        self.assertEqual(Attempt.objects.count(),1)
        self.assertTrue(Attempt.objects.first().patch_correct)
        self.assertFalse(Attempt.objects.first().case_correct)
        self.submit('A06',patch_ok=True,case_ok=True)
        self.assertEqual(Clear.objects.count(),1)

    def test_first_attempt_only_statistics(self):
        self.join()
        self.submit('A01',patch_ok=False)
        self.submit('A01',patch_ok=False)
        self.submit('A01',patch_ok=True)
        rows,_=confusion_stats(category='array',minimum_players=1)
        record=next(row for row in rows if row['concept']=='초기값 설정')
        self.assertEqual((record['wrong'],record['total']), (1,1))

    def test_no_answers_before_clear(self):
        self.join()
        q=Question.objects.get(code='A06')
        page=self.client.get(reverse('question',args=[q.pk])).content.decode()
        self.assertNotIn(q.accepted_patches[0],page)
        self.assertNotIn(q.explanation,page)

    def test_no_anonymous_submit(self):
        self.submit('A01')
        self.assertEqual(Attempt.objects.count(),0)

    def test_report_locked_until_boss_defeated(self):
        page=self.client.get(reverse('results'))
        self.assertContains(page,'아직 잠겨')
        RaidState.objects.filter(pk=1).update(remaining_hp=0)
        page=self.client.get(reverse('results'))
        self.assertContains(page,'첫 제출 오답률 TOP 5')

    def test_api_has_no_answer_information(self):
        raw=self.client.get(reverse('api_status')).json()
        self.assertEqual(set(raw), {'hp','max_hp','progress','finished'})

    def test_all_patch_lines_unique(self):
        for q in Question.objects.all():
            self.assertTrue(check_patch(q,target_line(q),q.accepted_patches[0]),q.code)

    def test_join_requires_consent(self):
        self.client.post(reverse('join'),{'nickname':'나비'})
        self.assertEqual(Player.objects.count(),0)

    def test_healthcheck(self):
        self.assertEqual(self.client.get(reverse('healthcheck')).status_code,200)

    @override_settings(RAID_INVITE_CODE='class-join-2026')
    def test_invite_code_required(self):
        self.client.post(reverse('join'),{'nickname':'헌터A','consent':'yes'})
        self.assertFalse(Player.objects.exists())
        self.client.post(reverse('join'),{'nickname':'헌터A','consent':'yes','invite_code':'class-join-2026'})
        self.assertEqual(Player.objects.count(),1)
