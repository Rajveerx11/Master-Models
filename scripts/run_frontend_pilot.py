"""Isolated source snapshots and append-only actual pi tool events for the pilot.

Setup is separate from task events. No synthetic command output or approval labels.
"""
from __future__ import annotations
import argparse
import hashlib
import io
import json
import os
import shutil
import shlex
import subprocess
import sys
import time
import tempfile
import zipfile
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / 'outputs/frontend-pilot'
SPEC = ROOT / 'datasets/frontend-stack/v2/review/pilot/tasks.jsonl'
HARNESS = OUT / 'harness'
PNPM = shutil.which('pnpm.cmd')
BASH = Path('C:/Program Files/Git/bin/bash.exe')

def sha(data):
    return hashlib.sha256(data).hexdigest()

def task_spec(number):
    return next(r for r in map(json.loads, SPEC.read_text(encoding='utf-8').splitlines()) if r['id'] == f'frontend-pilot-{number:02}')

def write_json(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')

def append(path, event):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('a', encoding='utf-8', newline='\n') as stream:
        stream.write(json.dumps(event, ensure_ascii=False)+'\n')

def captured_command(argv, cwd, log, env=None):
    start = datetime.now(timezone.utc).isoformat()
    before = time.monotonic()
    completed = subprocess.run(argv, cwd=cwd, env=env, capture_output=True)
    event = dict(argv=[str(a) for a in argv], cwd=str(cwd), started_at=start,
                 duration_seconds=round(time.monotonic()-before, 6), exit_code=completed.returncode,
                 stdout=completed.stdout.decode('utf-8', errors='replace'),
                 stderr=completed.stderr.decode('utf-8', errors='replace'),
                 stdout_sha256=sha(completed.stdout), stderr_sha256=sha(completed.stderr))
    append(log, event)
    print(event['stdout'], end='')
    print(event['stderr'], end='', file=sys.stderr)
    return event

def repair_desktop_setup(number):
    """Explicit, hash-guarded setup overlay for the one observed manifest mismatch."""
    if number != 1: raise SystemExit('No setup overlay specified for this task')
    run=OUT/task_spec(number)['id']; path=run/'snapshot/package.json'
    before=path.read_bytes()
    if sha(before) != '017ea87958013fe8344f9d7d71162c0822b5d9ed12c5c733bb52403fc9db8829':
        raise SystemExit('Unexpected parent package; refuse setup overlay')
    package=json.loads(before)
    if package['devDependencies'].pop('husky') != '^9.1.7': raise SystemExit('Unexpected dependency')
    write_json(path,package)
    write_json(run/'setup-overlay.json',dict(
        reason='Parent root package declares husky absent from its lockfile. Remove only this unused Git-hook dev dependency for isolated no-Git execution; source lock remains unchanged.',
        path='package.json',before_sha256=sha(before),after_sha256=sha(path.read_bytes()),
        removed={'devDependencies.husky':'^9.1.7'},training_eligible=False))
    return captured_command([PNPM,'install','--frozen-lockfile','--ignore-scripts'],run/'snapshot',run/'setup-events.jsonl')['exit_code']

def harness_hashes():
    hashes={}
    for directory,folders,files in os.walk(HARNESS):
        folders[:]=[name for name in folders if name not in {'node_modules','__pycache__'}]
        for name in files:
            p=Path(directory)/name
            hashes[p.relative_to(HARNESS).as_posix()]=sha(p.read_bytes())
    return hashes

def configure():
    source=ROOT/'scripts/frontend_pilot'
    for p in source.rglob('*'):
        if p.is_file() and '__pycache__' not in p.parts:
            target=HARNESS/p.relative_to(source);target.parent.mkdir(parents=True,exist_ok=True)
            shutil.copy2(p,target)
    temporary=Path(tempfile.gettempdir())/'frontend-pilot-browser.cjs'
    shutil.copy2(source/'browser-check.cjs',temporary)
    quote=lambda p:shlex.quote(Path(p).as_posix())
    runner=Path.home()/'.agents/skills/playwright-skill/run.js'
    if not runner.is_file():raise SystemExit(f'Browser skill runner missing: {runner}')
    commands={
        'check':f'node {quote(HARNESS/"node_modules/vitest/vitest.mjs")} run --config {quote(HARNESS/"vitest.config.mjs")} --reporter=dot',
        'browser':f'node {quote(runner)} {quote(temporary)} && node {quote(HARNESS/"browser-status.cjs")}',
        'typecheck':'node node_modules/typescript/bin/tsc --version && node node_modules/typescript/bin/tsc --noEmit',
        'typecheck-desktop':'node node_modules/typescript/bin/tsc --version && node node_modules/typescript/bin/tsc -p apps/desktop/tsconfig.json --noEmit',
    }
    for name,command in commands.items():write_json(OUT/f'{name}-call.json',dict(name='bash',arguments=dict(command=command)))
    print('Configured source-pinned checks and browser skill entry point')

def prepare(numbers):
    require_node = subprocess.check_output(['node', '--version'], text=True).strip()
    require_pnpm = subprocess.check_output([PNPM, '--version'], text=True).strip()
    if require_node != 'v24.16.0' or require_pnpm != '10.9.0':
        raise SystemExit('Runtime mismatch: require Node v24.16.0 / pnpm 10.9.0')
    HARNESS.mkdir(parents=True, exist_ok=True)
    shutil.copy2(ROOT/'scripts/frontend_pilot/package.json', HARNESS/'package.json')
    checked_lock = ROOT/'scripts/frontend_pilot/pnpm-lock.yaml'
    if checked_lock.exists():
        shutil.copy2(checked_lock, HARNESS/'pnpm-lock.yaml')
    setup_log = OUT/'setup-events.jsonl'
    mode = '--frozen-lockfile' if checked_lock.exists() else '--no-frozen-lockfile'
    event = captured_command([PNPM, 'install', mode, '--ignore-scripts'], HARNESS, setup_log)
    if event['exit_code']:
        raise SystemExit(event['exit_code'])
    shutil.copy2(HARNESS/'pnpm-lock.yaml', checked_lock)
    for file in (ROOT/'scripts/frontend_pilot').rglob('*'):
        if file.is_file() and file.name not in {'package.json','pnpm-lock.yaml'}:
            target=HARNESS/file.relative_to(ROOT/'scripts/frontend_pilot')
            target.parent.mkdir(parents=True,exist_ok=True)
            shutil.copy2(file,target)
    registry=json.loads((ROOT/'datasets/v2-registry.json').read_text())
    for number in numbers:
        task=task_spec(number)
        run=OUT/task['id']
        snapshot=run/'snapshot'
        if snapshot.exists():
            raise SystemExit(f'Refuse to overwrite existing snapshot: {snapshot}')
        repo=registry['source_repositories'][task['repository']]['path']
        archive=subprocess.check_output(['git','-C',repo,'archive','--format=zip',task['parent']])
        snapshot.mkdir(parents=True)
        with zipfile.ZipFile(io.BytesIO(archive)) as zipped:
            # Git archive entries are checked before extraction, including symlink-mode entries.
            for item in zipped.infolist():
                dest=(snapshot/item.filename).resolve()
                if not dest.is_relative_to(snapshot.resolve()):
                    raise SystemExit('Unsafe archive entry')
            zipped.extractall(snapshot)
        # No Git history or frozen evaluation tree is copied into the snapshots.
        metadata=dict(task_id=task['id'], repository=task['repository'], parent=task['parent'],
                      archive_sha256=sha(archive), node=require_node, pnpm=require_pnpm,
                      spec_sha256=sha(SPEC.read_bytes()), created_at=datetime.now(timezone.utc).isoformat(),
                      source_lock_sha256=sha((snapshot/'pnpm-lock.yaml').read_bytes()),
                      author_reference_exposure=True, training_eligible=False)
        write_json(run/'provenance.json',metadata)
        event=captured_command([PNPM,'install','--frozen-lockfile','--ignore-scripts'],snapshot,run/'setup-events.jsonl')
        if sha((snapshot/'pnpm-lock.yaml').read_bytes()) != metadata['source_lock_sha256']:
            raise SystemExit('Source lockfile mutated during setup')
        if event['exit_code']:
            print(f"SETUP FAILED {task['id']}; captured, not silently repaired",file=sys.stderr)
        else:
            print(f"PREPARED {task['id']}")
    write_json(OUT/'runtime.json',dict(node=require_node,pnpm=require_pnpm,
        harness_lock_sha256=sha((HARNESS/'pnpm-lock.yaml').read_bytes()), platform=sys.platform))

def tool(number, call_path):
    task=task_spec(number)
    run=OUT/task['id']; snapshot=run/'snapshot'
    call=json.loads(Path(call_path).read_text(encoding='utf-8'))
    name,args=call['name'],call['arguments']
    event=dict(name=name,arguments=args,started_at=datetime.now(timezone.utc).isoformat())
    event['harness_files']=harness_hashes()
    tick=time.monotonic()
    if name in {'read','edit'}:
        path=(snapshot/args['path']).resolve()
        if not path.is_relative_to(snapshot.resolve()):
            raise SystemExit('Tool path escapes snapshot')
        original=path.read_text(encoding='utf-8')
        event['before_sha256']=sha(path.read_bytes())
        if name=='read':
            lines=original.splitlines(keepends=True)
            offset=args.get('offset',1)-1
            result=''.join(lines[offset:offset+args.get('limit',2000)])
        else:
            if args['path'] not in task['scope_paths']:
                raise SystemExit('Edit outside declared task scope')
            spans=[]
            for edit in args['edits']:
                old=edit['oldText']
                if not old or original.count(old)!=1:
                    raise SystemExit('Edit must have exactly one nonempty match')
                start=original.index(old); spans.append((start,start+len(old),edit['newText']))
            spans.sort()
            if any(a[1]>b[0] for a,b in zip(spans,spans[1:])):
                raise SystemExit('Overlapping edits')
            updated=original
            for start,end,replacement in reversed(spans):
                updated=updated[:start]+replacement+updated[end:]
            path.write_text(updated,encoding='utf-8',newline='\n')
            event['after_sha256']=sha(path.read_bytes())
            result=f"Successfully applied {len(spans)} edit(s) to {args['path']}."
        event['content']=result
        print(result,end='' if result.endswith('\n') else '\n')
    elif name=='bash':
        env=os.environ.copy()
        env.update(PILOT_SNAPSHOT=str(snapshot),PILOT_TASK=str(number),PILOT_RUN=str(run),NO_COLOR='1')
        result=captured_command([str(BASH),'--noprofile','--norc','-c',args['command']],snapshot,run/'command-events.jsonl',env)
        event.update(content=result['stdout']+result['stderr'], metadata={'exit_code':result['exit_code']},
                     stdout=result['stdout'],stderr=result['stderr'],argv=result['argv'],cwd=str(snapshot))
    else:
        raise SystemExit('Supported tools: read, edit, bash')
    event['duration_seconds']=round(time.monotonic()-tick,6)
    append(run/'tool-events.jsonl',event)
    return event.get('metadata',{}).get('exit_code',0)

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    sub=parser.add_subparsers(dest='action',required=True)
    prep=sub.add_parser('prepare'); prep.add_argument('tasks',type=int,nargs='+')
    use=sub.add_parser('tool'); use.add_argument('task',type=int); use.add_argument('call',type=Path)
    repair=sub.add_parser('repair-setup'); repair.add_argument('task',type=int)
    sub.add_parser('configure')
    args=parser.parse_args()
    if args.action=='prepare': prepare(args.tasks)
    elif args.action=='configure': configure()
    elif args.action=='repair-setup': sys.exit(repair_desktop_setup(args.task))
    else: sys.exit(tool(args.task,args.call))

if __name__=='__main__': main()
