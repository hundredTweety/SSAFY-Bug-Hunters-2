import csv
import json
import uuid
import secrets
from django.conf import settings
from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.db import transaction, connection
from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST
from .models import Player, Question, RaidState, Attempt, Clear
from .logic import check_patch, target_line
from .stats import confusion_stats

CATEGORY_META = [
    {'code':'array','name':'배열·문자열','icon':'🔤','desc':'인덱스, 문자열, 슬라이딩 윈도우','tone':'violet'},
    {'code':'grid','name':'2차원·시뮬레이션','icon':'🗺️','desc':'델타, 섬 탐색, 행렬, 경로 DP','tone':'cyan'},
    {'code':'search','name':'탐색·자료구조','icon':'🧠','desc':'스택, BFS·DFS, 그래프, 부분집합','tone':'amber'},
    {'code':'strategy','name':'그리디·DP','icon':'⚙️','desc':'정렬, 그리디, 이분탐색, 배낭','tone':'rose'},
]

def ensure_state():
    state, _=RaidState.objects.get_or_create(pk=1, defaults={
        'max_hp':settings.RAID_MAX_HP, 'remaining_hp':settings.RAID_MAX_HP,
        'damage_per_clear':settings.RAID_DAMAGE,
    })
    return state

def current_player(request):
    player_id=request.session.get('player_id')
    if not player_id:
        return None
    try:
        return Player.objects.filter(pk=uuid.UUID(str(player_id))).first()
    except (ValueError,TypeError,AttributeError):
        return None

def home(request):
    player=current_player(request)
    state=ensure_state()
    cleared_ids=set(Clear.objects.filter(player=player).values_list('question_id',flat=True)) if player else set()
    questions=list(Question.objects.filter(is_active=True).order_by('difficulty','code'))
    categories=[]
    for meta in CATEGORY_META:
        group=[q for q in questions if q.category==meta['code']]
        categories.append({**meta,'questions':group,'count':len(group),
                           'cleared':sum(q.id in cleared_ids for q in group)})
    cleared_total=Clear.objects.filter(damage__gt=0).count()
    members=Clear.objects.filter(damage__gt=0).values('player_id').distinct().count()
    return render(request,'raid/home.html',{
        'player':player,'state':state,'categories':categories,'cleared_ids':cleared_ids,
        'invite_required':bool(settings.RAID_INVITE_CODE),
        'total_progress':round((state.max_hp-state.remaining_hp)/state.max_hp*100),
        'members':members,'cleared_total':cleared_total,
        'personal_clears':Clear.objects.filter(player=player).count() if player else 0,
        'max_rewarded':settings.RAID_MAX_CLEARS_PER_PLAYER,
        'total_questions':len(questions),
    })

@require_POST
def join(request):
    if current_player(request):
        return redirect('home')
    nickname=(request.POST.get('nickname') or '').strip()
    if not 2<=len(nickname)<=12 or any(ord(x)<32 for x in nickname):
        messages.error(request,'닉네임은 2~12자로 입력해 주세요.')
        return redirect('home')
    if settings.RAID_INVITE_CODE and not secrets.compare_digest(
        (request.POST.get('invite_code') or '').strip(), settings.RAID_INVITE_CODE
    ):
        messages.error(request,'반 참여 코드를 확인해 줘.')
        return redirect('home')
    if request.POST.get('consent')!='yes':
        messages.error(request,'기록 저장 안내를 확인하고 동의해 주세요.')
        return redirect('home')
    player=Player.objects.create(nickname=nickname)
    request.session['player_id']=str(player.pk)
    request.session.set_expiry(60*60*24*60)
    messages.success(request,f'{nickname} 헌터, 임무 준비 완료!')
    return redirect('home')

def question_detail(request,pk):
    question=get_object_or_404(Question,pk=pk,is_active=True)
    player=current_player(request)
    if not player:
        messages.info(request,'먼저 닉네임을 등록해 줘!')
        return redirect('home')
    clear=Clear.objects.filter(question=question,player=player).first()
    attempts=Attempt.objects.filter(question=question,player=player).count()
    state=ensure_state()
    code_lines=[]
    correct_line=target_line(question)
    for num, content in enumerate(question.buggy_code.splitlines(),start=1):
        code_lines.append({'num':num,'content':content})
    cases=[{'num':i,'label':chr(65+i),'data':json.dumps(c['input'],ensure_ascii=False),
            'expected':json.dumps(c['expected'],ensure_ascii=False)}
           for i,c in enumerate(question.case_options)]
    return render(request,'raid/question.html',{
        'question':question,'player':player,'clear':clear,'attempts':attempts,'state':state,
        'code_lines':code_lines,'cases':cases,
        'show_case':question.difficulty>=2,'correct_line':correct_line if clear else None,
        'category_name':question.get_category_display(),
    })

@require_POST
def submit_answer(request,pk):
    question=get_object_or_404(Question,pk=pk,is_active=True)
    player=current_player(request)
    if not player:
        return redirect('home')
    if Clear.objects.filter(player=player,question=question).exists():
        messages.info(request,'이미 해결했어! 다른 미션에도 도전해 봐.')
        return redirect('question',pk=pk)
    patch=(request.POST.get('patch') or '').strip()
    raw_line=request.POST.get('line','')
    if not raw_line.isdigit() or len(patch)>300 or not patch or '\n' in patch or '\r' in patch:
        messages.error(request,'수정할 줄을 선택하고, 교체할 코드 한 줄을 입력해 줘.')
        return redirect('question',pk=pk)
    line=int(raw_line)
    raw_case=request.POST.get('counterexample','')
    selected_case=int(raw_case) if raw_case.isdigit() else None
    if question.difficulty>=2 and (selected_case is None or not 0<=selected_case<len(question.case_options)):
        messages.error(request,'오류가 발생하는 입력도 하나 선택해 줘.')
        return redirect('question',pk=pk)
    patch_ok=check_patch(question,line,patch)
    case_ok=(question.difficulty==1 or selected_case==question.counterexample_index)
    is_correct=patch_ok and case_ok
    # Row lock and all writes inside one transaction (PostgreSQL recommended in deployment).
    ensure_state()
    with transaction.atomic():
        state=RaidState.objects.select_for_update().get(pk=1)
        if Clear.objects.filter(player=player,question=question).exists():
            return redirect('question',pk=pk)
        Attempt.objects.create(
            player=player,question=question,selected_line=line,patch_text=patch,
            selected_case=selected_case,patch_correct=patch_ok,case_correct=case_ok,
            hint_used=request.POST.get('hint_used')=='1',is_correct=is_correct,
        )
        if is_correct:
            prior=Clear.objects.filter(player=player,damage__gt=0).count()
            amount=min(state.remaining_hp,state.damage_per_clear) if (state.remaining_hp>0 and prior<settings.RAID_MAX_CLEARS_PER_PLAYER) else 0
            Clear.objects.create(player=player,question=question,damage=amount)
            if amount:
                state.remaining_hp-=amount
                state.save(update_fields=['remaining_hp'])
                messages.success(request,f'버그 수정 성공! 공동 보스에게 {amount} 데미지! 💥')
            else:
                messages.success(request,'버그 수정 성공! 추가 공격 횟수와 무관하게 학습 기록은 남았어.')
        else:
            if not patch_ok:
                messages.error(request,'아직 버그가 남아 있어. 수정할 줄과 코드를 다시 점검해 봐.')
            else:
                messages.error(request,'수정 코드는 맞았어! 어떤 입력에서 원본 코드가 실패하는지 다시 생각해 봐.')
    return redirect('question',pk=pk)

def results(request):
    state=ensure_state()
    if state.remaining_hp>0 and not settings.RAID_RESULTS_PUBLIC and not request.user.is_staff:
        return render(request,'raid/results_locked.html',{'state':state,'player':current_player(request)})
    top5,reliable=confusion_stats(minimum_players=3)
    groups=[]
    for meta in CATEGORY_META:
        rows,_=confusion_stats(category=meta['code'],minimum_players=3)
        groups.append({**meta,'rows':rows[:3]})
    return render(request,'raid/results.html',{
        'state':state,'player':current_player(request),'top5':top5,'reliable':reliable,
        'categories':groups,'players':Player.objects.count(),
        'attempt_count':Attempt.objects.count(),'clears':Clear.objects.count(),
    })

@staff_member_required
@require_POST
def export_results(request):
    response=HttpResponse(content_type='text/csv; charset=utf-8-sig')
    response['Content-Disposition']='attachment; filename="bughunters_first_attempts.csv"'
    response.write('\ufeff')
    writer=csv.writer(response)
    writer.writerow(['범주','개념','닉네임','문제 코드','난이도','첫 제출 정답','패치 정확','반례 정확','힌트 사용','제출 시각'])
    seen=set()
    for a in Attempt.objects.select_related('player','question').order_by('id'):
        key=(a.player_id,a.question_id)
        if key in seen: continue
        seen.add(key)
        writer.writerow([a.question.get_category_display(),a.question.concept,a.player.nickname,
                         a.question.code,a.question.difficulty,int(a.is_correct),
                         int(a.patch_correct),int(a.case_correct),int(a.hint_used),a.created_at.isoformat()])
    return response

def api_status(request):
    state=ensure_state()
    return JsonResponse({'hp':state.remaining_hp,'max_hp':state.max_hp,
        'progress':round((state.max_hp-state.remaining_hp)/state.max_hp*100),
        'finished':state.remaining_hp==0})


def healthcheck(request):
    """Readiness probe: app + primary DB connection. No private data returned."""
    try:
        with connection.cursor() as cursor:
            cursor.execute('SELECT 1')
            cursor.fetchone()
    except Exception:
        return HttpResponse('unavailable', status=503, content_type='text/plain')
    return HttpResponse('ok', content_type='text/plain')
