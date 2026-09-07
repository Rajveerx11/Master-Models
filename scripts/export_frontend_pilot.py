"""Export captured pilot evidence and verify archive ancestry and scoped edits."""
import difflib
import io
import json
import shutil
import subprocess
import zipfile
from pathlib import Path
try:
    from .run_frontend_pilot import ROOT,OUT,sha,task_spec,write_json
except ImportError:
    from run_frontend_pilot import ROOT,OUT,sha,task_spec,write_json

DEST=ROOT/'datasets/frontend-stack/v2/review/execution-pilot'

def main():
    registry=json.loads((ROOT/'datasets/v2-registry.json').read_text(encoding='utf-8'))
    tasks=[]
    for number in [1,10,15,20,29]:
        task=task_spec(number); run=OUT/task['id']; target=DEST/task['id']
        target.mkdir(parents=True,exist_ok=True)
        provenance=json.loads((run/'provenance.json').read_text(encoding='utf-8'))
        repo=registry['source_repositories'][task['repository']]['path']
        archive=subprocess.check_output(['git','-C',repo,'archive','--format=zip',task['parent']])
        if sha(archive)!=provenance['archive_sha256']:raise SystemExit('Archive changed')
        source=zipfile.ZipFile(io.BytesIO(archive))
        changed=[]; diff=[]
        for entry in source.infolist():
            if entry.is_dir():continue
            before=source.read(entry.filename); after=(run/'snapshot'/entry.filename).read_bytes()
            if before==after:continue
            if entry.filename=='package.json' and number==1:
                overlay=json.loads((run/'setup-overlay.json').read_text(encoding='utf-8'))
                if sha(before)!=overlay['before_sha256'] or sha(after)!=overlay['after_sha256']:raise SystemExit('Setup overlay drift')
                continue
            if entry.filename not in task['scope_paths']:raise SystemExit(f'Out-of-scope source change: {task["id"]}:{entry.filename}')
            changed.append(dict(path=entry.filename,before_sha256=sha(before),after_sha256=sha(after)))
            diff.extend(difflib.unified_diff(before.decode().replace('\r\n','\n').splitlines(keepends=True),after.decode().replace('\r\n','\n').splitlines(keepends=True),fromfile='a/'+entry.filename,tofile='b/'+entry.filename))
        # Validate every edit against the exact archive bytes, not inferred Git claims.
        events=[json.loads(line) for line in (run/'tool-events.jsonl').read_text(encoding='utf-8').splitlines()]
        replay={p:source.read(p) for p in task['scope_paths']}
        for event in events:
            if event['name']!='edit':continue
            path=event['arguments']['path']; before=replay[path]
            if sha(before)!=event['before_sha256']:raise SystemExit('Edit ancestry mismatch')
            text=before.decode().replace('\r\n','\n'); spans=[]
            for change in event['arguments']['edits']:
                old=change['oldText']
                if not old or text.count(old)!=1:raise SystemExit('Ambiguous captured edit')
                offset=text.index(old);spans.append((offset,offset+len(old),change['newText']))
            spans.sort()
            if any(a[1]>b[0] for a,b in zip(spans,spans[1:])):raise SystemExit('Overlapping captured edits')
            for start,end,replacement in reversed(spans):text=text[:start]+replacement+text[end:]
            replay[path]=text.encode()
            if sha(replay[path])!=event['after_sha256']:raise SystemExit('Edit result mismatch')
        for path,data in replay.items():
            if data!=(run/'snapshot'/path).read_bytes():raise SystemExit('Snapshot disagrees with captured edits')
        (target/'source.patch').write_text(''.join(diff).replace('\r\n','\n'),encoding='utf-8',newline='\n')
        for name in ['provenance.json','tool-events.jsonl','command-events.jsonl','setup-events.jsonl','setup-overlay.json']:
            if (run/name).exists():shutil.copy2(run/name,target/name)
        browser=[]
        if (run/'browser').exists():
            shutil.copytree(run/'browser',target/'browser',dirs_exist_ok=True)
            for p in sorted((target/'browser').glob('*/result.json')):
                report=json.loads(p.read_text(encoding='utf-8'));browser.append(dict(path=p.relative_to(DEST).as_posix(),passed=report['passed'],checks=len(report['checks']),errors=len(report['errors'])))
        tasks.append(dict(id=task['id'],parent=task['parent'],changed_files=changed,tool_events=len(events),
            browser_runs=browser,source_archive_verified=True,captured_edit_chain_verified=True,
            source_lock_unchanged=sha((run/'snapshot/pnpm-lock.yaml').read_bytes())==provenance['source_lock_sha256'],
            author_reference_exposure=True,independent_semantic_review='pending',training_eligible=False))
    for name in ['setup-events.jsonl','runtime.json','tokenizer-source.json']:
        if (OUT/name).exists():shutil.copy2(OUT/name,DEST/name)
    if (OUT/'harness-history').exists():shutil.copytree(OUT/'harness-history',DEST/'harness-history',dirs_exist_ok=True)
    files={p.relative_to(DEST).as_posix():sha(p.read_bytes()) for p in sorted(DEST.rglob('*')) if p.is_file() and p.name not in {'manifest.json','README.md'}}
    harness={p.relative_to(ROOT).as_posix():sha(p.read_bytes()) for p in sorted((ROOT/'scripts/frontend_pilot').rglob('*')) if p.is_file() and '__pycache__' not in p.parts}
    write_json(DEST/'manifest.json',dict(schema_version=1,selected_tasks=30,executed_tasks=5,remaining_tasks=25,gold_approved=0,
        training_eligible=False,expansion_gate='blocked: oversized complete records and pending independent semantic review',
        tasks=tasks,files=files,harness_files=harness,
        limitations=['Same-author replay, reference patches were previously inspected.',
            'Early harness failures are preserved and are not product defect baselines.',
            'Early events predate per-event harness hashes; historical setup lock and final harness are retained.',
            'Source Git archive uses CRLF conversion; original Git blobs and archive bytes have distinct hashes.',
            'Fixtures do not execute native Tauri services or a live model server.',
            'Machine-specific paths and browser timestamps remain intact in raw evidence.']))
    print('Exported five captured pilots; archive ancestry, scope and edit chains verified; gold=0')

if __name__=='__main__':main()
