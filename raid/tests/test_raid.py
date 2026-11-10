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

    def submit(self,code,patch_ok=True,case_ok=True,line_ok=True):
        q=Question.objects.get(code=code)
        expected=target_line(q)
        line=expected if line_ok else (1 if expected != 1 else 2)
        self.client.post(reverse('check_line',args=[q.pk]),{'line':str(line)})
        return self.client.post(reverse('submit',args=[q.pk]),{
            'choice':str(q.choices.index(q.accepted_patches[0]) if patch_ok else next(i for i,v in enumerate(q.choices) if v != q.accepted_patches[0])),
        })

    def test_two_independent_players_share_boss_hp(self):
        q=Question.objects.get(code='A01')
        choice=q.choices.index(q.accepted_patches[0])
        for n, nickname in enumerate(('헌터가','헌터나'),start=1):
            client=Client()
            self.assertEqual(client.post(reverse('join'),{'nickname':nickname,'consent':'yes'}).status_code,302)
            self.assertEqual(client.post(reverse('check_line',args=[q.pk]),{'line':str(target_line(q))}).status_code,302)
            self.assertEqual(client.post(reverse('submit',args=[q.pk]),{'choice':str(choice)}).status_code,302)
            self.assertEqual(client.get(reverse('api_status')).json()['hp'],1000-20*n)
        self.assertEqual(Player.objects.count(),2)
        self.assertEqual(Clear.objects.filter(damage=20).count(),2)
        self.assertEqual(RaidState.objects.get(pk=1).remaining_hp,960)

    def test_wrong_line_even_with_correct_choice_does_not_attack(self):
        self.join()
        self.submit('A01',line_ok=False)
        self.assertEqual(Clear.objects.count(),0)
        self.assertEqual(Attempt.objects.count(),0)
        self.assertEqual(RaidState.objects.get(pk=1).remaining_hp,1000)
        self.submit('A01')
        self.assertEqual(Clear.objects.count(),1)
        self.assertEqual(RaidState.objects.get(pk=1).remaining_hp,980)

    def test_no_line_cannot_attack(self):
        self.join()
        q=Question.objects.get(code='A01')
        choice=q.choices.index(q.accepted_patches[0])
        for line in ('','0','999','wrong'):
            self.client.post(reverse('check_line',args=[q.pk]),{'line':line})
            self.client.post(reverse('submit',args=[q.pk]),{'choice':str(choice)})
        self.assertEqual(Attempt.objects.count(),0)
        self.assertEqual(Clear.objects.count(),0)

    def test_line_check_blocks_options_until_correct(self):
        self.join()
        q=Question.objects.get(code='A01')
        correct=target_line(q)
        wrong=1 if correct!=1 else 2
        self.client.post(reverse('check_line',args=[q.pk]),{'line':str(wrong)})
        page=self.client.get(reverse('question',args=[q.pk]))
        self.assertNotContains(page,'name="choice"')
        self.assertNotContains(page,q.accepted_patches[0])
        self.client.post(reverse('check_line',args=[q.pk]),{'line':str(correct)})
        page=self.client.get(reverse('question',args=[q.pk]))
        self.assertContains(page,'name="choice"',count=4)
        self.assertEqual(Attempt.objects.count(),0)

    def test_direct_choice_post_without_verified_line_is_rejected(self):
        self.join()
        q=Question.objects.get(code='A01')
        self.client.post(reverse('submit',args=[q.pk]),{
            'choice':str(q.choices.index(q.accepted_patches[0])),
            'line':str(target_line(q)),
        })
        self.assertEqual(Attempt.objects.count(),0)
        self.assertEqual(Clear.objects.count(),0)

    def test_next_question_skips_already_cleared(self):
        self.join()
        q=Question.objects.get(code='A01')
        self.submit('A01')
        response=self.client.get(reverse('question',args=[q.pk]))
        self.assertContains(response,'다음 문제 풀기')
        next_question=response.context['next_question']
        self.assertIsNotNone(next_question)
        self.assertNotEqual(next_question.pk,q.pk)
        self.assertContains(response,reverse('question',args=[next_question.pk]))

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

    def test_hard_also_uses_only_four_choices(self):
        self.join()
        q=Question.objects.get(code='A06')
        page=self.client.get(reverse('question',args=[q.pk]))
        self.assertNotContains(page,'name="choice"')
        self.assertContains(page,'name="line"')
        self.assertNotContains(page,'id="choice-step"')
        self.client.post(reverse('check_line',args=[q.pk]),{'line':str(target_line(q))})
        page=self.client.get(reverse('question',args=[q.pk]))
        self.assertContains(page,'name="choice"',count=4)
        self.assertNotContains(page,'name="line"')
        self.assertNotContains(page,'name="patch"')
        self.assertNotContains(page,'name="counterexample"')
        self.submit('A06',patch_ok=False)
        self.assertEqual(Clear.objects.count(),0)
        self.submit('A06',patch_ok=True)
        self.assertEqual(Clear.objects.count(),1)

    def test_crafted_posted_patch_is_not_accepted(self):
        self.join()
        q=Question.objects.get(code='A01')
        self.client.post(reverse('submit',args=[q.pk]),{
            'patch':q.accepted_patches[0], 'line':str(target_line(q)),
        })
        self.assertEqual(Attempt.objects.count(),0)
        self.assertEqual(Clear.objects.count(),0)

    def test_out_of_range_choice_is_not_accepted(self):
        self.join()
        q=Question.objects.get(code='A01')
        self.client.post(reverse('check_line',args=[q.pk]),{'line':str(target_line(q))})
        self.client.post(reverse('submit',args=[q.pk]),{'choice':'99'})
        self.assertEqual(Attempt.objects.count(),0)

    def test_four_distinct_choices_each_question(self):
        for q in Question.objects.all():
            self.assertEqual(len(q.choices),4,q.code)
            self.assertEqual(len(set(q.choices)),4,q.code)
            self.assertEqual(sum(check_patch(q,target_line(q),s) for s in q.choices),1,q.code)

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
        self.assertEqual(page.count('name="choice"'),0)
        self.assertIn('name="line"',page)
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

    def test_admin_lists_and_per_hunter_histories(self):
        from django.contrib.auth import get_user_model
        from django.urls import reverse
        User=get_user_model()
        User.objects.create_superuser(username='testadmin',email='',password='strong-test-pass-12345')
        self.client.login(username='testadmin',password='strong-test-pass-12345')
        a=Player.objects.create(nickname='헌터하나')
        b=Player.objects.create(nickname='헌터둘')
        q=Question.objects.get(code='A01')
        Attempt.objects.create(player=a,question=q,selected_line=target_line(q),selected_choice=1,is_correct=False)
        Clear.objects.create(player=a,question=q,damage=20)
        index=self.client.get(reverse('admin:raid_player_changelist'))
        self.assertEqual(index.status_code,200)
        self.assertContains(index,'헌터하나')
        detail=self.client.get(reverse('admin:raid_player_change',args=[a.pk]))
        self.assertEqual(detail.status_code,200)
        self.assertContains(detail,'해결한 문제')
        self.assertContains(detail,'제출 이력')
        self.assertContains(detail,'20 HP')
        self.assertContains(detail,q.title)
        other=self.client.get(reverse('admin:raid_player_change',args=[b.pk]))
        self.assertEqual(other.status_code,200)
        self.assertNotContains(other,'20 HP')
        self.assertEqual(self.client.get(reverse('admin:raid_attempt_changelist')).status_code,200)
        self.assertEqual(self.client.get(reverse('admin:raid_clear_changelist')).status_code,200)

    @override_settings(RAID_DEMO_MODE=True)
    def test_demo_anonymous_complete_without_writing_live_records(self):
        q=Question.objects.get(code='A01')
        hp_before=RaidState.objects.get(pk=1).remaining_hp
        page=self.client.get(reverse('home'))
        self.assertContains(page,'이벤트 종료 · 체험 모드')
        self.assertNotContains(page,'name="nickname"')
        self.assertContains(page,reverse('question',args=[q.pk]))
        self.assertEqual(self.client.get(reverse('question',args=[q.pk])).status_code,200)
        self.assertNotContains(self.client.get(reverse('question',args=[q.pk])),'name="choice"')
        line=target_line(q)
        self.assertEqual(self.client.post(reverse('check_line',args=[q.pk]),{'line':str(line)}).status_code,302)
        self.assertContains(self.client.get(reverse('question',args=[q.pk])),'name="choice"',count=4)
        choice=q.choices.index(q.accepted_patches[0])
        self.client.post(reverse('submit',args=[q.pk]),{'choice':str(choice)})
        done=self.client.get(reverse('question',args=[q.pk]))
        self.assertContains(done,'체험 성공')
        self.assertContains(done,'다음 문제 풀기')
        self.assertContains(self.client.get(reverse('home')),'1 / 32')
        self.assertEqual(Player.objects.count(),0)
        self.assertEqual(Attempt.objects.count(),0)
        self.assertEqual(Clear.objects.count(),0)
        self.assertEqual(RaidState.objects.get(pk=1).remaining_hp,hp_before)

    @override_settings(RAID_DEMO_MODE=True)
    def test_demo_incorrect_line_and_forged_answer_cannot_skip_check(self):
        q=Question.objects.get(code='A01')
        choice=q.choices.index(q.accepted_patches[0])
        self.client.post(reverse('submit',args=[q.pk]),{'choice':str(choice),'line':str(target_line(q))})
        self.assertNotContains(self.client.get(reverse('question',args=[q.pk])),'name="choice"')
        wrong=1 if target_line(q)!=1 else 2
        self.client.post(reverse('check_line',args=[q.pk]),{'line':str(wrong)})
        self.assertNotContains(self.client.get(reverse('question',args=[q.pk])),'name="choice"')
        self.assertEqual(Attempt.objects.count(),0)
        self.assertEqual(Clear.objects.count(),0)

    @override_settings(RAID_DEMO_MODE=True)
    def test_demo_wrong_patch_and_reset_only_change_browser_progress(self):
        q=Question.objects.get(code='A01')
        self.client.post(reverse('check_line',args=[q.pk]),{'line':str(target_line(q))})
        wrong=next(i for i,patch in enumerate(q.choices) if patch not in q.accepted_patches)
        self.client.post(reverse('submit',args=[q.pk]),{'choice':str(wrong)})
        self.assertContains(self.client.get(reverse('question',args=[q.pk])),'현재 시도 횟수 1회')
        self.assertEqual(Clear.objects.count(),0)
        choice=q.choices.index(q.accepted_patches[0])
        self.client.post(reverse('submit',args=[q.pk]),{'choice':str(choice)})
        self.assertContains(self.client.get(reverse('home')),'1 / 32')
        self.client.post(reverse('reset_demo'))
        self.assertContains(self.client.get(reverse('home')),'0 / 32')
        self.assertNotContains(self.client.get(reverse('question',args=[q.pk])),'DEBUG COMPLETE!')
        self.assertEqual(Player.objects.count(),0)
        self.assertEqual(Attempt.objects.count(),0)
        self.assertEqual(Clear.objects.count(),0)
        self.assertEqual(RaidState.objects.get(pk=1).remaining_hp,1000)

    @override_settings(RAID_DEMO_MODE=True)
    def test_demo_join_disabled_even_with_valid_payload(self):
        self.client.post(reverse('join'),{'nickname':'공개방문자','consent':'yes'})
        self.assertEqual(Player.objects.count(),0)
        self.assertNotContains(self.client.get(reverse('home')),'name="nickname"')

    @override_settings(RAID_DEMO_MODE=True)
    def test_demo_never_mutates_existing_event_data(self):
        q=Question.objects.get(code='A01')
        previous=Player.objects.create(nickname='행사참가자')
        Attempt.objects.create(player=previous,question=q,is_correct=False)
        Clear.objects.create(player=previous,question=q,damage=20)
        RaidState.objects.filter(pk=1).update(remaining_hp=0)
        self.client.post(reverse('check_line',args=[q.pk]),{'line':str(target_line(q))})
        self.client.post(reverse('submit',args=[q.pk]),{'choice':str(q.choices.index(q.accepted_patches[0]))})
        self.client.post(reverse('reset_demo'))
        self.client.post(reverse('join'),{'nickname':'신규헌터','consent':'yes'})
        self.assertEqual(Player.objects.count(),1)
        self.assertEqual(Attempt.objects.count(),1)
        self.assertEqual(Clear.objects.count(),1)
        self.assertEqual(RaidState.objects.get(pk=1).remaining_hp,0)
