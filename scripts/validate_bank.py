"""Validate trusted authored code, never run arbitrary participant input.
Usage: python scripts/validate_bank.py
"""
import json
from pathlib import Path

bank=json.loads((Path(__file__).resolve().parents[1]/'raid'/'question_bank.json').read_text(encoding='utf-8'))
assert len(bank)==24
for q in bank:
    bad=q['buggy_code']
    lines=bad.splitlines()
    matches=[i for i,s in enumerate(lines) if s.strip()==q['original_line']]
    assert len(matches)==1,(q['code'],'line nonunique')
    n=matches[0]
    good_lines=lines[:]
    spaces=lines[n][:len(lines[n])-len(lines[n].lstrip())]
    good_lines[n]=spaces+q['accepted_patches'][0]
    good='\n'.join(good_lines)
    compile(bad,q['code']+'-bad','exec')
    compile(good,q['code']+'-good','exec')
    actual=[]
    for case in q['case_options']:
        def run(program):
            namespace={}
            exec(program,namespace)
            try:
                return ('ok',namespace['solve'](case['input']))
            except Exception as exc:
                return ('error',type(exc).__name__)
        buggy=run(bad)
        fixed=run(good)
        assert fixed==('ok',case['expected']),(q['code'],'wrong expected',case,fixed)
        actual.append(buggy!=fixed)
    assert sum(actual)==1,(q['code'],'invalid cases',actual)
    assert actual[q['counterexample_index']],(q['code'],'wrong counterexample index')
print('✅ verified',len(bank),'questions × 3 cases, syntax, unique patches and counterexamples')
