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
from .demo import demo_state, save_demo_state, clear_demo_state, MAX_ATTEMPTS

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

def demo_cleared_ids(request):
    """Anonymous demo progression in this browser only; no live raid tables change."""
    return set(demo_state(request)['c'])

def demo_next_question(request, current_question):
    questions = list(Question.objects.filter(is_active=True).order_by('difficulty', 'code'))
    cleared = demo_cleared_ids(request)
    if not questions:
        return None
    index = next((i for i, question in enumerate(questions) if question.pk == current_question.pk), -1)
    return next((question for question in (questions[index + 1:] + questions[:index + 1])
                 if question.pk not in cleared), None)

def demo_attempts(request, pk):
    return demo_state(request)['a'].get(str(pk), 0)

def home(request):
    demo_mode=settings.RAID_DEMO_MODE
    player=None if demo_mode else current_player(request)
    state=ensure_state()
    cleared_ids=(demo_cleared_ids(request) if demo_mode else
                 (set(Clear.objects.filter(player=player).values_list('question_id',flat=True)) if player else set()))
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
        'demo_mode':demo_mode,
        'invite_required':bool(settings.RAID_INVITE_CODE),
        'total_progress':round((state.max_hp-state.remaining_hp)/state.max_hp*100),
        'members':members,'cleared_total':cleared_total,
        'personal_clears':len(cleared_ids) if demo_mode else (Clear.objects.filter(player=player).count() if player else 0),
        'max_rewarded':settings.RAID_MAX_CLEARS_PER_PLAYER,
        'total_questions':len(questions),
    })

@require_POST
def join(request):
    if settings.RAID_DEMO_MODE:
        messages.info(request,'이벤트가 종료되어 신규 헌터 등록은 중단됐어. 로그인 없이 미션을 체험해 봐!')
        return redirect('home')
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

def line_verification_key(pk):
    return f'bug_line_verified_{pk}'

def next_unsolved_question(player,current_question):
    questions=list(Question.objects.filter(is_active=True).order_by('difficulty','code'))
    solved=set(Clear.objects.filter(player=player).values_list('question_id',flat=True))
    if not questions:
        return None
    position=next((i for i,q in enumerate(questions) if q.pk==current_question.pk),-1)
    ordered=questions[position+1:]+questions[:position+1]
    return next((q for q in ordered if q.pk not in solved),None)

def question_detail(request,pk):
    question=get_object_or_404(Question,pk=pk,is_active=True)
    demo_mode=settings.RAID_DEMO_MODE
    player=None if demo_mode else current_player(request)
    if not demo_mode and not player:
        messages.info(request,'먼저 닉네임을 등록해 줘!')
        return redirect('home')
    clear=({'damage':0} if pk in demo_cleared_ids(request) else None) if demo_mode else Clear.objects.filter(question=question,player=player).first()
    attempts=demo_attempts(request,pk) if demo_mode else Attempt.objects.filter(question=question,player=player).count()
    state=ensure_state()
    code_lines=[]
    correct_line=target_line(question)
    line_verified=(pk in demo_state(request)['v']) if demo_mode else (
        request.session.get(line_verification_key(pk))==correct_line)
    for num, content in enumerate(question.buggy_code.splitlines(),start=1):
        code_lines.append({'num':num,'content':content})
    return render(request,'raid/question.html',{
        'question':question,'player':player,'clear':clear,'attempts':attempts,'state':state,
        'demo_mode':demo_mode,
        'code_lines':code_lines,'correct_line':correct_line if clear or line_verified else None,
        'line_verified':line_verified,
        'next_question':(demo_next_question(request,question) if demo_mode else next_unsolved_question(player,question)) if clear else None,
        'choices':list(enumerate(question.choices)) if line_verified else [],
        'category_name':question.get_category_display(),
    })

@require_POST
def check_line(request,pk):
    question=get_object_or_404(Question,pk=pk,is_active=True)
    demo_mode=settings.RAID_DEMO_MODE
    player=None if demo_mode else current_player(request)
    if not demo_mode and not player:
        messages.info(request,'먼저 닉네임을 등록해 줘!')
        return redirect('home')
    if (pk in demo_cleared_ids(request)) if demo_mode else Clear.objects.filter(player=player,question=question).exists():
        return redirect('question',pk=pk)
    key=line_verification_key(pk)
    raw=(request.POST.get('line') or '').strip()
    matched=raw.isdigit() and int(raw)==target_line(question)
    if demo_mode:
        state=demo_state(request)
        verified=set(state['v'])
        if matched:
            verified.add(pk)
        else:
            verified.discard(pk)
        state['v']=sorted(verified)
    elif matched:
        request.session[key]=target_line(question)
    else:
        request.session.pop(key,None)
    if matched:
        messages.success(request,'버그 위치 발견! 이제 올바른 수정 코드를 선택해 줘.')
    else:
        messages.error(request,'그 줄은 버그 위치가 아니야. 코드를 다시 읽고 다른 줄을 선택해 봐.')
    response=redirect('question',pk=pk)
    return save_demo_state(response,request) if demo_mode else response

@require_POST
def submit_answer(request,pk):
    question=get_object_or_404(Question,pk=pk,is_active=True)
    demo_mode=settings.RAID_DEMO_MODE
    player=None if demo_mode else current_player(request)
    if not demo_mode and not player:
        return redirect('home')
    if (pk in demo_cleared_ids(request)) if demo_mode else Clear.objects.filter(player=player,question=question).exists():
        messages.info(request,'이미 해결했어! 다른 미션에도 도전해 봐.')
        return redirect('question',pk=pk)
    correct_line=target_line(question)
    key=line_verification_key(pk)
    if (pk not in demo_state(request)['v']) if demo_mode else request.session.get(key)!=correct_line:
        messages.error(request,'먼저 잘못된 코드 줄을 정확히 찾아야 수정안을 제출할 수 있어.')
        return redirect('question',pk=pk)
    raw_choice=(request.POST.get('choice') or '').strip()
    if not raw_choice.isdigit() or len(question.choices)!=4:
        messages.error(request,'4개 보기 중 하나를 선택해 줘.')
        return redirect('question',pk=pk)
    selected_choice=int(raw_choice)
    if not 0<=selected_choice<4:
        messages.error(request,'4개 보기 중 하나를 선택해 줘.')
        return redirect('question',pk=pk)
    # Step 1 was verified on the server; clients cannot skip it by forging POST data.
    line=correct_line
    patch=question.choices[selected_choice]
    patch_ok=check_patch(question,line,patch)
    case_ok=True
    is_correct=patch_ok
    if demo_mode:
        # Only an authenticated signature-bound practice cookie is updated.
        # Player, Attempt, Clear and RaidState remain untouched.
        state=demo_state(request)
        state['a'][str(pk)] = min(state['a'].get(str(pk), 0) + 1, MAX_ATTEMPTS)
        if is_correct:
            state['v'] = [qid for qid in state['v'] if qid != pk]
            state['c'] = sorted(set(state['c']) | {pk})
            messages.success(request,'체험 미션 성공! 실제 행사 보스 HP와 기록은 변경되지 않아. 🎉')
        else:
            messages.error(request,'수정안이 정답이 아니야. 다른 코드를 골라 봐!')
        return save_demo_state(redirect('question',pk=pk),request)
    # Row lock and all writes inside one transaction (PostgreSQL recommended in deployment).
    ensure_state()
    with transaction.atomic():
        state=RaidState.objects.select_for_update().get(pk=1)
        if Clear.objects.filter(player=player,question=question).exists():
            return redirect('question',pk=pk)
        Attempt.objects.create(
            player=player,question=question,selected_line=line,patch_text=patch,
            selected_case=None,selected_choice=selected_choice,
            patch_correct=patch_ok,case_correct=case_ok,
            hint_used=request.POST.get('hint_used')=='1',is_correct=is_correct,
        )
        if is_correct:
            request.session.pop(key,None)
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
            messages.error(request,'수정안이 정답이 아니야. 버그 위치는 맞았으니 다른 코드를 골라 봐!')
    return redirect('question',pk=pk)

@require_POST
def reset_demo(request):
    if not settings.RAID_DEMO_MODE:
        return redirect('home')
    messages.success(request, '체험 진행 상황만 초기화했어. 실제 행사 기록은 그대로야!')
    return clear_demo_state(redirect('home'))

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
    writer.writerow(['범주','개념','닉네임','문제 코드','난이도','첫 제출 정답','선택한 보기(0~3)','힌트 사용','제출 시각'])
    seen=set()
    for a in Attempt.objects.select_related('player','question').order_by('id'):
        key=(a.player_id,a.question_id)
        if key in seen: continue
        seen.add(key)
        writer.writerow([a.question.get_category_display(),a.question.concept,a.player.nickname,
                         a.question.code,a.question.difficulty,int(a.is_correct),
                         a.selected_choice if a.selected_choice is not None else '',
                         int(a.hint_used),a.created_at.isoformat()])
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
