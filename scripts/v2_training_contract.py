"""Model-free, fail-closed V2 Colab contract (stdlib only).

No V1 fallback. Final manifest schema_version=2 binds `artifacts` (relative path ->
SHA256), `records` (id -> kind/generator/families), `frozen_eval` (path/repository/
reference/start), and a spot-check (ledger path, required_ids). Default policy
`human` uses `human_spot_check`; explicitly declared `independent_ai` uses
`ai_spot_check` with a hash-bound third-reviewer evidence file per sampled row.
It also names `reviews` and `validation` JSON files. Every named file must be
in artifacts. Reviews bind exact record fingerprints, two independent approving
reviewers, and all CHECKS. Validation binds fingerprints and source families.
No policy infers approval from scores or impersonates a human; a file hash alone
cannot authenticate the reviewer or establish semantic correctness.

Base pin schema_version=1: model/revision, canonical_model/canonical_revision,
canonical_pin_sha256, template_sha256 (canonical), native_template_sha256,
native_tokenizer_files, backend_files, parity_verified=true, normalization with
chat_template (explicit documented canonical normalization), native_pad_token/id,
canonical_pad_token/id, render_options. Native file hashes precede normalization.
Runtime independently compares canonical/native unpadded rendering per row.
weights_downloaded/training_eligible=false are metadata, not runtime waivers.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import re
from datetime import datetime
from collections import Counter
from pathlib import Path, PurePosixPath

try:
    from .build_short_train import check_trajectory, fingerprint
except ImportError:
    from build_short_train import check_trajectory, fingerprint

ROOT = Path(__file__).resolve().parent.parent
BASE = 'unsloth/Qwen3-4B-bnb-4bit'
REVISION = 'cad0bedfdd862093a12af478cb974ab2addd0e0a'
CANONICAL = 'Qwen/Qwen3-4B'
CANONICAL_REVISION = '1cfa9a7208912126459214e8b04321603b3df60c'
CHECKS = {'structure', 'tool_contract', 'source_identity', 'execution', 'semantics', 'contamination', 'source_families'}
SHA = re.compile(r'^[0-9a-f]{64}$')
COMMIT = re.compile(r'^[0-9a-f]{40}$')
TOKENIZER_FILES = {'tokenizer.json', 'tokenizer_config.json', 'vocab.json', 'merges.txt'}
CONTRACT_FILES = ('datasets/v2-registry.json', 'training/pi_tools.json',
                  'training/templates/qwen3-4b.jinja', 'training/templates/qwen3-4b.pin.json',
                  'training/templates/qwen3-4b.base-pin.json', 'training/requirements-v2-colab.txt')


def canonical(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(',', ':'))


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def require(condition, message):
    if not condition:
        raise ValueError(message)


def safe_path(root: Path, name: str) -> Path:
    require(isinstance(name, str) and name and '\\' not in name and ':' not in name, 'invalid artifact path')
    path = PurePosixPath(name)
    require(not path.is_absolute() and '..' not in path.parts and str(path) == name, f'unsafe artifact path: {name}')
    target = (root / name).resolve()
    require(target.is_relative_to(root.resolve()), f'artifact escapes root: {name}')
    return target


def load_json(path):
    return json.loads(path.read_text(encoding='utf-8'))


def load_rows(path):
    rows = [json.loads(line) for line in path.read_text(encoding='utf-8').splitlines() if line.strip()]
    require(rows and all(isinstance(row, dict) for row in rows), f'{path}: empty/non-object JSONL')
    return rows


def validate_base_pin(base, pin):
    require(base.get('schema_version') == 1, 'base pin schema_version must be 1')
    require(base.get('model') == BASE and base.get('revision') == REVISION, 'unpinned quantized 4B base')
    require(base.get('canonical_model') == CANONICAL and base.get('canonical_revision') == CANONICAL_REVISION, 'unpinned canonical 4B identity')
    require(pin.get('model') == CANONICAL and pin.get('revision') == CANONICAL_REVISION, 'canonical tokenizer pin mismatch')
    require(SHA.fullmatch(base.get('native_template_sha256', '')) is not None, 'missing native template hash')
    files = base.get('native_tokenizer_files', {})
    native_files = TOKENIZER_FILES | {'config.json', 'special_tokens_map.json'}
    require(native_files <= files.keys() and all(SHA.fullmatch(files[key]) for key in native_files), 'missing native tokenizer/config hashes')
    canonical_files = dict(pin.get('tokenizer_files', {}))
    canonical_files['merges.txt'] = pin.get('merges_sha256')
    for name in ('tokenizer.json', 'vocab.json', 'merges.txt'):
        require(files[name] == canonical_files.get(name) == base.get('backend_files', {}).get(name), f'base/canonical {name} differs')
    norm = base.get('normalization', {})
    require(base.get('parity_verified') is True
            and isinstance(norm.get('chat_template'), str) and norm['chat_template'].strip()
            and base.get('template_sha256') == pin.get('template_sha256'), 'normalization not explicitly verified/documented')
    require(norm.get('native_pad_token') == '<|vision_pad|>' and norm.get('canonical_pad_token') == '<|endoftext|>'
            and type(norm.get('native_pad_token_id')) is int and type(norm.get('canonical_pad_token_id')) is int
            and norm['native_pad_token_id'] == 151654 and norm['canonical_pad_token_id'] == 151643,
            'missing native/canonical pad contract')
    require(pin.get('render_options') == norm.get('render_options') == {'enable_thinking': False, 'add_generation_prompt': False}, 'render options drift')


def assistant_labels(text, ids, offsets, expected_calls):
    """Mask template turns, not tool-call markers in system instruction examples."""
    require(len(ids) == len(offsets), 'token/offset count differs')
    spans = [(match.start(1), match.end()) for match in
             re.finditer(r'<\|im_start\|>assistant\n(.*?)<\|im_end\|>', text, re.S)]
    labels = [token if any(start >= a and end <= b for a, b in spans) and end > start else -100
              for token, (start, end) in zip(ids, offsets)]
    require(any(label != -100 for label in labels), 'all assistant labels masked')
    calls = []
    for a, b in spans:
        calls.extend((a + match.start(), a + match.end()) for match in
                     re.finditer(r'<tool_call>.*?</tool_call>', text[a:b], re.S))
    require(len(calls) == expected_calls, 'rendered assistant tool-call count differs')
    for start, end in calls:
        indices = [i for i, (a, b) in enumerate(offsets) if a < end and b > start]
        require(indices and all(labels[i] != -100 for i in indices), 'assistant tool-call labels missing')
    return labels


def normalized_prompt(row):
    text = '\n'.join(m.get('content', '') or '' for m in row['messages'] if m['role'] == 'user')
    return ' '.join(re.findall(r'[a-z0-9_]+', text.lower()))


def source_keys(row, metadata):
    families = metadata.get('families')
    require(isinstance(families, list) and families and all(isinstance(x, str) and x for x in families), 'missing complete source families')
    keys = {'family:' + family for family in families}
    source = row.get('source')
    require(isinstance(source, dict) and source.get('license'), 'source/license required (including general rows)')
    if metadata['kind'] == 'gold':
        require(set(source) == {'repository', 'commit', 'parent', 'files', 'license'}, 'invalid gold source')
        require(source['files'] and all(isinstance(x, str) for x in source['files']), 'source files required')
        for field in ('commit', 'parent'):
            require(COMMIT.fullmatch(source.get(field, '')), 'gold source requires full hashes')
            keys.add('commit:' + source['repository'] + ':' + source[field])
        require(source['commit'] != source['parent'], 'identical source and parent')
    else:
        require(isinstance(source.get('identity'), str) and source['identity'], 'general source identity required')
        keys.add('general:' + source['identity'])
    return keys


def validate_tool_value(value, schema, where):
    """Closed subset matching pi_tools.json; new schema constructs fail closed."""
    supported = {'type', 'required', 'properties', 'items', 'description', 'additionalProperties', 'enum', 'const'}
    require(isinstance(schema, dict) and set(schema) <= supported, where + ': unsupported tool schema')
    kind = schema.get('type')
    matches = {'object': isinstance(value, dict), 'array': isinstance(value, list),
               'string': isinstance(value, str), 'boolean': type(value) is bool,
               'number': type(value) in (int, float), 'integer': type(value) is int,
               'null': value is None}
    require(kind in matches and matches[kind], where + ': tool argument type mismatch')
    if 'enum' in schema: require(value in schema['enum'], where + ': argument outside enum')
    if 'const' in schema: require(value == schema['const'], where + ': argument differs from const')
    if kind == 'object':
        properties = schema.get('properties', {})
        require(set(schema.get('required', [])) <= set(value) <= set(properties), where + ': missing/unknown tool argument')
        for name, item in value.items(): validate_tool_value(item, properties[name], where + '.' + name)
    if kind == 'array':
        require('items' in schema, where + ': untyped tool array')
        for index, item in enumerate(value): validate_tool_value(item, schema['items'], where + f'[{index}]')


def validate_row(row, metadata, specialist, tools):
    require(set(row) == {'id', 'schema_version', 'specialist', 'source', 'messages', 'tools', 'quality'}, 'invalid V2 row fields')
    require(metadata.get('kind') in {'gold', 'general'}, 'unknown corpus kind')
    require(isinstance(metadata.get('generator'), str) and metadata['generator'], 'generator identity required')
    require(row.get('schema_version') == 2 and isinstance(row.get('id'), str) and row['id'], 'not a V2 record')
    require(row.get('specialist') == (specialist if metadata['kind'] == 'gold' else 'general'), 'wrong specialist/general identity')
    check_trajectory(row, row['id'])
    require(row['messages'][-1].get('content') and not row['messages'][-1].get('tool_calls'), 'missing final assistant summary')
    require(row.get('tools') == tools if metadata['kind'] == 'gold' else row.get('tools') in (None, [], tools), 'tool schema drift')
    schemas = {tool['function']['name']: tool['function']['parameters'] for tool in row.get('tools') or []}
    require(len(schemas) == len(row.get('tools') or []), 'duplicate declared tools')
    for message in row['messages']:
        for call in message.get('tool_calls') or []:
            require(set(call) == {'name', 'arguments'}, 'invalid pi tool-call fields')
            validate_tool_value(call['arguments'], schemas[call['name']], row['id'] + ':' + call['name'])
    quality = row.get('quality', {})
    require(set(quality) == {'difficulty', 'skills', 'verification_commands', 'review_state', 'judge_score'}, 'invalid quality fields')
    require(quality['difficulty'] in {'easy', 'medium', 'hard'} and isinstance(quality['skills'], list)
            and quality['skills'] and all(isinstance(x, str) and x for x in quality['skills']), 'missing difficulty/skills')
    require(quality.get('review_state') in {'judge_passed', 'human_approved'}, 'record not reviewed')
    require(type(quality.get('judge_score')) is int and 8 <= quality['judge_score'] <= 10, 'record judge score outside 8-10')
    if metadata['kind'] == 'gold':
        require(metadata.get('author_reference_exposure') is False, 'gold authorship missing/has reference exposure')
        commands = quality.get('verification_commands')
        require(isinstance(commands, list) and commands and all(isinstance(c, str) and c for c in commands), 'missing gold verification commands')
        success = set()
        for index, message in enumerate(row['messages']):
            if message.get('role') == 'assistant':
                for offset, call in enumerate(message.get('tool_calls') or [], 1):
                    if call['name'] in {'edit', 'write'}:
                        success.clear()
                    if call['name'] == 'bash':
                        result = row['messages'][index + offset]
                        code = result.get('metadata', {}).get('exit_code')
                        require(type(code) is int, 'bash result missing real exit_code')
                        if code == 0:
                            content = result.get('content')
                            require(isinstance(content, str), 'bash output must be captured text')
                            # Same obvious contradictory-success signals used by
                            # the existing V2 audit; do not infer success from text.
                            require(not re.search(r'(?im)^\s*(?:Error:|error:|FAIL(?:\s|$)|npm ERR!|[^\n]*error TS\d+)', content), 'exit_code=0 contradicts failure output')
                            success.add(call['arguments'].get('command'))
        require(set(commands) <= success, 'verification lacks successful post-edit execution')


def validate_split_policy(policy, splits, records, gold_minimum):
    require(policy == {'method':'source-family-grouped', 'seed':3407, 'holdout_fraction':0.05}, 'missing/changed grouped 5% split policy')
    counts = {split:Counter(records[row['id']]['kind'] for row in rows) for split,rows in splits.items()}
    for kind,minimum in (('gold',gold_minimum),('general',60)):
        total = counts['train'][kind] + counts['holdout'][kind]
        require(counts['train'][kind] >= math.floor(minimum * 0.95), f'{kind}: insufficient training coverage; holdout is not training')
        require(counts['holdout'][kind] > 0 and abs(counts['holdout'][kind] - round(total * 0.05)) <= 1,
                f'{kind}: grouped holdout differs from 5% by more than one record')
    return {split:dict(value) for split,value in counts.items()}


def validate_probe_evidence(evidence):
    require(type(evidence.get('optimizer_steps')) is int and evidence['optimizer_steps'] == 1
            and type(evidence.get('optimizer_attempts')) is int and evidence['optimizer_attempts'] == 1,
            'probe needs exactly one optimizer update attempt')
    require(evidence.get('optimizer_step_was_skipped') is False, 'probe optimizer update was skipped')
    require(evidence.get('gradient_finite') is True and evidence.get('gradient_nonzero') is True
            and evidence.get('adapter_finite') is True, 'probe gradients/adapter invalid')
    for key in ('loss','learning_rate','adapter_change_max'):
        value = evidence.get(key)
        require(type(value) in (int,float) and math.isfinite(value) and (value >= 0 if key == 'loss' else value > 0),
                'probe invalid/non-updating ' + key)
    require(evidence.get('longest_holdout_passed') is True, 'longest holdout memory/finite-loss probe missing')


def file_sha256(path):
    digest = hashlib.sha256()
    with path.open('rb') as stream:
        for chunk in iter(lambda:stream.read(8*1024**2), b''): digest.update(chunk)
    return digest.hexdigest()


def checkpoint_hashes(folder):
    files = {}
    for path in folder.rglob('*'):
        require(not path.is_symlink(), 'checkpoint contains a symlink')
        if path.is_file() and path.name != 'checkpoint-hashes.json':
            files[path.relative_to(folder).as_posix()] = file_sha256(path)
    require(files, 'empty checkpoint')
    return files


def validate_checkpoint(folder, run_contract):
    require(re.fullmatch(r'checkpoint-[0-9]+', folder.name), 'invalid checkpoint name')
    require(load_json(folder / 'run-contract.json') == run_contract, 'checkpoint run contract differs')
    require(all((folder / name).is_file() for name in ('trainer_state.json','optimizer.pt','scheduler.pt')), 'incomplete resumable checkpoint')
    require(load_json(folder / 'trainer_state.json')['global_step'] == int(folder.name.split('-')[1]), 'checkpoint step identity differs')
    require(load_json(folder / 'checkpoint-hashes.json') == checkpoint_hashes(folder), 'checkpoint content hash mismatch')


def discover_gguf_exports(requested, outputs, result=None, previous=()):
    """Use same-pinned Unsloth's returned paths and requested/_gguf sibling roots."""
    outputs=outputs.resolve();requested=Path(requested)
    sibling=requested.with_name(requested.name+'_gguf')
    require(result is None or isinstance(result,dict), 'unsupported Unsloth export result')
    result=result or {}
    def contained(value, base):
        path=Path(value)
        if not path.is_absolute():path=base/path
        require(path.resolve().is_relative_to(outputs), 'GGUF export path escapes outputs')
        for component in (path,*path.parents):
            require(not component.is_symlink(), 'GGUF export contains a symlink')
            if component==outputs:break
        return path
    returned_dir=contained(result.get('gguf_directory') or sibling,outputs.parent)
    files=result.get('gguf_files',[])
    require(isinstance(files,(list,tuple)), 'invalid returned GGUF paths')
    roots=[contained(requested,outputs.parent),contained(sibling,outputs.parent),returned_dir]
    roots.extend(contained(value,returned_dir) for value in files)
    found=set();previous={Path(p).resolve() for p in previous}
    for root in roots:
        candidates=[root] if root.is_file() else root.rglob('*.gguf') if root.is_dir() else []
        for path in candidates:
            path=contained(path,outputs.parent)
            if path.is_file() and path.suffix.lower()=='.gguf':
                require(path.resolve() not in previous, 'pre-existing GGUF candidate; preserve it and use a fresh runtime')
                found.add(path.resolve())
    return sorted(found,key=str)


def validate_gguf_reader(reader, file_bytes, config, vocab, template, special_ids):
    """Validate a trusted gguf.GGUFReader's full tensor table and pinned identity.

    No gguf/numpy import here: callers provide the pinned reader; tests use explicitly
    synthetic structural fixtures. Origin/quality still require serving and A/B gates.
    """
    def field(name):
        require(name in reader.fields, 'missing GGUF metadata: ' + name)
        return reader.fields[name].contents()
    require(field('GGUF.version') == 3 and field('general.file_type') == 15, 'not GGUF v3 Q4_K_M')
    require(config['model_type'] == field('general.architecture') == 'qwen3', 'GGUF architecture differs')
    for key,source in (('block_count','num_hidden_layers'),('embedding_length','hidden_size'),
                       ('feed_forward_length','intermediate_size'),('attention.head_count','num_attention_heads'),
                       ('attention.head_count_kv','num_key_value_heads')):
        require(field('qwen3.' + key) == config[source], 'GGUF dimension differs: ' + key)
    require(field('tokenizer.chat_template') == template, 'GGUF chat template differs')
    tokens = field('tokenizer.ggml.tokens')
    require(len(tokens) == config['vocab_size'] and all(type(i) is int and 0 <= i < len(tokens) and tokens[i] == token for token,i in vocab.items()), 'GGUF vocabulary differs')
    for key,value in special_ids.items():
        if value is not None:require(field('tokenizer.ggml.' + key + '_token_id') == value, 'GGUF special token differs: ' + key)
    hidden,ffn,head = config['hidden_size'],config['intermediate_size'],config['head_dim']
    q,kv = head*config['num_attention_heads'],head*config['num_key_value_heads']
    expected = {'token_embd.weight':[hidden,config['vocab_size']], 'output_norm.weight':[hidden]}
    shapes = {'attn_q':[hidden,q], 'attn_k':[hidden,kv], 'attn_v':[hidden,kv], 'attn_output':[q,hidden],
              'ffn_gate':[hidden,ffn], 'ffn_up':[hidden,ffn], 'ffn_down':[ffn,hidden],
              'attn_norm':[hidden], 'ffn_norm':[hidden], 'attn_q_norm':[head], 'attn_k_norm':[head]}
    for block in range(config['num_hidden_layers']):
        expected.update({f'blk.{block}.{name}.weight':shape for name,shape in shapes.items()})
    if not config.get('tie_word_embeddings') or any(t.name == 'output.weight' for t in reader.tensors):
        expected['output.weight'] = [hidden,config['vocab_size']]
    require(len(reader.tensors) == len(expected) and {t.name for t in reader.tensors} == set(expected), 'GGUF tensor table differs')
    ranges,parameters,q4 = [],0,0
    alignment = int(reader.alignment)
    require(0 < alignment <= 4096 and alignment & (alignment-1) == 0, 'invalid GGUF alignment')
    for tensor in reader.tensors:
        shape = [int(x) for x in tensor.shape]
        require(shape == expected[tensor.name] and int(tensor.n_elements) == math.prod(shape), 'GGUF tensor shape differs: ' + tensor.name)
        kind = int(tensor.tensor_type)
        require(kind in {0,1,12,14,30}, 'unexpected GGUF tensor quantization')
        start,size = int(tensor.data_offset),int(tensor.n_bytes)
        require(size > 0 and start >= reader.data_offset and start % alignment == 0 and start+size <= file_bytes, 'GGUF tensor payload out of bounds')
        ranges.append((start,start+size))
        parameters += int(tensor.n_elements)
        if kind == 12:q4 += int(tensor.n_elements)
    ranges.sort()
    require(all(a[1] <= b[0] for a,b in zip(ranges,ranges[1:])), 'GGUF tensor payloads overlap')
    require(q4 > parameters/2, 'GGUF is not mostly Q4_K')
    return {'architecture':'qwen3', 'tensor_count':len(expected), 'parameters':parameters,
            'tensor_ranges_verified':True, 'tokenizer_template_verified':True, 'general.file_type':15}


def check_contract(root: Path = ROOT, specialist: str = 'frontend-stack') -> dict:
    """Never imports ML libraries or resolves packages; malformed/missing inputs block."""
    report = {'schema_version': 1, 'specialist': specialist, 'status': 'BLOCKED',
              'data_ready': False, 'train_ready': False, 'runtime_compatibility': 'unverified',
              'blockers': [], 'artifact_hashes': {}, 'counts': {}}
    try:
        require(re.fullmatch(r'[a-z0-9-]+', specialist), 'invalid specialist')
        prefix = f'datasets/{specialist}/v2/final/'
        required = list(CONTRACT_FILES) + [prefix + name for name in ('train.jsonl', 'holdout.jsonl', 'train-short3072.jsonl', 'holdout-short3072.jsonl', 'manifest.json')]
        missing = [name for name in required if not safe_path(root, name).is_file()]
        if missing:
            report['blockers'] = ['missing required V2 input: ' + name for name in missing]
            return report
        manifest_path = prefix + 'manifest.json'
        manifest = load_json(root / manifest_path)
        require(manifest.get('schema_version') == 2 and manifest.get('specialist') == specialist, 'invalid final manifest identity')
        artifacts = manifest.get('artifacts', {})
        require(isinstance(artifacts, dict) and artifacts, 'missing artifact bindings')
        require(set(required) - {manifest_path} <= artifacts.keys(), 'manifest does not bind every required input')
        for name, digest in artifacts.items():
            require(isinstance(digest, str) and SHA.fullmatch(digest), f'invalid hash: {name}')
            path = safe_path(root, name)
            require(path.is_file(), f'missing bound artifact: {name}')
            require(sha256(path.read_bytes()) == digest, f'hash mismatch: {name}')
        hashes = dict(artifacts)
        hashes[manifest_path] = sha256((root / manifest_path).read_bytes())
        report['artifact_hashes'] = hashes
        registry = load_json(root / CONTRACT_FILES[0])
        require(registry.get('schema_version') == 2, 'registry is not V2')
        domain = next(s for s in registry['specialists'] if s['id'] == specialist)
        require(domain['eval_state'] == 'frozen' and domain['eval_task_count'] == 20, 'eval not frozen at 20 tasks')
        base = registry['base_model']
        require(base['training_id'] == BASE and base['canonical_id'] == CANONICAL and base['context_tokens'] == 3072 and base['quantization'] == 'Q4_K_M', 'registry base contract drift')
        pin = load_json(root / 'training/templates/qwen3-4b.pin.json')
        base_pin = load_json(root / 'training/templates/qwen3-4b.base-pin.json')
        validate_base_pin(base_pin, pin)
        require(base_pin.get('canonical_pin_sha256') == artifacts['training/templates/qwen3-4b.pin.json'], 'base does not bind exact canonical pin')
        require(artifacts['training/templates/qwen3-4b.jinja'] == pin['template_sha256'], 'canonical template hash drift')
        require(manifest.get('max_tokens') == 3072 and manifest.get('render_options') == pin['render_options'], 'manifest token/render contract drift')
        tools = load_json(root / 'training/pi_tools.json')
        records = manifest.get('records', {})
        require(isinstance(records, dict) and records, 'missing record classification/provenance')
        validation = load_json(safe_path(root, manifest['validation']))
        reviews = load_json(safe_path(root, manifest['reviews']))
        require(manifest['validation'] in artifacts and manifest['reviews'] in artifacts, 'unbound review/validation')
        require(validation.get('schema_version') == 1 and reviews.get('schema_version') == 1, 'invalid evidence schema')
        require(validation.get('checks') == {name: 'passed' for name in CHECKS}, 'validation checks incomplete')
        require(validation.get('source_families_complete') is True, 'source-family coverage not complete')
        split_rows = {split: load_rows(root / (prefix + split + '.jsonl')) for split in ('train', 'holdout')}
        all_rows = split_rows['train'] + split_rows['holdout']
        ids = [row.get('id') for row in all_rows]
        require(len(set(ids)) == len(ids) and set(ids) == set(records), 'duplicate ids or incomplete record provenance')
        observed = Counter()
        split_keys = {}
        for split, rows in split_rows.items():
            keys = set()
            for row in rows:
                ident = row['id']
                metadata = records[ident]
                validate_row(row, metadata, specialist, tools)
                source = row['source']
                if metadata['kind'] == 'gold':
                    require(source['repository'] in domain['sources'], 'unregistered gold source')
                    require(source['license'] == registry['source_repositories'][source['repository']]['license'], 'source license mismatch')
                row_hash = fingerprint(row)
                evidence = validation.get('records', {}).get(ident, {})
                require(evidence.get('sha256') == row_hash and evidence.get('families') == metadata['families'], f'{ident}: validation not bound to exact row/families')
                entries = reviews.get('records', {}).get(ident, [])
                reviewers = set()
                for entry in entries:
                    require(entry.get('record_sha256') == row_hash and entry.get('decision') == 'approved'
                            and entry.get('checks') == {name: 'passed' for name in CHECKS}, f'{ident}: incomplete/stale review')
                    reviewer = entry.get('reviewer')
                    require(isinstance(reviewer, str) and reviewer.strip() and reviewer != metadata['generator'], f'{ident}: reviewer is generator or missing')
                    reviewers.add(reviewer)
                require(len(reviewers) >= 2, f'{ident}: two independent approving reviews required')
                keys |= source_keys(row, metadata)
                keys.add('prompt:' + normalized_prompt(row))
                keys.add('messages:' + sha256(canonical(row['messages']).encode()))
                observed[metadata['kind']] += 1
            split_keys[split] = keys
        require(not split_keys['train'] & split_keys['holdout'], 'train/holdout source-family/commit/prompt/messages overlap')
        for field in ('messages', 'prompt'):
            values = [canonical(row['messages']) if field == 'messages' else normalized_prompt(row) for row in all_rows]
            require(len(set(values)) == len(values), f'duplicate normalized {field}')
        target = domain['target_gold_records'][0]
        require(type(target) is int and target >= 180 and observed['gold'] >= target, 'gold below registry lower bound (at least 180)')
        require(observed['general'] >= 60, 'reviewed general corpus below 60 (gold counted separately)')
        split_counts = validate_split_policy(manifest.get('split_policy'), split_rows, records, target)
        frozen = manifest.get('frozen_eval', [])
        actual_eval = {str(p.relative_to(root)).replace('\\', '/') for p in (root / 'evals/tasks').rglob('*.md')}
        require(actual_eval and {item['path'] for item in frozen} == actual_eval and len(frozen) == len(actual_eval), 'incomplete frozen eval bindings')
        require(validation.get('frozen_eval') == frozen, 'frozen eval identities not independently bound by validation')
        require(set(validation.get('records', {})) == set(ids) and set(reviews.get('records', {})) == set(ids), 'evidence record coverage differs')
        counts = Counter()
        for item in frozen:
            path = item['path']
            require(path in artifacts and path.startswith('evals/tasks/'), 'unbound frozen eval')
            counts[path.split('/')[2]] += 1
            text = safe_path(root, path).read_text(encoding='utf-8')
            require(item['repository'] in registry['source_repositories'], 'unregistered frozen eval repository')
            families = item.get('families')
            require(isinstance(families, list) and families and all(isinstance(x, str) and x for x in families), 'frozen eval missing source families')
            require(not {'family:' + x for x in families} & (split_keys['train'] | split_keys['holdout']), 'frozen eval source-family contamination')
            for field in ('reference', 'start'):
                commit = item[field]
                require(COMMIT.fullmatch(commit), 'eval identity not a full commit')
                # V1 frontend task metadata contains short commit hashes: verify
                # every displayed commit prefix belongs to the frozen identity pair.
                displayed = re.findall(r'(?<![0-9a-f])[0-9a-f]{7,40}(?![0-9a-f])', text)
                in_text = any(commit.startswith(ref) for ref in displayed)
                if field == 'start' and not in_text:
                    # Historical frontend tasks spell parent as reference^ / ~1.
                    parent_refs = re.findall(r'([0-9a-f]{7,40})(?:\^|~1)', text)
                    in_text = any(item['reference'].startswith(ref) for ref in parent_refs)
                require(in_text, f'eval {field} identity missing from task text')
                for row in all_rows:
                    source = row['source']
                    require(not (source.get('repository') == item['repository'] and commit in (source.get('commit'), source.get('parent'))), 'frozen eval commit contamination')
            prompt_match = re.search(r'## Prompt[^\n]*\n(.*?)\n## Success criteria', text, re.S)
            require(prompt_match is not None, 'frozen eval prompt missing')
            eval_prompt = ' '.join(re.findall(r'[a-z0-9_]+', prompt_match[1].lower()))
            require(eval_prompt not in {normalized_prompt(row) for row in all_rows}, 'frozen eval prompt contamination')
        for item in registry['specialists']:
            require(item['eval_state'] == 'frozen' and counts[item['id']] == item['eval_task_count'], 'registry/frozen eval counts drift')
        policy = manifest.get('review_policy', 'human')
        require(policy in ('human', 'independent_ai'), 'unknown spot-check policy')
        ai_review = policy == 'independent_ai'
        require(not ai_review or 'human_spot_check' not in manifest, 'AI review cannot claim a human spot-check')
        spot_check = manifest['ai_spot_check' if ai_review else 'human_spot_check']
        ledger_path = spot_check['ledger']
        require(ledger_path in artifacts, 'unbound review ledger')
        ledger = load_json(safe_path(root, ledger_path))
        required_ids = spot_check.get('required_ids')
        require(isinstance(required_ids, list) and required_ids and set(required_ids) <= set(ids), 'spot-check required_ids missing/invalid')
        require({row['id'] for row in all_rows if row['quality']['judge_score'] == 8} <= set(required_ids),
                'every borderline score-8 record requires an extra review')
        approved = set()
        for entry in ledger.get('entries', []):
            ident = entry['id']
            require(ident in records and entry.get('record_sha256') == fingerprint(next(r for r in all_rows if r['id'] == ident)), 'stale spot-check record binding')
            reviewer = entry.get('reviewer')
            require(isinstance(reviewer, str) and reviewer.strip()
                    and reviewer != records[ident]['generator']
                    and isinstance(entry.get('approved_at'), str) and entry['approved_at'].strip()
                    and isinstance(entry.get('notes'), str) and entry['notes'].strip(), 'missing spot-check identity/time/notes')
            if ai_review:
                require(entry.get('decision') == 'ai_approved' and entry.get('actor_type') == 'ai'
                        and reviewer not in {r['reviewer'] for r in reviews['records'][ident]},
                        'AI spot-check must be distinct from generator and two row reviewers')
                evidence_path = entry.get('evidence_path')
                require(isinstance(evidence_path, str) and evidence_path in artifacts,
                        'AI spot-check review evidence is not hash-bound')
                evidence = load_json(safe_path(root, evidence_path))
                findings = evidence.get('findings')
                require(evidence.get('reviewer') == reviewer and evidence.get('record_sha256') == entry['record_sha256']
                        and evidence.get('decision') == 'approved' and isinstance(findings, list)
                        and findings and all(isinstance(f, str) and len(f.strip()) >= 40 for f in findings)
                        and evidence.get('checks') == {name: 'passed' for name in CHECKS},
                        'AI spot-check evidence lacks row-specific findings or complete checks')
            else:
                require(entry.get('decision') == 'human_approved' and entry.get('actor_type') == 'human',
                        'missing actual declared human approval')
            datetime.fromisoformat(entry['approved_at'].replace('Z', '+00:00'))
            require(ident not in approved, 'duplicate spot-check approval id')
            approved.add(ident)
        require(set(required_ids) <= approved, ('AI' if ai_review else 'human') + ' spot-check incomplete')
        require({records[x]['kind'] for x in approved} == {'gold', 'general'}, 'spot-check must cover gold and general separately')
        require(all(row['quality']['review_state'] != 'human_approved' or (not ai_review and row['id'] in approved)
                    for row in all_rows), 'fabricated/unbound human_approved state')
        bounded_counts = Counter()
        bounded_splits = {}
        for split, rows in split_rows.items():
            bounded = load_rows(root / (prefix + split + '-short3072.jsonl'))
            bounded_splits[split] = bounded
            original = {row['id']: fingerprint(row) for row in rows}
            require(len({row['id'] for row in bounded}) == len(bounded), 'duplicate bounded id')
            require(all(original.get(row['id']) == fingerprint(row) for row in bounded), 'bounded split modifies/reassigns whole records')
            if split == 'holdout':
                require(len(bounded) == len(rows), 'holdout must remain complete; no filtering or truncation')
            for row in bounded:
                bounded_counts[records[row['id']]['kind']] += 1
        require(bounded_counts['gold'] >= target and bounded_counts['general'] >= 60, 'bounded corpus below gold/general minimum')
        bounded_split_counts = validate_split_policy(manifest.get('split_policy'), bounded_splits, records, target)
        report.update(status='DATA_READY_RUNTIME_PROVISIONAL', data_ready=True,
                      counts={'final': dict(observed), 'bounded': dict(bounded_counts),
                              'splits':split_counts, 'bounded_splits':bounded_split_counts},
                      contract_sha256=sha256(canonical(hashes).encode()),
                      limitation='Requires Colab package/GPU preflight and isolated optimizer probe; never a runtime readiness waiver.')
    except (OSError, ValueError, KeyError, TypeError, StopIteration, AttributeError, SystemExit) as exc:
        report['blockers'].append(str(exc) or type(exc).__name__)
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=ROOT)
    parser.add_argument('--specialist', default='frontend-stack')
    args = parser.parse_args()
    report = check_contract(args.root, args.specialist)
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if report['data_ready'] else 2


if __name__ == '__main__':
    raise SystemExit(main())
