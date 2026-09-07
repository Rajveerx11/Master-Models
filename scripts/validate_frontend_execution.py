"""Validate exported evidence fidelity. This never grants training approval."""
import hashlib
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parent.parent
DEST=ROOT/'datasets/frontend-stack/v2/review/execution-pilot'

def require(condition,message):
    if not condition:raise ValueError(message)

def validate_projection(record,events):
    require(record['training_eligible'] is False,'Evidence must remain ineligible')
    messages=record['messages']
    require(len(messages)==2*len(events)+3,'Captured event omitted or duplicated')
    for index,event in enumerate(events):
        assistant,result=messages[2+2*index:4+2*index]
        calls=assistant.get('tool_calls',[])
        require(assistant['role']=='assistant' and len(calls)==1,'Bad assistant projection')
        require(calls[0]['function']==dict(name=event['name'],arguments=event['arguments']),'Tool call changed')
        require(result['role']=='tool' and result['content']==event['content'],'Tool output changed')
        require(result.get('metadata')==event.get('metadata'),'Tool metadata changed')
        require(result['tool_call_id']==calls[0]['id'],'Tool result link changed')

def validate_decision(decision,events):
    require(decision['training_eligible'] is False,'Review cannot promote evidence')
    last_edit=max(i+1 for i,e in enumerate(events) if e['name']=='edit')
    for index in decision['baseline_events']:
        e=events[index-1]
        require(e['name']=='bash' and e['metadata']['exit_code']!=0,'Baseline must reference an observed failed check')
    for index in decision['final_check_events']:
        e=events[index-1]
        require(index>last_edit and e['name']=='bash' and e['metadata']['exit_code']==0,'Final check must pass after last edit')

def main():
    manifest=json.loads((DEST/'manifest.json').read_text(encoding='utf-8'))
    require(manifest['executed_tasks']==5 and manifest['gold_approved']==0 and manifest['training_eligible'] is False,'Pilot admission drift')
    for relative,expected in manifest['files'].items():
        p=(DEST/relative).resolve();require(p.is_relative_to(DEST.resolve()),'Evidence path escape')
        require(hashlib.sha256(p.read_bytes()).hexdigest()==expected,f'Evidence changed: {relative}')
    for relative,expected in manifest['harness_files'].items():
        require(hashlib.sha256((ROOT/relative).read_bytes()).hexdigest()==expected,f'Harness changed: {relative}')
    review=json.loads((DEST/'review-decisions.json').read_text(encoding='utf-8'))
    fit=json.loads((DEST/'token-fit.json').read_text(encoding='utf-8'))
    pin_path=ROOT/'training/templates/qwen3-4b.pin.json'
    pin=json.loads(pin_path.read_text(encoding='utf-8'))
    require(fit['tokenizer_pin_sha256']==hashlib.sha256(pin_path.read_bytes()).hexdigest(),'Tokenizer pin changed')
    require(pin['template_sha256']==hashlib.sha256((ROOT/'training/templates/qwen3-4b.jinja').read_bytes()).hexdigest(),'Template changed')
    require(fit['tools_sha256']==hashlib.sha256((ROOT/'training/pi_tools.json').read_bytes()).hexdigest(),'Tool schema changed')
    require(review['independent_semantic_review']=='pending' and review['gold_approved']==0,'False independent approval')
    require(len(review['tasks'])==5 and len(fit['records'])==5,'Missing review/fit')
    decisions={r['id']:r for r in review['tasks']}
    for task in manifest['tasks']:
        run=DEST/task['id'];data=(run/'tool-events.jsonl').read_bytes()
        events=[json.loads(line) for line in data.decode().splitlines()]
        record=json.loads((DEST/'records'/f'{task["id"]}.json').read_text(encoding='utf-8'))
        require(record['source_events_sha256']==hashlib.sha256(data).hexdigest(),'Record ancestry changed')
        validate_projection(record,events);validate_decision(decisions[task['id']],events)
        for browser in task['browser_runs']:
            report=json.loads((DEST/browser['path']).read_text(encoding='utf-8'))
            expected=not report['errors'] and bool(report['checks']) and all(c['pass'] for c in report['checks'])
            require(report['passed']==expected,'Browser outcome mismatch')
        for image in decisions[task['id']]['inspected_screenshots']:
            require(image in manifest['files'],'Unbound screenshot')
    for row in fit['records']:
        path=DEST/'records'/f'{row["id"]}.json'
        require(row['record_sha256']==hashlib.sha256(path.read_bytes()).hexdigest(),'Measured record changed')
        require(row['complete_record'] and not row['truncated'] and row['fits_3072']==(row['tokens']<=3072),'Bad token-fit claim')
        require(not row['training_eligible'],'Oversized/unreviewed record promoted')
    print('PASS: five evidence bundles, complete event projections, final-check ordering and hashes; gold=0')

if __name__=='__main__':main()
