"""Validate authored question code and 4 MCQ options (never student submissions).
Usage: python scripts/validate_bank.py
"""
import json
import signal
from pathlib import Path

bank=json.loads((Path(__file__).resolve().parents[1]/'raid'/'question_bank.json').read_text(encoding='utf-8'))
assert len(bank)==32,(len(bank),'expected 32 authored questions')
assert len({q['code'] for q in bank})==len(bank)

class ProgramTimeout(Exception):
    pass

def on_timeout(_signum,_frame):
    raise ProgramTimeout('authored snippet ran too long')

signal.signal(signal.SIGALRM,on_timeout)
def run(program, input_data):
    namespace={}
    try:
        exec(program,namespace)
        signal.setitimer(signal.ITIMER_REAL,0.2)
        return ('ok',namespace['solve'](input_data))
    except Exception as exc:
        return ('error',type(exc).__name__)
    finally:
        signal.setitimer(signal.ITIMER_REAL,0)

for q in bank:
    code=q['code']
    bad=q['buggy_code']
    lines=bad.splitlines()
    hits=[i for i,s in enumerate(lines) if s.strip()==q['original_line']]
    assert len(hits)==1,(code,'original line must be unique')
    i=hits[0]
    leading=lines[i][:len(lines[i])-len(lines[i].lstrip())]
    def patched(text):
        modified=lines[:]
        modified[i]=leading+text
        return '\n'.join(modified)
    good=patched(q['accepted_patches'][0])
    compile(bad,code+'-buggy','exec')
    compile(good,code+'-correct','exec')
    actual=[]
    for c in q['case_options']:
        fixed=run(good,c['input'])
        assert fixed==('ok',c['expected']),(code,'expected result mismatch',c,fixed)
        actual.append(run(bad,c['input'])!=fixed)
    assert len(actual)==3 and sum(actual)==1,(code,'exactly one counterexample required',actual)
    assert actual[q['counterexample_index']],(code,'counterexample index wrong')
    choices=q['choices']
    assert len(choices)==4 and len(set(choices))==4,(code,'four distinct choices')
    assert choices.count(q['accepted_patches'][0])==1,(code,'one correct option')
    for opt in choices:
        if opt==q['accepted_patches'][0]: continue
        candidate=patched(opt)
        compile(candidate,code+'-distractor','exec')
        assert any(run(candidate,c['input'])!=('ok',c['expected']) for c in q['case_options']), (code,'distractor matches all examples',opt)
print('✅ verified',len(bank),'4-choice missions × 3 cases; one correct option and three testable distractors each')
