"""First attempt per (person, mission); only qualified concepts are ranked."""
from collections import defaultdict
from .models import Attempt

def confusion_stats(category=None,minimum_players=3):
    records=Attempt.objects.select_related('question').order_by('id')
    if category:
        records=records.filter(question__category=category)
    seen=set()
    grouped=defaultdict(lambda:{'wrong':0,'total':0,'players':set(),'questions':set(),
                                'patch_wrong':0,'case_wrong':0,'hints':0})
    for a in records:
        key=(a.player_id,a.question_id)
        if key in seen: continue
        seen.add(key)
        row=grouped[a.question.concept]
        row['total']+=1
        row['wrong']+=int(not a.is_correct)
        row['patch_wrong']+=int(not a.patch_correct)
        row['case_wrong']+=int(not a.case_correct and a.question.difficulty>=2)
        row['hints']+=int(a.hint_used)
        row['players'].add(a.player_id)
        row['questions'].add(a.question_id)
    rows=[]
    for concept,data in grouped.items():
        nplayers=len(data['players'])
        rows.append({'concept':concept,'wrong':data['wrong'],'total':data['total'],
            'players':nplayers,'question_count':len(data['questions']),
            'patch_wrong':data['patch_wrong'],'case_wrong':data['case_wrong'],'hints':data['hints'],
            'rate':round(100*data['wrong']/data['total'],1),
            'qualified':nplayers>=minimum_players})
    rows.sort(key=lambda r:(-r['rate'],-r['players'],r['concept']))
    # If fewer than 5 qualified concepts, use only those in official Top 5.
    qualified=[r for r in rows if r['qualified']]
    return qualified[:5],len(qualified)>=5
