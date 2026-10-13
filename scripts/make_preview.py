"""Build a full offline 24-mission demo. Do not deploy HTML to a public class: solutions are embedded."""
import json,base64
from pathlib import Path
root=Path(__file__).resolve().parents[1]
bank=json.loads((root/'raid/question_bank.json').read_text(encoding='utf8'))
css=(root/'raid/static/raid/site.css').read_text(encoding='utf8')
svg=base64.b64encode((root/'raid/static/raid/boss.svg').read_bytes()).decode('ascii')
question_json=json.dumps(bank,ensure_ascii=False).replace('</','<\\/')
page=r'''<!doctype html><html lang="ko"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>BUG HUNTERS 2.0 | 체험판</title>
<style>__CSS__
.preview-badge{display:inline-block;background:#273c3a;color:#b6fae9;border:1px solid #4b9c8c;border-radius:30px;font-size:11px;padding:5px 10px}.preview-header{background:#172c31;border-bottom:1px solid #2d695d;padding:8px 18px;text-align:center;color:#baf4d6;font-size:12px}.mini-hero{max-width:1150px;margin:35px auto 24px;padding:32px;display:grid;grid-template-columns:1fr 260px;align-items:center;gap:20px;background:radial-gradient(ellipse at right,#27535e,transparent 70%),#151e34;border-radius:24px;border:1px solid #365263}.mini-hero h1{font-size:clamp(34px,4.2vw,57px);line-height:1.25;margin:8px 0 13px;letter-spacing:-2px}.mini-hero p{color:#c3d6e5;margin:0 0 20px}.demo-boss{text-align:center}.demo-boss img{width:210px;max-width:100%;height:190px;object-fit:contain;filter:drop-shadow(0 10px 20px #030915)}.demo-hp{height:13px;background:#344059;border-radius:50px;overflow:hidden;margin-top:10px}.demo-hp div{height:100%;width:100%;background:linear-gradient(90deg,#ff789a,#ffc38a);border-radius:50px;transition:width .3s}.demo-stats{display:flex;gap:13px;margin-top:10px;flex-wrap:wrap;color:#aebbd7;font-size:12px}.demo-stats b{color:#ecfff8}.preview-main{padding-bottom:50px}.preview-title{display:flex;justify-content:space-between;align-items:center;margin-bottom:12px;gap:15px}.preview-title h2{font-size:27px;margin:5px 0}.preview-title p{font-size:12px;color:#aab7d2;margin:0}.preview-categories{display:grid;grid-template-columns:repeat(4,1fr);gap:11px;margin:18px 0}.preview-cat{padding:17px 14px;border-radius:14px;border:1px solid #394763;background:#1c273f;color:#e7ecfc;text-align:left;min-height:113px;display:flex;flex-direction:column;gap:5px}.preview-cat.active{background:#25423f;border:2px solid #8adfc1;padding:16px 13px}.preview-cat strong{font-size:14px}.preview-cat small{font-size:10px;color:#aabacd}.preview-cat .emo{font-size:23px}.preview-list{display:grid;grid-template-columns:repeat(2,1fr);gap:11px}.preview-mission{border:1px solid #3b4b65;background:#1a263e;border-radius:13px;padding:16px;text-align:left;display:flex;gap:15px;align-items:center;color:#edf1fc}.preview-mission:hover{border-color:#84e4bc;background:#23384b}.preview-mission.done{border-color:#5eac8e;background:#1d3637}.preview-mission b{font-size:13px}.preview-mission small{display:block;font-size:11px;color:#9caeca}.preview-mission .no{color:#8badd7;font-size:15px;font-weight:900}.preview-mission .arrow{margin-left:auto;font-size:11px;color:#b6f4d8;white-space:nowrap}.preview-modal{position:fixed;inset:0;background:#01040bd6;z-index:100;display:none;overflow-y:auto;padding:35px 15px}.preview-modal.show{display:block}.preview-dialog{max-width:890px;margin:auto;background:#182239;border:1px solid #53627c;border-radius:18px;overflow:hidden;box-shadow:0 35px 80px #0009}.preview-dialog-head{display:flex;align-items:center;justify-content:space-between;gap:9px;padding:18px 25px;border-bottom:1px solid #3a4760}.preview-dialog-head h2{margin:3px 0;font-size:24px}.close-btn{font-size:26px;color:#fff;border:0;background:transparent}.preview-content{padding:20px 25px 30px}.preview-description{color:#bfd0e7;font-size:13px}.preview-code{background:#0b1425;border:1px solid #324260;border-radius:13px;padding:9px 0;overflow-x:auto;max-height:450px;overflow-y:auto}.preview-code label{display:flex;min-width:max-content;white-space:pre;align-items:start;font:12px/1.75 ui-monospace,Consolas,monospace;padding:2px 16px;cursor:pointer;border-left:3px solid transparent}.preview-code label:hover{background:#233950}.preview-code label:has(input:checked){border-left-color:#75ecc5;background:#254339}.preview-code input{margin:5px 13px 0 0;accent-color:#83f3ca}.preview-code .num{color:#7284a5;padding-right:15px;margin-right:15px;border-right:1px solid #2d3952}.preview-code code{white-space:pre;font-family:inherit}.preview-content textarea{width:100%;background:#0b1726;border:1px solid #53627b;border-radius:9px;padding:14px;color:#d7ffec;font:13px/1.4 ui-monospace,Consolas,monospace;resize:vertical;min-height:74px}.preview-form-block{margin-top:22px}.preview-form-block h3{font-size:17px;margin:0 0 8px}.preview-form-block p{font-size:12px;color:#aebbd0}.preview-case{display:flex;gap:11px;align-items:center;border:1px solid #425273;background:#1e2c47;padding:13px 15px;border-radius:10px;margin-bottom:8px;cursor:pointer}.preview-case:has(input:checked){border-color:#79dec0;background:#254341}.preview-case input{accent-color:#7be5ba}.preview-case code{display:block;font:12px/1.5 ui-monospace,Consolas,monospace;overflow-wrap:anywhere;white-space:pre-wrap;color:#f0f7ff}.preview-case small{font-size:11px;color:#a8bad5}.preview-submit{display:flex;justify-content:space-between;align-items:center;gap:12px;margin-top:20px;flex-wrap:wrap}.preview-message{background:#463143;border:1px solid #a76a8a;border-radius:10px;color:#ffe0ea;padding:12px 15px;margin-top:15px;font-size:13px}.preview-message.ok{background:#23423d;border-color:#57a484;color:#d6ffef}.preview-note{font-size:12px;color:#a5b3cc}.sample-panel{border:1px solid #435372;border-radius:17px;background:#19243d;padding:25px;margin-top:28px}.sample-panel h2{font-size:21px;margin:5px 0}.sample-panel p{color:#aab8d3;font-size:12px}.sample-row{padding:12px;border-bottom:1px solid #394967;display:flex;justify-content:space-between}.btn-text{padding:9px 13px;color:#ccfff2;background:#233d3d;border:1px solid #487c71;border-radius:9px;font-size:12px}.preview-action{background:#80e8c4;color:#0a2226;border:0;border-radius:9px;padding:12px 20px;font-weight:900}.preview-action:hover{background:#adffe0}.preview-action:disabled{opacity:.45}.hidden{display:none!important}
@media(max-width:800px){.mini-hero{grid-template-columns:1fr 160px;padding:24px}.demo-boss img{width:150px}.preview-categories{grid-template-columns:repeat(2,1fr)}}@media(max-width:580px){.mini-hero{display:flex;flex-direction:column-reverse;margin-top:16px;padding:19px}.mini-hero h1{font-size:31px}.demo-boss img{width:130px;height:120px}.preview-list{grid-template-columns:1fr}.preview-dialog-head{padding:12px 16px}.preview-content{padding:14px 15px}.preview-code label{font-size:11px}.preview-categories{gap:7px}.preview-cat{min-height:105px;padding:12px}.preview-title h2{font-size:22px}}
</style></head>
<body><div class="preview-header">🧪 설치 없는 로컬 체험판 · 공유 HP/반 전체 통계 연동 없음 · 정답은 이 파일에 포함됨</div>
<header class="global-header"><div class="container header-inner"><span class="brand"><span class="brand-mark">🐛</span> BUG <em>HUNTERS</em> <small>2.0</small></span><nav class="main-nav"><a href="#missions">미션 선택</a><a href="#report">학습 리포트 예시</a></nav></div></header>
<main class="container preview-main">
<section class="mini-hero"><div><span class="eyebrow">SSAFY 1반 · IM DEBUGGING RAID</span><h1>버그는 각자 잡고,<br><span class="gradient-text">보스는 함께 잡자.</span></h1><p>24개의 진짜 디버깅 미션. 코드 한 줄을 직접 고치고, 오류가 발생하는 반례도 골라보자.</p><span class="preview-badge">✅ 실전 미션 24개</span> <span class="preview-badge">⚡ 1인 최대 3회 공격</span></div><div class="demo-boss"><img src="data:image/svg+xml;base64,__SVG__" alt="버그로드"><b style="display:block">👾 LV.99 버그로드</b></div></section>
<div class="boss-hp-panel"><div class="hp-heading"><span>❤️ BOSS HP <small style="color:#a2b5c5">(체험판의 개인 공격만 반영)</small></span><strong><span id="hp">1000</span> / 1000</strong></div><div class="demo-hp"><div id="hpbar"></div></div><div class="demo-stats"><span>나의 해결 <b id="clears">0</b>개</span><span>공격 기여 <b id="hits">0</b> / 3회</span><span>미션 <b>24</b>개</span></div></div>
<section id="missions" style="margin-top:35px"><div class="preview-title"><div><span class="eyebrow">CHOOSE YOUR MISSION</span><h2>어떤 버그부터 잡을래?</h2><p>난이도와 분야를 선택해 미션에 도전해 봐.</p></div><span class="preview-badge">24 MISSIONS</span></div>
<div id="levels" class="filter-row"></div><div id="cats" class="preview-categories"></div><div id="missions-list" class="preview-list"></div></section>
<section id="report" class="sample-panel"><span class="eyebrow">REPORT PREVIEW</span><h2>우리 반의 취약 개념 TOP 5</h2><p>실제 Django 서버 배포 후에는 사람별·문제별 첫 제출만 집계하고, 개념별 참여자 3명 이상일 때 순위에 포함돼. 아래는 화면 설명을 위한 <b>가상 데이터</b>야.</p><div id="sample-report"></div></section>
<p class="preview-note" style="margin:22px 0 8px">* 이 체험판에서는 혼자 푼 결과만 브라우저에 저장돼. 25명이 공유하는 보스 HP와 실제 분석 결과는 Django 앱 배포 후에만 동작해.</p></main>
<div class="preview-modal" id="modal" role="dialog" aria-modal="true" aria-labelledby="modal-title"><div class="preview-dialog"><div class="preview-dialog-head"><div><span class="eyebrow" id="modal-meta"></span><h2 id="modal-title"></h2></div><button class="close-btn" type="button" id="close" aria-label="닫기">×</button></div><div class="preview-content"><p id="mission-desc" class="preview-description"></p><div class="preview-code" id="code"></div><p class="preview-note">↑ 버그가 있는 코드 줄의 동그라미를 선택해 줘.</p><div id="input-steps"></div><div class="preview-submit"><button id="hint" type="button" class="btn-text">💡 힌트</button><button id="submit" type="button" class="preview-action">🐛 버그 수정하고 공격 →</button></div><div id="feedback" aria-live="polite"></div></div></div></div>
<script>const BANK=__BANK__;
const META=[['array','🔤','배열·문자열','문자열, 인덱스, 누적합'],['grid','🗺️','2차원·시뮬레이션','델타, 행렬, 섬 탐색'],['search','🧠','탐색·자료구조','스택, BFS·DFS'],['strategy','⚙️','그리디·DP','최적화, 정렬, DP']];
const names={1:'EASY',2:'NORMAL',3:'HARD'};
let demo=JSON.parse(localStorage.getItem('bh2_preview')||'{"cleared":{},"first":{},"att":{}}');
let category='array',level='all',active=null;
function escapeHtml(value){return String(value).replace(/[&<>\"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','\"':'&quot;',"'":'&#39;'}[c]));}
function getQuestion(code){return BANK.find(q=>q.code===code)}
function save(){localStorage.setItem('bh2_preview',JSON.stringify(demo));}
function norm(str){return (str||'').trim().replace(/\s+/g,'');}
function renderHome(){
 document.getElementById('levels').innerHTML=[['all','전체'],['1','🟢 EASY'],['2','🟡 NORMAL'],['3','🔴 HARD']].map(([v,label])=>`<button class="filter-pill ${level===v?'active':''}" data-lev="${v}">${label}</button>`).join('');
 document.querySelectorAll('[data-lev]').forEach(b=>b.onclick=()=>{level=b.dataset.lev;renderHome();});
 document.getElementById('cats').innerHTML=META.map(([id,icon,label,desc])=>`<button class="preview-cat ${id===category?'active':''}" data-cat="${id}"><span class="emo">${icon}</span><strong>${label}</strong><small>${desc}</small></button>`).join('');
 document.querySelectorAll('[data-cat]').forEach(b=>b.onclick=()=>{category=b.dataset.cat;renderHome()});
 let qs=BANK.filter(q=>q.category===category&&(level==='all'||q.difficulty===Number(level)));
 document.getElementById('missions-list').innerHTML=qs.length?qs.map(q=>`<button class="preview-mission ${demo.cleared[q.code]?'done':''}" data-open="${q.code}"><span class="no">${q.code}</span><span><b>${escapeHtml(q.title)}</b><small>${escapeHtml(q.concept)} · ${names[q.difficulty]}</small></span><span class="arrow">${demo.cleared[q.code]?'✓ 해결':'→ 도전'}</span></button>`).join(''):'<p class="preview-note">이 영역에는 해당 난이도의 미션이 없어.</p>';
 document.querySelectorAll('[data-open]').forEach(b=>b.onclick=()=>openQ(b.dataset.open));
 const solved=Object.values(demo.cleared).filter(Boolean).length;
 const hits=Math.min(solved,3);
 document.getElementById('clears').textContent=solved;
 document.getElementById('hits').textContent=hits;
 document.getElementById('hp').textContent=1000-20*hits;
 document.getElementById('hpbar').style.width=(100-2*hits)+'%';
}
function openQ(code){
 active=getQuestion(code);const q=active;
 document.getElementById('modal-meta').textContent=`MISSION ${q.code} · ${names[q.difficulty]} · ${q.concept}`;
 document.getElementById('modal-title').textContent=q.title;
 document.getElementById('mission-desc').textContent=q.body;
 document.getElementById('code').innerHTML=q.buggy_code.split('\n').map((line,i)=>`<label><input name="line-pick" type="radio" value="${i+1}" ${demo.cleared[q.code]?'disabled':''}><span class="num">${String(i+1).padStart(2,'0')}</span><code>${escapeHtml(line)}</code></label>`).join('');
 const solved=demo.cleared[q.code];
 document.getElementById('input-steps').innerHTML=solved?`<div class="preview-message ok"><b>🏅 이미 해결한 버그야!</b><p>정답 수정 코드: <code>${escapeHtml(q.accepted_patches[0])}</code></p><p>${escapeHtml(q.explanation)}</p></div>`:`<div class="preview-form-block"><h3>STEP 1 · 수정 코드 한 줄</h3><p>잘못된 줄을 위에서 선택하고, 교체할 코드를 직접 작성해.</p><textarea id="patch" spellcheck="false" placeholder="예: if 0 <= nr < n and 0 <= nc < m:"></textarea></div>`+(q.difficulty>=2?`<div class="preview-form-block"><h3>STEP 2 · 실패하는 입력 찾기</h3><p>아래 세 가지 중 버그가 드러나는 입력은 하나뿐이야.</p>${q.case_options.map((c,i)=>`<label class="preview-case"><input type="radio" name="case-pick" value="${i}"><span><b>${'ABC'[i]}. 입력</b><code>${escapeHtml(JSON.stringify(c.input))}</code><small>기대 결과: ${escapeHtml(JSON.stringify(c.expected))}</small></span></label>`).join('')}</div>`:'');
 document.getElementById('feedback').innerHTML='';
 document.getElementById('submit').disabled=!!solved;
 document.getElementById('hint').disabled=!!solved;
 document.getElementById('modal').classList.add('show');document.body.style.overflow='hidden';
}
function closeQ(){document.getElementById('modal').classList.remove('show');document.body.style.overflow='';active=null;renderHome();}
document.getElementById('close').onclick=closeQ;
document.getElementById('modal').addEventListener('click',e=>{if(e.target.id==='modal')closeQ()});
document.addEventListener('keydown',e=>{if(e.key==='Escape'&&active)closeQ()});
document.getElementById('hint').onclick=()=>{if(!active)return;document.getElementById('feedback').innerHTML=`<div class="preview-message">💡 ${escapeHtml(active.hint)}</div>`};
document.getElementById('submit').onclick=()=>{
 if(!active||demo.cleared[active.code])return;
 const picked=document.querySelector('[name="line-pick"]:checked');const patch=document.getElementById('patch')?.value||'';
 const selected=document.querySelector('[name="case-pick"]:checked');
 if(!picked||!patch.trim()||(active.difficulty>=2&&!selected)){document.getElementById('feedback').innerHTML='<div class="preview-message">수정할 줄, 코드, 필요한 경우 반례까지 선택해 줘.</div>';return;}
 const correctLine=active.buggy_code.split('\n').findIndex(s=>s.trim()===active.original_line)+1;
 const patchOkay=Number(picked.value)===correctLine&&active.accepted_patches.some(s=>norm(s)===norm(patch));
 const caseOkay=active.difficulty===1||Number(selected.value)===active.counterexample_index;
 if(!demo.first[active.code])demo.first[active.code]={correct:patchOkay&&caseOkay,patch:patchOkay,counterexample:caseOkay};
 demo.att[active.code]=(demo.att[active.code]||0)+1;
 if(patchOkay&&caseOkay){const canDamage=Object.values(demo.cleared).filter(Boolean).length<3;demo.cleared[active.code]=true;save();document.getElementById('feedback').innerHTML=`<div class="preview-message ok"><b>💥 DEBUG COMPLETE!</b><p>${canDamage?'보스 HP -20!':'개인 공격 3회를 다 썼지만 풀이 기록은 남았어.'}</p><p>수정: <code>${escapeHtml(active.accepted_patches[0])}</code></p><p>${escapeHtml(active.explanation)}</p><button id="close-answer" class="btn-text">다른 미션 고르기 →</button></div>`;document.getElementById('submit').disabled=true;document.getElementById('close-answer').onclick=closeQ;
 }else{save();document.getElementById('feedback').innerHTML=`<div class="preview-message">${!patchOkay?'아직 수정할 코드 줄이나 내용이 틀렸어. 다시 살펴봐.':'코드 수정은 맞았어! 오류가 발생하는 입력을 다시 골라봐.'}</div>`;}
};
const fake=[['방문 처리',72],['인덱스·경계',65],['DP 상태 전이',54],['정렬·그리디 판단',43],['상태 초기화',31]];
document.getElementById('sample-report').innerHTML=fake.map(([name,rate],i)=>`<div class="sample-row"><span><b>${i+1}.</b> ${name}</span><strong>${rate}%</strong></div>`).join('');
renderHome();
</script></body></html>'''
page=page.replace('__CSS__',css).replace('__SVG__',svg).replace('__BANK__',question_json)
dst=root/'BUG_HUNTERS_2_체험판.html'
dst.write_text(page,encoding='utf8')
print('built',dst,len(page),'bytes')
