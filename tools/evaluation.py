#!/usr/bin/env python3
"""Score explicitly supplied paired engineering task outcomes. No model calls.

The input should come from independently executed baseline / candidate trials.
The script refuses invented or ambiguous measurements, but cannot authenticate them.
"""
import argparse, json, sys
from pathlib import Path


def score(run):
    required={'tests_passed','tests_total','high_findings','critical_findings','scope_violations','human_interventions'}
    if set(run) != required or any(type(run[k]) is not int or run[k] < 0 for k in required):
        raise ValueError('Each run requires six nonnegative integer metrics')
    if run['tests_total'] == 0 or run['tests_passed'] > run['tests_total']:
        raise ValueError('Invalid test counts: zero selected tests are not success')
    return {'test_rate': round(run['tests_passed']/run['tests_total'],3),
            'quality_pass': run['tests_passed']==run['tests_total'] and
                            run['high_findings']==0 and run['critical_findings']==0 and run['scope_violations']==0,
            'interventions':run['human_interventions']}


def evaluate(records):
    if not isinstance(records,list) or not records: raise ValueError('Need a nonempty list of paired trials')
    results=[]
    ids=set()
    for t in records:
        if not isinstance(t,dict) or set(t)!={'id','baseline','candidate'} or not isinstance(t['id'],str):
            raise ValueError('Each trial must contain id, baseline and candidate')
        if not t['id'] or t['id'] in ids:raise ValueError('Duplicate/empty trial ID')
        ids.add(t['id'])
        results.append({'id':t['id'],'baseline':score(t['baseline']),'candidate':score(t['candidate'])})
    n=len(results)
    b=sum(x['baseline']['quality_pass'] for x in results)
    c=sum(x['candidate']['quality_pass'] for x in results)
    return {'trials':n,'baseline_passed':b,'candidate_passed':c,
            'baseline_success_rate':round(b/n,3),'candidate_success_rate':round(c/n,3),
            'delta_percentage_points':round((c-b)*100/n,1),
            'results':results,
            'caveat':'Scores are based solely on provided measurements; evaluation does not execute Codex or verify the measurements.'}


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--input',required=True)
    p.add_argument('--output')
    args=p.parse_args()
    try:
        summary=evaluate(json.loads(Path(args.input).read_text()))
        output=json.dumps(summary,indent=2)+'\n'
        if args.output:Path(args.output).write_text(output)
        print(output)
        return 0
    except (ValueError,KeyError,OSError,TypeError,json.JSONDecodeError) as ex:
        print('ERROR:',ex,file=sys.stderr);return 2
if __name__=='__main__':sys.exit(main())
