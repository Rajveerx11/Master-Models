"""Pin the downloaded Qwen tokenizer and measure complete captured pilot records.

No model weights, inference, truncation or training. All failed tool calls remain.
The messages are a mechanical projection of events, not an authored gold trace.
"""
import hashlib
import json
from pathlib import Path
from transformers import AutoTokenizer
import transformers, tokenizers, huggingface_hub
import jinja2

ROOT=Path(__file__).resolve().parent.parent
OUT=ROOT/'outputs/frontend-pilot'
REVIEW=ROOT/'datasets/frontend-stack/v2/review/execution-pilot'
REVISION='1cfa9a7208912126459214e8b04321603b3df60c'

def sha(data):return hashlib.sha256(data).hexdigest()
def save(path,data):
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')

def main():
    tokenizer=AutoTokenizer.from_pretrained(OUT/'tokenizer',local_files_only=True)
    template=tokenizer.chat_template
    if not isinstance(template,str) or '<tool_call>' not in template:raise SystemExit('Unexpected template')
    target=ROOT/'training/templates/qwen3-4b.jinja'
    target.write_text(template,encoding='utf-8',newline='\n')
    pin=dict(model='Qwen/Qwen3-4B',revision=REVISION,
        source=f'https://huggingface.co/Qwen/Qwen3-4B/blob/{REVISION}/tokenizer_config.json',
        template_sha256=sha(target.read_bytes()),
        tokenizer_files={p.name:sha(p.read_bytes()) for p in sorted((OUT/'tokenizer').glob('*.json'))},
        merges_sha256=sha((OUT/'tokenizer/merges.txt').read_bytes()),
        packages=dict(transformers=transformers.__version__,tokenizers=tokenizers.__version__,huggingface_hub=huggingface_hub.__version__,jinja2=jinja2.__version__),
        render_options=dict(enable_thinking=False,add_generation_prompt=False),max_tokens=3072,
        weights_downloaded=False,training_eligible=False,
        limitation='Pins export-identity tokenizer only; quantized training base revision and parity remain pending.')
    save(ROOT/'training/templates/qwen3-4b.pin.json',pin)
    tools=json.loads((ROOT/'training/pi_tools.json').read_text(encoding='utf-8'))
    rows=[]
    specs={r['id']:r for r in map(json.loads,(ROOT/'datasets/frontend-stack/v2/review/pilot/tasks.jsonl').read_text(encoding='utf-8').splitlines())}
    for run in sorted(OUT.glob('frontend-pilot-*')):
        if not (run/'tool-events.jsonl').exists():continue
        events=[json.loads(line) for line in (run/'tool-events.jsonl').read_text(encoding='utf-8').splitlines()]
        messages=[dict(role='system',content='You are a frontend coding assistant. Inspect source, make scoped edits, and report only observed verification results.'),dict(role='user',content=specs[run.name]['prompt'])]
        for index,event in enumerate(events):
            call_id=f'call_{index+1}'
            messages.append(dict(role='assistant',content='',tool_calls=[dict(id=call_id,type='function',function=dict(name=event['name'],arguments=event['arguments']))]))
            result=dict(role='tool',tool_call_id=call_id,name=event['name'],content=event['content'])
            if 'metadata' in event:result['metadata']=event['metadata']
            messages.append(result)
        # A factual boundary statement; no fabricated missing author reasoning.
        messages.append(dict(role='assistant',content='Captured pilot execution only. Independent semantic review and training admission remain pending.'))
        record=dict(id=run.name,tools=tools,messages=messages,training_eligible=False,
            derivation='Mechanical projection of every captured event in order; no reconstructed intermediate reasoning.',
            source_events_sha256=sha((run/'tool-events.jsonl').read_bytes()))
        save(REVIEW/'records'/f'{run.name}.json',record)
        rendered=tokenizer.apply_chat_template(messages,tools=tools,tokenize=False,enable_thinking=False,add_generation_prompt=False)
        if '<tools>' not in rendered or rendered.count('<tool_call>')<len(events):raise SystemExit('Tool rendering lost')
        ids=tokenizer.apply_chat_template(messages,tools=tools,tokenize=True,enable_thinking=False,add_generation_prompt=False)
        save(OUT/'rendered'/f'{run.name}.json',dict(text=rendered,token_ids=ids))
        rows.append(dict(id=run.name,events=len(events),tokens=len(ids),fits_3072=len(ids)<=3072,
            rendered_sha256=sha(rendered.encode()),record_sha256=sha((REVIEW/'records'/f'{run.name}.json').read_bytes()),
            complete_record=True,truncated=False,training_eligible=False))
    save(REVIEW/'token-fit.json',dict(tokenizer_pin_sha256=sha((ROOT/'training/templates/qwen3-4b.pin.json').read_bytes()),
        tools_sha256=sha((ROOT/'training/pi_tools.json').read_bytes()),records=rows,
        limitation='Counts include all captured tool failures and reads. No truncation. These are replay evidence records, not approved V2 trajectories.'))
    print(json.dumps(rows,indent=2))

if __name__=='__main__':main()
