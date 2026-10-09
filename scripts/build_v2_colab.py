"""Deterministic, self-contained 4B Colab builder; missing V2 inputs emit zero payload.

python scripts/build_v2_colab.py [--check]
The checked-in notebook is intentionally BLOCKED until a real final V2 corpus,
independent reviews, the declared review-policy ledger, frozen evals and base pin satisfy v2_training_contract.
Neither this generator nor its model-free gate imports torch or downloads weights.
"""
from __future__ import annotations

import argparse
import base64
import io
import json
import zipfile
from pathlib import Path

try:
    from .v2_training_contract import ROOT, canonical, check_contract, sha256
except ImportError:
    from v2_training_contract import ROOT, canonical, check_contract, sha256

NOTEBOOK = 'notebooks/frontend_stack_qwen3_4b_colab.ipynb'
HELPERS = ('scripts/v2_training_contract.py', 'scripts/build_short_train.py')

# This program runs only in fresh Colab subprocesses after the model-free gate.
# Probe and training never share a mutated model/optimizer or Python process.
RUNTIME = r'''import argparse, hashlib, importlib.metadata, importlib.util, json, os, platform, shutil, struct, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent / 'scripts'))
from v2_training_contract import (check_contract, load_json, load_rows, canonical, sha256,
    require, assistant_labels, BASE, REVISION, CANONICAL, CANONICAL_REVISION, TOKENIZER_FILES,
    validate_probe_evidence, checkpoint_hashes, validate_checkpoint, validate_gguf_reader, file_sha256,
    discover_gguf_exports)


def gguf_type(path):
    # Parse GGUF v3 metadata, not the filename. GGML_FTYPE_MOSTLY_Q4_K_M = 15.
    with path.open('rb') as stream:
        def read(fmt):
            size = struct.calcsize(fmt)
            data = stream.read(size)
            require(len(data) == size, 'truncated GGUF')
            return struct.unpack(fmt, data)[0]
        def string():
            size = read('<Q')
            require(size <= 2**24, 'unreasonable GGUF string')
            data = stream.read(size)
            require(len(data) == size, 'truncated GGUF string')
            return data.decode('utf-8')
        def value(kind, depth=0):
            require(depth < 4, 'invalid GGUF nesting')
            formats = {0:'<B', 1:'<b', 2:'<H', 3:'<h', 4:'<I', 5:'<i', 6:'<f', 7:'<?', 10:'<Q', 11:'<q', 12:'<d'}
            if kind in formats: return read(formats[kind])
            if kind == 8: return string()
            if kind == 9:
                subtype, count = read('<I'), read('<Q')
                require(count <= 10**7, 'invalid GGUF array length')
                for _ in range(count): value(subtype, depth + 1)
                return None
            raise RuntimeError('unknown GGUF metadata type')
        require(stream.read(4) == b'GGUF' and read('<I') == 3, 'not GGUF v3')
        tensors, count = read('<Q'), read('<Q')
        require(tensors > 0 and count < 10**6, 'invalid GGUF counts')
        file_type = None
        for _ in range(count):
            key, kind = string(), read('<I')
            result = value(kind)
            if key == 'general.file_type': file_type = result
        require(file_type == 15, 'export is not Q4_K_M (general.file_type != 15)')
        return file_type


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--mode', choices=('probe', 'train'), required=True)
    ap.add_argument('--resume')
    args = ap.parse_args()
    resume_from_checkpoint = None
    root = Path(__file__).resolve().parent
    report = check_contract(root)
    require(report['data_ready'], 'BLOCKED before ML imports: ' + canonical(report['blockers']))
    require(platform.system() == 'Linux' and Path('/content').is_dir()
            and importlib.util.find_spec('google.colab') is not None, 'Colab only; local GPU training prohibited')
    require(shutil.disk_usage(root).free >= 25 * 1024**3, 'need 25 GiB free disk before base download')
    os.environ['UNSLOTH_CE_LOSS_TARGET_GB'] = '0.05'
    os.environ['UNSLOTH_DISABLE_DOUBLE_BUFFER'] = '1'
    # Unsloth patch ordering is significant.
    import unsloth
    import torch
    from unsloth import FastLanguageModel, is_bfloat16_supported
    from datasets import Dataset
    from transformers import AutoTokenizer, TrainerCallback
    from huggingface_hub import snapshot_download
    from trl import SFTTrainer, SFTConfig
    from importlib.metadata import version
    requirements = (root / 'training/requirements-v2-colab.txt').read_text().splitlines()
    expected = dict(line.strip().split('==') for line in requirements if line.strip() and not line.startswith('#'))
    packages = {name: version(name) for name in expected}
    require(packages == expected, 'installed direct package pins differ')
    require(torch.cuda.is_available(), 'CUDA unavailable')
    gpu = torch.cuda.get_device_properties(0)
    free, total = torch.cuda.mem_get_info()
    require(any(name in gpu.name for name in ('T4', 'L4', 'A100')) and total >= 14.5 * 1024**3
            and free >= 13 * 1024**3, 'need clean T4/L4/A100 with >=13 GiB free VRAM')
    runtime = {'python': platform.python_version(), 'packages': packages,
               'torch': torch.__version__, 'cuda': torch.version.cuda,
               'triton': version('triton'), 'gpu': gpu.name, 'vram_bytes': total,
               'installed_distributions':dict(sorted((dist.metadata['Name'],dist.version)
                   for dist in importlib.metadata.distributions() if dist.metadata['Name']))}
    params = {'rank':16, 'alpha':32, 'dropout':0, 'max_seq_length':3072,
              'epochs':2, 'batch':1, 'accumulation':16, 'lr':2e-4,
              'seed':3407, 'optimizer':'paged_adamw_8bit', 'assistant_only':True,
              'packing':False, 'base':BASE, 'revision':REVISION,
              'targets':['q_proj','k_proj','v_proj','o_proj','gate_proj','up_proj','down_proj']}
    run_contract = {'data_contract': report['contract_sha256'], 'runtime':runtime, 'parameters':params,
                    'runtime_program_sha256':sha256(Path(__file__).read_bytes()),
                    'helper_sha256':{name:sha256((root / 'scripts' / name).read_bytes())
                                     for name in ('v2_training_contract.py','build_short_train.py')}}
    run_hash = sha256(canonical(run_contract).encode())
    out = root / 'outputs'
    out.mkdir(exist_ok=True)
    contract_file = out / 'run-contract.json'
    if args.mode == 'train':
        probe = load_json(out / 'probe.json')
        require(probe.get('run_sha256') == run_hash and probe.get('passed') is True, 'real isolated probe missing/stale; no waiver')
        validate_probe_evidence(probe)
        if contract_file.exists():
            require(load_json(contract_file) == run_contract, 'existing run contract differs')
        contract_file.write_text(canonical(run_contract))
        if args.resume:
            checkpoint = Path(args.resume).resolve()
            require(checkpoint.parent == (out / 'trainer').resolve() and checkpoint.name.startswith('checkpoint-'), 'invalid resume path')
            validate_checkpoint(checkpoint, run_contract)
            resume_from_checkpoint = str(checkpoint)
        else:
            require(not list((out / 'trainer').glob('checkpoint-*')) and not (out / 'holdout-evaluation.json').exists(), 'existing run requires explicit checkpoint resume or a fresh runtime')
    else:
        require(not args.resume, 'probe cannot resume')
        (out / 'probe.json').unlink(missing_ok=True)

    # Download/verify only tokenizer metadata first; base weights come later.
    pin = load_json(root / 'training/templates/qwen3-4b.pin.json')
    base_pin = load_json(root / 'training/templates/qwen3-4b.base-pin.json')
    native_path = Path(snapshot_download(BASE, revision=REVISION,
                       allow_patterns=list(TOKENIZER_FILES) + ['config.json', 'special_tokens_map.json']))
    canonical_path = Path(snapshot_download(CANONICAL, revision=CANONICAL_REVISION,
                          allow_patterns=list(TOKENIZER_FILES) + ['config.json', 'special_tokens_map.json']))
    canonical_hashes = dict(pin['tokenizer_files'], **{'merges.txt':pin['merges_sha256']})
    for folder, hashes in ((native_path, base_pin['native_tokenizer_files']), (canonical_path, canonical_hashes)):
        for name, digest in hashes.items():
            require(sha256((folder / name).read_bytes()) == digest, 'tokenizer file drift: ' + name)
    model_config = load_json(native_path / 'config.json')
    native_config = load_json(native_path / 'tokenizer_config.json')
    require(sha256(native_config['chat_template'].encode()) == base_pin['native_template_sha256'], 'native template drift before normalization')
    native = AutoTokenizer.from_pretrained(str(native_path), local_files_only=True)
    canonical_tokenizer = AutoTokenizer.from_pretrained(str(canonical_path), local_files_only=True)
    native_pad = native.pad_token
    normalization = base_pin['normalization']
    require(native_pad == normalization['native_pad_token'] and native.pad_token_id == normalization['native_pad_token_id'], 'native pad drift')
    require(canonical_tokenizer.pad_token == normalization['canonical_pad_token']
            and canonical_tokenizer.pad_token_id == normalization['canonical_pad_token_id'], 'canonical pad drift')
    template = (root / 'training/templates/qwen3-4b.jinja').read_text(encoding='utf-8')
    require(sha256(template.encode()) == pin['template_sha256'], 'canonical template drift')
    # Only the documented verified normalization is allowed. Do not replace pad.
    native.chat_template = template
    canonical_tokenizer.chat_template = template
    prefix = root / 'datasets/frontend-stack/v2/final'
    rows = {split:load_rows(prefix / (split + '-short3072.jsonl')) for split in ('train', 'holdout')}
    token_data, lengths = {}, {}
    for split, records in rows.items():
        processed, counts = [], []
        for row in records:
            for msg in row['messages']:
                require(not any(marker in canonical(msg) for marker in ('<|im_start|>', '<|im_end|>')), 'turn-marker injection in source record')
            options = dict(tools=row.get('tools') or None, tokenize=False,
                           add_generation_prompt=False, enable_thinking=False)
            text = native.apply_chat_template(row['messages'], **options)
            canonical_text = canonical_tokenizer.apply_chat_template(row['messages'], **options)
            encoded = native(text, add_special_tokens=False, return_offsets_mapping=True)
            ids = encoded['input_ids']
            require(ids == canonical_tokenizer(canonical_text, add_special_tokens=False)['input_ids'], 'unpadded token parity failure')
            require(text.strip() and 0 < len(ids) <= 3072, 'whole record over cap; no slicing/truncation/fallback')
            require(not row.get('tools') or '<tools>' in text, 'missing tool definitions')
            # Locate complete template assistant spans. Tool results render as user
            # spans. Keep assistant tool-call JSON AND turn-ending tokens as labels.
            expected_calls = sum(len(m.get('tool_calls') or []) for m in row['messages'])
            labels = assistant_labels(text, ids, encoded['offset_mapping'], expected_calls)
            processed.append({'input_ids':ids, 'attention_mask':[1]*len(ids), 'labels':labels})
            counts.append(len(ids))
        token_data[split], lengths[split] = processed, counts
    (out / ('probe-token-bounds.json' if args.mode == 'probe' else 'token-bounds.json')).write_text(canonical({
        split:{'records':len(values),'min':min(values),'max':max(values)} for split,values in lengths.items()}))

    model, tokenizer = FastLanguageModel.from_pretrained(model_name=BASE, revision=REVISION,
                    max_seq_length=3072, load_in_4bit=True)
    require(tokenizer.get_vocab() == native.get_vocab(), 'loaded base tokenizer vocabulary drift')
    require(tokenizer.pad_token == native_pad and tokenizer.pad_token_id == normalization['native_pad_token_id'], 'loader changed native pad; refuse repair')
    # Loader-specific templates are not trusted; raw native metadata was verified
    # above and the sole approved canonical-template normalization is explicit.
    tokenizer.chat_template = template
    require(all(tokenizer(native.apply_chat_template(row['messages'], tools=row.get('tools') or None,
        tokenize=False, add_generation_prompt=False, enable_thinking=False), add_special_tokens=False)['input_ids']
        == item['input_ids'] for split in rows for row,item in zip(rows[split],token_data[split])), 'loaded tokenizer token drift')
    model = FastLanguageModel.get_peft_model(model, r=16, lora_alpha=32, lora_dropout=0,
                    bias='none', target_modules=params['targets'], use_gradient_checkpointing='unsloth',
                    random_state=3407, use_rslora=False, loftq_config=None)
    # Custom token collator avoids TRL text-field/EOS insertion or hidden truncation.
    def collate(batch):
        width = max(len(item['input_ids']) for item in batch)
        return {key:torch.tensor([item[key] + [fill]*(width-len(item[key])) for item in batch], dtype=torch.long)
                for key,fill in (('input_ids',tokenizer.pad_token_id),('attention_mask',0),('labels',-100))}
    class BindCheckpoint(TrainerCallback):
        def on_save(self, args, state, control, **kwargs):
            path = Path(args.output_dir) / ('checkpoint-' + str(state.global_step))
            (path / 'run-contract.json').write_text(canonical(run_contract))
            (path / 'checkpoint-hashes.json').write_text(canonical(checkpoint_hashes(path)))
    probing = args.mode == 'probe'
    probe_evidence = {'optimizer_attempts':0}
    class ObserveProbe(TrainerCallback):
        def on_pre_optimizer_step(self, args, state, control, **kwargs):
            grads = [p.grad for p in kwargs['model'].parameters() if p.requires_grad and p.grad is not None]
            probe_evidence.update(optimizer_attempts=probe_evidence['optimizer_attempts']+1,
                gradient_finite=bool(grads) and all(bool(torch.isfinite(g).all()) for g in grads),
                gradient_nonzero=any(bool(torch.any(g != 0)) for g in grads),
                learning_rate=float(kwargs['optimizer'].param_groups[0]['lr']))
    if probing:
        probe_name,probe_tensor = next((name,p) for name,p in model.named_parameters() if p.requires_grad and 'lora_B' in name)
        probe_before = probe_tensor.detach().float().cpu().clone()
    train_data = token_data['train']
    if probing:
        longest = max(range(len(train_data)), key=lambda i:len(train_data[i]['input_ids']))
        train_data = [train_data[longest]]
    trainer = SFTTrainer(model=model, processing_class=tokenizer,
        train_dataset=Dataset.from_list(train_data),
        eval_dataset=None if probing else Dataset.from_list(token_data['holdout']),
        data_collator=collate, callbacks=[ObserveProbe()] if probing else [BindCheckpoint()],
        args=SFTConfig(output_dir=str(out / ('probe-trainer' if probing else 'trainer')),
            per_device_train_batch_size=1, per_device_eval_batch_size=1,
            gradient_accumulation_steps=1 if probing else 16,
            num_train_epochs=2, max_steps=1 if probing else -1,
            learning_rate=2e-4, warmup_ratio=0 if probing else 0.05,
            lr_scheduler_type='constant' if probing else 'cosine',
            optim='paged_adamw_8bit', fp16=not is_bfloat16_supported(), bf16=is_bfloat16_supported(),
            logging_steps=1, save_strategy='no' if probing else 'steps', save_steps=10, save_total_limit=2,
            eval_strategy='no' if probing else 'epoch', seed=3407, report_to='none',
            max_length=3072, packing=False, dataset_kwargs={'skip_prepare_dataset':True},
            remove_unused_columns=False))
    for prepared, original in zip(trainer.train_dataset, train_data):
        require(prepared['input_ids'] == original['input_ids'] and prepared['labels'] == original['labels'], 'trainer changed token bounds or assistant-only labels')
    require(len(trainer.train_dataset) == len(train_data), 'trainer changed train record count')
    if not probing:
        require(len(trainer.eval_dataset) == len(token_data['holdout']), 'trainer changed holdout count')
        for prepared, original in zip(trainer.eval_dataset, token_data['holdout']):
            require(prepared['input_ids'] == original['input_ids'] and prepared['labels'] == original['labels'], 'trainer changed frozen holdout')
    train_result = trainer.train(resume_from_checkpoint=resume_from_checkpoint)
    if probing:
        require(trainer.state.global_step == 1, 'probe did not complete one optimizer step')
        skipped_update = bool(trainer.accelerator.optimizer_step_was_skipped)
        probe_after = dict(model.named_parameters())[probe_name].detach().float().cpu()
        longest_holdout = max(range(len(token_data['holdout'])), key=lambda i:len(token_data['holdout'][i]['input_ids']))
        holdout_probe = trainer.evaluate(eval_dataset=Dataset.from_list([token_data['holdout'][longest_holdout]]))
        import math
        holdout_loss = holdout_probe.get('eval_loss')
        probe_evidence.update(optimizer_steps=trainer.state.global_step,
            optimizer_step_was_skipped=skipped_update,
            loss=float(train_result.training_loss),
            adapter_finite=all(bool(torch.isfinite(p).all()) for p in model.parameters() if p.requires_grad),
            adapter_change_max=float((probe_after-probe_before).abs().max()),
            longest_holdout_passed=type(holdout_loss) in (int,float) and math.isfinite(holdout_loss))
        validate_probe_evidence(probe_evidence)
        (out / 'probe.json').write_text(canonical(dict(probe_evidence,run_sha256=run_hash,run_contract=run_contract,
            passed=True,longest_train_tokens=max(lengths['train']),longest_holdout_tokens=max(lengths['holdout']),
            training_row_index=longest,holdout_row_index=longest_holdout,max_vram_bytes=torch.cuda.max_memory_allocated())))
        # Process exit is the isolation barrier. No probe adapter is reused.
        return
    metrics = trainer.evaluate()
    import math
    require(isinstance(metrics.get('eval_loss'), (int,float)) and math.isfinite(metrics['eval_loss']), 'invalid final holdout loss')
    (out / 'holdout-evaluation.json').write_text(canonical({'run_sha256':run_hash,'metrics':metrics,
        'note':'Frozen final holdout loss; not a frozen repository-task A/B gate or release approval.'}))
    model.save_pretrained(str(out / 'adapter'))
    tokenizer.save_pretrained(str(out / 'adapter'))
    require(shutil.disk_usage(root).free >= 20*1024**3, 'need 20 GiB free before merge/export')
    requested = out / 'gguf'
    sibling = requested.with_name(requested.name + '_gguf')
    require(not requested.exists() and not sibling.exists(), 'existing export directories preserved; use a fresh runtime')
    previous = {p.resolve() for p in out.rglob('*.gguf')}
    export_result = model.save_pretrained_gguf(str(requested), tokenizer, quantization_method='q4_k_m')
    require(version('gguf') == expected['gguf'], 'conversion changed the pinned GGUF reader')
    artifacts = discover_gguf_exports(requested,out,export_result,previous)
    quantized = []
    for artifact in artifacts:
        # Unsloth may leave an intermediate F16 GGUF. Only release Q4_K_M.
        try:
            gguf_type(artifact)  # Header selection only; never an identity certificate.
            from gguf import GGUFReader
            verification = validate_gguf_reader(GGUFReader(str(artifact)),artifact.stat().st_size,
                model_config,tokenizer.get_vocab(),template,
                {'padding':tokenizer.pad_token_id,'eos':tokenizer.eos_token_id,'bos':tokenizer.bos_token_id})
        except (ValueError, RuntimeError, IndexError, OverflowError): continue
        quantized.append((artifact,verification))
    require(len(quantized) == 1, 'need exactly one fully parsed/identity-checked Q4_K_M GGUF')
    artifact,verification = quantized[0]
    digest = file_sha256(artifact)
    require(artifact.stat().st_size > 1024**3, 'implausibly small 4B GGUF')
    (out / 'artifact.json').write_text(canonical({'file':str(artifact.relative_to(root)),
        'bytes':artifact.stat().st_size, 'sha256':digest, 'magic':'GGUF', 'verification':verification,
        'general.file_type':15,'quantization':'Q4_K_M','run_sha256':run_hash,
        'template_sha256':pin['template_sha256'],'base':BASE,'revision':REVISION,
        'expected_export_identity':CANONICAL,'canonical_revision':CANONICAL_REVISION,
        'release_ready':False,'limitations':'Conversion toolchain is provisional; independently verify serving template, smoke suite and frozen A/B gate.'}))
    print('Export recorded; no automatic download, publication or release approval.')

if __name__ == '__main__': main()
'''


def cell(kind, source, ident):
    result = {'id': ident, 'cell_type': kind, 'metadata': {'id': ident}, 'source': source.splitlines(keepends=True)}
    if kind == 'code':
        result.update(execution_count=None, outputs=[])
    return result


def payload(root, report):
    if not report['data_ready']:
        return '', {}
    names = sorted(set(report['artifact_hashes']) | set(HELPERS))
    hashes = {name: sha256((root / name).read_bytes()) for name in names}
    stream = io.BytesIO()
    with zipfile.ZipFile(stream, 'w', compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for name in names:
            info = zipfile.ZipInfo(name, (1980, 1, 1, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o100644 << 16
            archive.writestr(info, (root / name).read_bytes())
    return base64.b64encode(stream.getvalue()).decode('ascii'), hashes


def build_notebook(root=ROOT):
    report = check_contract(root)
    encoded, hashes = payload(root, report)
    blockers = '\n'.join(f'- {reason}' for reason in report['blockers'])
    readiness = ('Blocked inputs (local contract):\n' + blockers if blockers else
                 'Local reviewed-data contract passed; the Colab GPU optimizer probe has not run.')
    title = f'''# Frontend V2 — pinned Qwen3-4B QLoRA

**Build status: {report['status']}.** Training/runtime compatibility remains provisional.
{'UPLOADABLE PREVIEW — NOT TRAINABLE. Zero approved data are embedded. Do not select a GPU or Run all yet.' if not encoded else 'Self-contained reviewed-data notebook; upload this single .ipynb to Colab.'}
{readiness}

To prepare a trainable export **on your own computer**, supply reviewed final V2 inputs
(180 approved gold and 60 separately reviewed general rows), then run
`py -3 scripts/v2_training_contract.py` and `py -3 scripts/build_v2_colab.py`.
The first command must exit 0, and the regenerated notebook must embed a nonempty
hash-bound payload. Upload `notebooks/frontend_stack_qwen3_4b_colab.ipynb` via
Colab **File → Upload notebook**. Only then choose a T4/L4/A100 GPU and Run all.
No V1 data fallback. Never edit the status flag to bypass a gate. The first code
cell rechecks the full restored contract before pip, torch or weight downloads.

Recipe: 3,072 whole-record tokens, rank 16, assistant-only labels (including tool
calls), two epochs, separate non-skipped/nonzero longest-training-record update
plus longest-holdout memory/finite-loss probe, clean-base reload, final holdout loss,
content-bound checkpoints, full Q4_K_M tensor/tokenizer/template validation.
No implicit 2,048 fallback: rebuild/review/re-pin derivatives first.
Package pins come from the archived repository recipe; 4B compatibility has not
been tested. A real clean Colab GPU optimizer probe is mandatory, not a waiver.
Export is provisional until independent serving smoke and frozen A/B gates pass.
Spot-check approval must use the declared human or independent-AI policy, never an invented human. File hashes cannot establish reviewer identity.
'''
    restore = f'''# Model-free gate FIRST. Executing later cells out of order also fails closed.
import base64, hashlib, io, json, platform, shutil, sys, zipfile
from pathlib import Path, PurePosixPath
BUILD_REPORT = json.loads({canonical(canonical(report))})
PAYLOAD_B64 = {encoded!r}
PAYLOAD_HASHES = {hashes!r}
READY = False
if not BUILD_REPORT['data_ready'] or not PAYLOAD_B64:
    print('NOT TRAINABLE: regenerate locally after the approved V2 corpus passes its contract.')
    raise RuntimeError('BLOCKED: ' + json.dumps(BUILD_REPORT['blockers']))
if platform.system() != 'Linux' or not Path('/content').is_dir():
    raise RuntimeError('Colab GPU only; no local training')
from google.colab import files
if shutil.disk_usage('/content').free < 25 * 1024**3:
    raise RuntimeError('Need at least 25 GiB free disk')
WORK = Path('/content/Master-Models-V2')
raw = base64.b64decode(PAYLOAD_B64, validate=True)
with zipfile.ZipFile(io.BytesIO(raw)) as archive:
    if len(archive.namelist()) != len(PAYLOAD_HASHES) or set(archive.namelist()) != set(PAYLOAD_HASHES):
        raise RuntimeError('Payload membership mismatch')
    for name in archive.namelist():
        parts = PurePosixPath(name)
        if parts.is_absolute() or '..' in parts.parts or '\\\\' in name or ':' in name:
            raise RuntimeError('Unsafe payload path')
        data = archive.read(name)
        if hashlib.sha256(data).hexdigest() != PAYLOAD_HASHES[name]:
            raise RuntimeError('Payload hash mismatch: ' + name)
        target = WORK / name
        if not target.resolve().is_relative_to(WORK.resolve()): raise RuntimeError('Payload escapes root')
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(data)
sys.path.insert(0, str(WORK / 'scripts'))
from v2_training_contract import check_contract
REPORT = check_contract(WORK)
if not REPORT['data_ready'] or REPORT['contract_sha256'] != BUILD_REPORT['contract_sha256']:
    raise RuntimeError('Restored contract failed: ' + json.dumps(REPORT))
READY = True
print('Data validated. Runtime readiness still unverified.')
'''
    install = '''if not globals().get('READY', False): raise RuntimeError('BLOCKED before pip')
if not check_contract(WORK)['data_ready']: raise RuntimeError('Inputs changed before pip')
import subprocess
subprocess.run([sys.executable, '-m', 'pip', 'install', '--no-cache-dir', '-r',
                str(WORK / 'training/requirements-v2-colab.txt')], check=True)
subprocess.run([sys.executable, '-m', 'pip', 'check'], check=True)
print('Packages installed; compatibility is not established until the real probe passes.')
'''
    runtime = f'''if not globals().get('READY', False): raise RuntimeError('BLOCKED before runtime setup')
RUNTIME_SOURCE = {RUNTIME!r}
(WORK / 'v2_runtime.py').write_text(RUNTIME_SOURCE, encoding='utf-8')
'''
    probe = '''if not globals().get('READY', False): raise RuntimeError('BLOCKED before probe')
# A subprocess owns the probe model; process exit discards its updated adapter.
subprocess.run([sys.executable, str(WORK / 'v2_runtime.py'), '--mode', 'probe'], check=True)
print((WORK / 'outputs/probe.json').read_text())
'''
    train = '''if not globals().get('READY', False): raise RuntimeError('BLOCKED before training')
# Explicit checkpoint path only. Copy the entire outputs directory when persisting
# to Drive, including run-contract.json, probe.json and checkpoint contracts.
RESUME_FROM_CHECKPOINT = None
command = [sys.executable, str(WORK / 'v2_runtime.py'), '--mode', 'train']
if RESUME_FROM_CHECKPOINT: command += ['--resume', RESUME_FROM_CHECKPOINT]
subprocess.run(command, check=True)
print((WORK / 'outputs/holdout-evaluation.json').read_text())
print((WORK / 'outputs/artifact.json').read_text())
'''
    return {'cells': [cell('markdown', title, 'overview'), cell('code', restore, 'gate'),
                     cell('code', install, 'install'), cell('code', runtime, 'runtime-source'),
                     cell('code', probe, 'isolated-probe'), cell('code', train, 'train-export'),
                     cell('markdown', 'In Colab, save `outputs/` (including probe.json, checkpoints, adapter, artifact.json and the GGUF) before the runtime expires; the Files pane supports downloads, and large GGUF files may need Drive or the official CLI. No automatic account access or export download occurs.\nExport is not release approval. Independently verify the serving template, 10/10 smoke suite and stock-versus-specialist frozen repository gate.\n', 'qualification')],
            'metadata': {'colab': {'provenance': [], 'name': 'Frontend Qwen3-4B — ' + report['status']}, 'kernelspec': {'display_name': 'Python 3', 'name': 'python3'},
                         'language_info': {'name': 'python'}, 'v2_readiness': report,
                         'v2_payload_file_count': len(hashes)}, 'nbformat': 4, 'nbformat_minor': 5}


def notebook_text(root=ROOT):
    return json.dumps(build_notebook(root), ensure_ascii=False, indent=1, sort_keys=True) + '\n'


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=ROOT)
    parser.add_argument('--check', action='store_true')
    args = parser.parse_args()
    target = args.root / NOTEBOOK
    text = notebook_text(args.root)
    if args.check:
        if not target.is_file() or target.read_text(encoding='utf-8') != text:
            raise SystemExit('notebook stale; run scripts/build_v2_colab.py')
        print('deterministic notebook matches generator')
    else:
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(text, encoding='utf-8', newline='\n')
        print(f'wrote {NOTEBOOK}; {check_contract(args.root)["status"]}')


if __name__ == '__main__':
    main()
