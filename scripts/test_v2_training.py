"""Dependency-free tests. All temporary rows/evidence are SYNTHETIC TEST FIXTURES.

python -m unittest scripts.test_v2_training -v
No model libraries, downloads, training, or real corpus promotion.
"""
from __future__ import annotations

import ast
import base64
import io
import json
import struct
import tempfile
import unittest
import zipfile
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock, patch

from scripts import build_v2_colab as builder
from scripts import v2_training_contract as contract

PREFIX = 'datasets/frontend-stack/v2/final/'


class V2TrainingTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='synthetic-v2-test-')
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)

    def write(self, name, obj, lines=False):
        path = self.root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        if lines:
            text = ''.join(contract.canonical(row) + '\n' for row in obj)
        elif isinstance(obj, str):
            text = obj
        else:
            text = contract.canonical(obj)
        path.write_text(text, encoding='utf-8', newline='\n')

    def read(self, name):
        return contract.load_json(self.root / name)

    def bind(self, name):
        manifest = self.read(PREFIX + 'manifest.json')
        manifest['artifacts'][name] = contract.sha256((self.root / name).read_bytes())
        self.write(PREFIX + 'manifest.json', manifest)

    def mutate(self, name, callback):
        value = self.read(name)
        callback(value)
        self.write(name, value)
        self.bind(name)

    def fixture(self):
        """Invented artifacts exist only in this disposable temp directory."""
        files = {}
        registry = {'schema_version':2, 'base_model':{
            'training_id':contract.BASE,'canonical_id':contract.CANONICAL,
            'context_tokens':3072,'quantization':'Q4_K_M'},
            'source_repositories':{'synthetic':{'path':'SYNTHETIC-NOT-A-REPOSITORY','license':'SYNTHETIC-TEST'}},
            'specialists':[{'id':'frontend-stack','eval_state':'frozen','eval_task_count':20,
                            'target_gold_records':[180,220],'sources':['synthetic']}]}
        files['datasets/v2-registry.json'] = registry
        tools = [{'type':'function','function':{'name':'bash','parameters':{'type':'object','properties':{'command':{'type':'string'}}}}}]
        files['training/pi_tools.json'] = tools
        template = 'SYNTHETIC TEST TEMPLATE ONLY\n'
        files['training/templates/qwen3-4b.jinja'] = template
        files['training/requirements-v2-colab.txt'] = '# SYNTHETIC TEST ONLY\n'
        token_hashes = {name:contract.sha256(('SYNTHETIC ' + name).encode()) for name in contract.TOKENIZER_FILES | {'config.json','special_tokens_map.json'}}
        files['training/templates/qwen3-4b.pin.json'] = {
            'model':contract.CANONICAL,'revision':contract.CANONICAL_REVISION,
            'template_sha256':contract.sha256(template.encode()),
            'tokenizer_files':{name:digest for name,digest in token_hashes.items() if name in contract.TOKENIZER_FILES - {'merges.txt'}}, 
            'merges_sha256':token_hashes['merges.txt'],
            'render_options':{'enable_thinking':False,'add_generation_prompt':False}}
        files['training/templates/qwen3-4b.base-pin.json'] = {
            'schema_version':1,'model':contract.BASE,'revision':contract.REVISION,
            'canonical_model':contract.CANONICAL,'canonical_revision':contract.CANONICAL_REVISION,
            'canonical_pin_sha256':contract.sha256(contract.canonical(files['training/templates/qwen3-4b.pin.json']).encode()),
            'template_sha256':contract.sha256(template.encode()),
            'native_template_sha256':contract.sha256(b'SYNTHETIC NATIVE TEMPLATE'),
            'native_tokenizer_files':token_hashes,
            'backend_files':{name:token_hashes[name] for name in ('tokenizer.json','vocab.json','merges.txt')},
            'parity_verified':True,'weights_downloaded':False,'training_eligible':False,
            'normalization':{'chat_template':'SYNTHETIC canonical normalization, NOT REAL PARITY',
                'native_pad_token':'<|vision_pad|>','native_pad_token_id':151654,
                'canonical_pad_token':'<|endoftext|>','canonical_pad_token_id':151643,
                'render_options':{'enable_thinking':False,'add_generation_prompt':False}}}
        records, reviews, validation_rows, splits = {}, {}, {}, {'train':[],'holdout':[]}
        for number in range(250):
            kind = 'gold' if number < 185 else 'general'
            split = 'holdout' if number in (*range(176,185),247,248,249) else 'train'
            ident = f'frontend-stack:synthetic-{number}'
            source = {'license':'SYNTHETIC-TEST'}
            if kind == 'gold':
                source.update(repository='synthetic',commit=f'{number*3+1:040x}',
                              parent=f'{number*3+2:040x}',files=['SYNTHETIC.tsx'])
            else:
                source['identity'] = f'SYNTHETIC-GENERAL-{number}'
            row = {'id':ident,'schema_version':2,'specialist':'frontend-stack' if kind == 'gold' else 'general',
                'source':source,'tools':tools,'quality':{'review_state':'judge_passed','judge_score':9,
                    'difficulty':'medium','skills':['SYNTHETIC-TEST-SKILL'],
                    'verification_commands':['SYNTHETIC CHECK']},
                'messages':[{'role':'user','content':f'SYNTHETIC task {number} never a real trajectory'},
                    {'role':'assistant','tool_calls':[{'name':'bash','arguments':{'command':'SYNTHETIC CHECK'}}]},
                    {'role':'tool','name':'bash','content':'SYNTHETIC result','metadata':{'exit_code':0}},
                    {'role':'assistant','content':f'SYNTHETIC summary {number}'}]}
            splits[split].append(row)
            families = [f'SYNTHETIC-FAMILY-{number}']
            records[ident] = {'kind':kind,'generator':'SYNTHETIC-GENERATOR','families':families,'author_reference_exposure':False}
            digest = contract.fingerprint(row)
            validation_rows[ident] = {'sha256':digest,'families':families}
            reviews[ident] = [{'record_sha256':digest,'reviewer':f'SYNTHETIC-REVIEWER-{i}',
                'decision':'approved','checks':{c:'passed' for c in contract.CHECKS}} for i in (1,2)]
        frozen = []
        for i in range(20):
            name = f'evals/tasks/frontend-stack/synthetic-{i}.md'
            reference, start = f'{1000000+i*2:040x}', f'{1000001+i*2:040x}'
            files[name] = (f'SYNTHETIC TEST ONLY\nReference commit: `{reference}`\nStart commit: `{start}`\n'
                           f'## Prompt\nSYNTHETIC frozen prompt {i}\n## Success criteria\nSYNTHETIC\n')
            frozen.append({'path':name,'repository':'synthetic','reference':reference,'start':start,
                           'families':[f'SYNTHETIC-EVAL-FAMILY-{i}']})
        validation_path = PREFIX + 'synthetic-validation.json'
        reviews_path = PREFIX + 'synthetic-reviews.json'
        ledger_path = PREFIX + 'synthetic-human-ledger.json'
        files[validation_path] = {'schema_version':1,'checks':{c:'passed' for c in contract.CHECKS},
            'source_families_complete':True,'records':validation_rows,'frozen_eval':frozen}
        files[reviews_path] = {'schema_version':1,'records':reviews}
        required = [splits['train'][0]['id'],splits['train'][-1]['id']]
        files[ledger_path] = {'entries':[{'id':ident,'record_sha256':validation_rows[ident]['sha256'],
            'actor_type':'human','decision':'human_approved','reviewer':'SYNTHETIC-TEST-HUMAN',
            'approved_at':'2026-08-06T00:00:00Z','notes':'SYNTHETIC FIXTURE, NOT A REAL HUMAN APPROVAL'} for ident in required]}
        for name,value in files.items(): self.write(name,value)
        for split,rows in splits.items():
            for suffix in ('', '-short3072'):
                self.write(PREFIX + split + suffix + '.jsonl',rows,lines=True)
        names = list(files) + [PREFIX + split + suffix + '.jsonl' for split in splits for suffix in ('','-short3072')]
        manifest = {'schema_version':2,'specialist':'frontend-stack','max_tokens':3072,
            'split_policy':{'method':'source-family-grouped','seed':3407,'holdout_fraction':0.05},
            'render_options':{'enable_thinking':False,'add_generation_prompt':False},
            'records':records,'reviews':reviews_path,'validation':validation_path,'frozen_eval':frozen,
            'human_spot_check':{'ledger':ledger_path,'required_ids':required},
            'artifacts':{name:contract.sha256((self.root / name).read_bytes()) for name in names}}
        self.write(PREFIX + 'manifest.json',manifest)
        for name in builder.HELPERS:
            self.write(name,(contract.ROOT / name).read_text(encoding='utf-8'))

    def report(self):
        return contract.check_contract(self.root)

    def assertBlocked(self, fragment):
        report = self.report()
        self.assertFalse(report['data_ready'],report)
        self.assertFalse(report['train_ready'])
        self.assertIn(fragment,' '.join(report['blockers']))

    def test_missing_v2_never_falls_back_to_v1(self):
        self.write('datasets/frontend-stack/final/train.jsonl','SYNTHETIC V1 DECOY')
        self.assertBlocked('missing required V2 input')

    def test_synthetic_model_free_contract_is_only_provisional(self):
        self.fixture()
        report = self.report()
        self.assertTrue(report['data_ready'],report)
        self.assertEqual(report['status'],'DATA_READY_RUNTIME_PROVISIONAL')
        self.assertFalse(report['train_ready'])
        self.assertEqual(report['counts']['final'],{'gold':185,'general':65})

    def ai_review_fixture(self):
        self.fixture()
        manifest = self.read(PREFIX + 'manifest.json')
        required = manifest['human_spot_check']['required_ids']
        manifest.pop('human_spot_check')
        ledger_path = PREFIX + 'synthetic-ai-ledger.json'
        manifest.update(review_policy='independent_ai', ai_spot_check={'ledger':ledger_path,'required_ids':required})
        entries = []
        for number, ident in enumerate(required):
            row = next(row for name in ('train','holdout') for row in contract.load_rows(self.root / (PREFIX + name + '.jsonl')) if row['id'] == ident)
            row_hash = contract.fingerprint(row)
            reviewer = 'SYNTHETIC-THIRD-AI-REVIEWER'
            evidence_path = PREFIX + f'synthetic-ai-review-{number}.json'
            self.write(evidence_path, {'reviewer':reviewer,'record_sha256':row_hash,
                                       'decision':'approved','checks':{c:'passed' for c in contract.CHECKS},
                                       'findings':[f'SYNTHETIC TEST ONLY: reviewed {ident} source, transcript, and validations; not a real approval.']})
            manifest['artifacts'][evidence_path] = contract.sha256((self.root / evidence_path).read_bytes())
            entries.append({'id':ident,'record_sha256':row_hash,'actor_type':'ai','decision':'ai_approved',
                            'reviewer':reviewer,'approved_at':'2026-08-06T00:00:00Z',
                            'notes':'SYNTHETIC TEST ONLY, NOT A REAL REVIEW','evidence_path':evidence_path})
        self.write(ledger_path, {'entries':entries})
        manifest['artifacts'][ledger_path] = contract.sha256((self.root / ledger_path).read_bytes())
        self.write(PREFIX + 'manifest.json', manifest)
        return ledger_path

    def test_ai_review_policy_requires_independent_bound_evidence(self):
        ledger_path = self.ai_review_fixture()
        self.assertTrue(self.report()['data_ready'], self.report())
        self.mutate(ledger_path, lambda ledger: ledger['entries'][0].update(reviewer='SYNTHETIC-REVIEWER-1'))
        self.assertBlocked('AI spot-check must be distinct')

    def test_ai_review_policy_rejects_human_impersonation_and_missing_evidence(self):
        ledger_path = self.ai_review_fixture()
        self.mutate(ledger_path, lambda ledger: ledger['entries'][0].update(actor_type='human', decision='human_approved'))
        self.assertBlocked('AI spot-check must be distinct')
        ledger = self.read(ledger_path)
        ledger['entries'][0].update(actor_type='ai',decision='ai_approved',evidence_path='missing.json')
        self.write(ledger_path, ledger)
        self.bind(ledger_path)
        self.assertBlocked('AI spot-check review evidence is not hash-bound')

    def test_ai_review_policy_rejects_empty_findings(self):
        self.ai_review_fixture()
        self.mutate(PREFIX + 'synthetic-ai-review-0.json', lambda evidence: evidence.update(findings=[]))
        self.assertBlocked('AI spot-check evidence lacks row-specific findings')

    def test_closed_tool_argument_schema(self):
        schema = {'type':'object','required':['path'],'properties':{'path':{'type':'string'}}}
        contract.validate_tool_value({'path':'synthetic'},schema,'test')
        for value in ({'path':3},{'path':'synthetic','extra':True},{}):
            with self.subTest(value=value),self.assertRaises(ValueError):
                contract.validate_tool_value(value,schema,'test')
        with self.assertRaises(ValueError):
            contract.validate_tool_value('synthetic',{'type':'string','pattern':'unverified'},'test')

    def test_hash_tampering(self):
        self.fixture()
        self.write('training/pi_tools.json',[])
        self.assertBlocked('hash mismatch')

    def test_native_normalization_must_be_documented_verified(self):
        self.fixture()
        self.mutate('training/templates/qwen3-4b.base-pin.json',lambda v:v.update(parity_verified=False))
        self.assertBlocked('normalization not explicitly verified')

    def test_wrong_base_revision(self):
        self.fixture()
        self.mutate('training/templates/qwen3-4b.base-pin.json',lambda v:v.update(revision='0'*40))
        self.assertBlocked('unpinned quantized 4B base')

    def test_stale_review_and_nonindependent_reviewer(self):
        self.fixture()
        name = PREFIX + 'synthetic-reviews.json'
        self.mutate(name,lambda v:v['records']['frontend-stack:synthetic-0'][0].update(record_sha256='0'*64))
        self.assertBlocked('incomplete/stale review')
        self.fixture()
        self.mutate(name,lambda v:v['records']['frontend-stack:synthetic-0'][0].update(reviewer='SYNTHETIC-GENERATOR'))
        self.assertBlocked('reviewer is generator')

    def test_human_ledger_required_and_never_inferred(self):
        self.fixture()
        self.mutate(PREFIX + 'synthetic-human-ledger.json',lambda v:v.update(entries=[]))
        self.assertBlocked('human spot-check incomplete')

    def test_borderline_score_8_cannot_omit_human_review(self):
        self.fixture();ident='frontend-stack:synthetic-10'
        rows=contract.load_rows(self.root/(PREFIX+'train.jsonl'))
        row=next(row for row in rows if row['id']==ident);row['quality']['judge_score']=8
        for suffix in ('','-short3072'):
            name=PREFIX+'train'+suffix+'.jsonl';self.write(name,rows,lines=True);self.bind(name)
        digest=contract.fingerprint(row)
        self.mutate(PREFIX+'synthetic-validation.json',lambda v:v['records'][ident].update(sha256=digest))
        def reviews(value):
            for entry in value['records'][ident]:entry['record_sha256']=digest
        self.mutate(PREFIX+'synthetic-reviews.json',reviews)
        self.assertBlocked('borderline score-8')

    def test_human_actor_cannot_be_an_agent(self):
        self.fixture()
        self.mutate(PREFIX + 'synthetic-human-ledger.json',lambda v:v['entries'][0].update(actor_type='agent'))
        self.assertBlocked('actual declared human approval')

    def test_complete_family_coverage_required(self):
        self.fixture()
        self.mutate(PREFIX + 'synthetic-validation.json',lambda v:v.update(source_families_complete=False))
        self.assertBlocked('source-family coverage not complete')

    def test_source_family_variants_cannot_cross_split(self):
        self.fixture()
        ident = 'frontend-stack:synthetic-180'
        manifest = self.read(PREFIX + 'manifest.json')
        families = manifest['records']['frontend-stack:synthetic-0']['families']
        manifest['records'][ident]['families'] = families
        self.write(PREFIX + 'manifest.json',manifest)
        self.mutate(PREFIX + 'synthetic-validation.json',lambda v:v['records'][ident].update(families=families))
        self.assertBlocked('source-family/commit/prompt/messages overlap')

    def test_frozen_eval_coverage_and_binding(self):
        self.fixture()
        manifest = self.read(PREFIX + 'manifest.json')
        manifest['frozen_eval'].pop()
        self.write(PREFIX + 'manifest.json',manifest)
        self.assertBlocked('incomplete frozen eval bindings')

    def test_registry_gold_lower_bound_is_enforced(self):
        self.fixture()
        self.mutate('datasets/v2-registry.json',lambda v:v['specialists'][0].update(target_gold_records=[186,220]))
        self.assertBlocked('gold below registry lower bound')

    def test_general_minimum_cannot_be_filled_with_gold(self):
        self.fixture()
        removed = {f'frontend-stack:synthetic-{i}' for i in range(239,245)}
        for split in ('train','holdout'):
            for suffix in ('','-short3072'):
                name = PREFIX + split + suffix + '.jsonl'
                rows = [row for row in contract.load_rows(self.root / name) if row['id'] not in removed]
                self.write(name,rows,lines=True)
                self.bind(name)
        manifest = self.read(PREFIX + 'manifest.json')
        for ident in removed: del manifest['records'][ident]
        self.write(PREFIX + 'manifest.json',manifest)
        for name in (PREFIX + 'synthetic-validation.json',PREFIX + 'synthetic-reviews.json'):
            def discard(value):
                for ident in removed: del value['records'][ident]
            self.mutate(name,discard)
        self.assertBlocked('reviewed general corpus below 60')

    def test_general_and_gold_counts_are_separate(self):
        self.fixture()
        manifest = self.read(PREFIX + 'manifest.json')
        manifest['records']['frontend-stack:synthetic-185']['kind'] = 'gold'
        self.write(PREFIX + 'manifest.json',manifest)
        self.assertBlocked('wrong specialist/general identity')

    def test_bounded_rows_are_not_edited_or_truncated(self):
        self.fixture()
        name = PREFIX + 'train-short3072.jsonl'
        rows = contract.load_rows(self.root / name)
        rows[0]['messages'][-1]['content'] = 'SYNTHETIC TRUNCATED'
        self.write(name,rows,lines=True)
        self.bind(name)
        self.assertBlocked('modifies/reassigns whole records')

    def test_holdout_cannot_be_filtered(self):
        self.fixture()
        name = PREFIX + 'holdout-short3072.jsonl'
        self.write(name,contract.load_rows(self.root / name)[:-1],lines=True)
        self.bind(name)
        self.assertBlocked('holdout must remain complete')

    def test_safe_paths(self):
        for name in ('../outside','/absolute','C:/host','folder\\file','a/../b'):
            with self.subTest(name=name),self.assertRaises(ValueError):
                contract.safe_path(self.root,name)

    def test_blocked_notebook_zero_payload_and_first_cell_stops(self):
        first,second = builder.notebook_text(self.root),builder.notebook_text(self.root)
        self.assertEqual(first,second)
        notebook = json.loads(first)
        self.assertEqual(notebook['metadata']['v2_payload_file_count'],0)
        self.assertEqual([cell['id'] for cell in notebook['cells']],
                         ['overview','gate','install','runtime-source','isolated-probe','train-export','qualification'])
        overview = ''.join(notebook['cells'][0]['source'])
        self.assertIn('Zero approved data', overview)
        self.assertIn('NOT TRAINABLE', overview)
        self.assertIn('missing required V2 input:', overview)
        self.assertIn('Do not select a GPU', overview)
        self.assertEqual(notebook['metadata']['colab']['name'], 'Frontend Qwen3-4B — BLOCKED')
        gate = ''.join(notebook['cells'][1]['source'])
        self.assertIn("PAYLOAD_B64 = ''", gate)
        with patch('subprocess.run',side_effect=AssertionError('no install or training before data')):
            with self.assertRaisesRegex(RuntimeError,'BLOCKED'): exec(gate,{})
            for blocked in notebook['cells'][2:6]:
                with self.subTest(blocked=blocked['id']), self.assertRaisesRegex(RuntimeError,'BLOCKED'):
                    exec(''.join(blocked['source']),{})
        for blocked in notebook['cells']:
            if blocked['cell_type']=='code': compile(''.join(blocked['source']),'<notebook-cell>','exec')

    def test_ready_synthetic_notebook_is_deterministic_and_hash_bound(self):
        self.fixture()
        notebook = builder.build_notebook(self.root)
        self.assertEqual(builder.notebook_text(self.root),builder.notebook_text(self.root))
        overview = ''.join(notebook['cells'][0]['source'])
        self.assertIn('Local reviewed-data contract passed', overview)
        self.assertNotIn('NOT TRAINABLE', overview)
        self.assertGreater(notebook['metadata']['v2_payload_file_count'], 0)
        gate = ''.join(notebook['cells'][1]['source'])
        tree = ast.parse(gate)
        values = {node.targets[0].id:ast.literal_eval(node.value) for node in tree.body
                  if isinstance(node,ast.Assign) and isinstance(node.targets[0],ast.Name)
                  and node.targets[0].id in {'PAYLOAD_B64','PAYLOAD_HASHES'}}
        with zipfile.ZipFile(io.BytesIO(base64.b64decode(values['PAYLOAD_B64']))) as archive:
            self.assertEqual(set(archive.namelist()),set(values['PAYLOAD_HASHES']))
            for name,digest in values['PAYLOAD_HASHES'].items():
                self.assertEqual(contract.sha256(archive.read(name)),digest)
        for cell in notebook['cells']:
            if cell['cell_type'] == 'code': compile(''.join(cell['source']),'<notebook-cell>','exec')

    def test_assistant_mask_includes_calls_not_system_examples_or_tool_results(self):
        text = ('<|im_start|>system\n<tool_call>instruction example</tool_call><|im_end|>\n'
                '<|im_start|>user\nSYNTHETIC USER<|im_end|>\n'
                '<|im_start|>assistant\n<tool_call>{"name":"bash"}</tool_call><|im_end|>\n'
                '<|im_start|>user\n<tool_response>SYNTHETIC RESULT</tool_response><|im_end|>\n'
                '<|im_start|>assistant\nSYNTHETIC ANSWER<|im_end|>')
        ids = list(range(len(text)))
        offsets = [(i,i+1) for i in ids]
        labels = contract.assistant_labels(text,ids,offsets,1)
        for value in ('instruction example','SYNTHETIC USER','SYNTHETIC RESULT'):
            start = text.index(value)
            self.assertTrue(all(label == -100 for label in labels[start:start+len(value)]))
        for value in ('{"name":"bash"}','SYNTHETIC ANSWER'):
            start = text.index(value)
            self.assertEqual(labels[start:start+len(value)],ids[start:start+len(value)])
        with self.assertRaises(ValueError): contract.assistant_labels(text,ids,offsets,0)

    def test_gguf_header_selection_is_not_an_identity_certificate(self):
        node = next(node for node in ast.parse(builder.RUNTIME).body
                    if isinstance(node,ast.FunctionDef) and node.name == 'gguf_type')
        namespace = {'struct':struct,'require':contract.require}
        exec(compile(ast.Module(body=[node],type_ignores=[]),'<gguf-parser>','exec'),namespace)
        key = b'general.file_type'
        def data(file_type):
            return b'GGUF' + struct.pack('<IQQ',3,1,1) + struct.pack('<Q',len(key)) + key + struct.pack('<II',4,file_type)
        path = self.root / 'SYNTHETIC-NOT-A-REAL-MODEL.gguf'
        path.write_bytes(data(15))
        self.assertEqual(namespace['gguf_type'](path),15)
        path.write_bytes(data(1))
        with self.assertRaises(ValueError): namespace['gguf_type'](path)
        path.write_bytes(b'NOT GGUF')
        with self.assertRaises(ValueError): namespace['gguf_type'](path)

    def test_runtime_source_compiles_without_importing_heavy_modules(self):
        compile(builder.RUNTIME,'<v2-runtime>','exec')
        self.assertLess(builder.RUNTIME.index("report = check_contract(root)"),builder.RUNTIME.index('import unsloth'))
        self.assertIn("require(trainer.state.global_step == 1",builder.RUNTIME)
        self.assertIn("metrics = trainer.evaluate()",builder.RUNTIME)
        self.assertIn("general.file_type != 15",builder.RUNTIME)
        self.assertIn('validate_checkpoint(checkpoint, run_contract)',builder.RUNTIME)
        self.assertIn('resume_from_checkpoint = str(checkpoint)',builder.RUNTIME)
        self.assertIn('trainer.train(resume_from_checkpoint=resume_from_checkpoint)',builder.RUNTIME)
        self.assertIn("warmup_ratio=0 if probing else 0.05",builder.RUNTIME)
        self.assertIn('validate_probe_evidence(probe_evidence)',builder.RUNTIME)
        self.assertIn('validate_gguf_reader(GGUFReader',builder.RUNTIME)

    def test_pip_torch_weights_unreachable_for_missing_data(self):
        # No import hook or subprocess is needed for the stdlib gate/builder.
        with patch('subprocess.run',side_effect=AssertionError('must not execute')):
            self.assertFalse(self.report()['data_ready'])
            self.assertEqual(builder.build_notebook(self.root)['metadata']['v2_payload_file_count'],0)

    def test_actual_checked_in_native_canonical_padding_contract(self):
        contract.validate_base_pin(contract.load_json(contract.ROOT/'training/templates/qwen3-4b.base-pin.json'),
                                   contract.load_json(contract.ROOT/'training/templates/qwen3-4b.pin.json'))

    def test_reference_exposed_gold_is_rejected(self):
        self.fixture()
        manifest=self.read(PREFIX+'manifest.json')
        manifest['records']['frontend-stack:synthetic-0']['author_reference_exposure']=True
        self.write(PREFIX+'manifest.json',manifest)
        self.assertBlocked('reference exposure')

    def test_general_rows_only_in_holdout_are_not_training_coverage(self):
        self.fixture()
        train=contract.load_rows(self.root/(PREFIX+'train.jsonl'))
        holdout=contract.load_rows(self.root/(PREFIX+'holdout.jsonl'))
        moved=[row for row in train if row['specialist']=='general']
        for split,rows in [('train',[row for row in train if row['specialist']!='general']),('holdout',holdout+moved)]:
            for suffix in ('','-short3072'):
                name=PREFIX+split+suffix+'.jsonl';self.write(name,rows,lines=True);self.bind(name)
        self.assertBlocked('general: insufficient training coverage')

    def test_missing_split_policy_is_blocked(self):
        self.fixture();manifest=self.read(PREFIX+'manifest.json');manifest.pop('split_policy')
        self.write(PREFIX+'manifest.json',manifest);self.assertBlocked('5% split policy')

    def test_probe_rejects_skipped_zero_lr_zero_delta_and_nonfinite_updates(self):
        valid={'optimizer_steps':1,'optimizer_attempts':1,'optimizer_step_was_skipped':False,
               'gradient_finite':True,'gradient_nonzero':True,'adapter_finite':True,
               'loss':2.0,'learning_rate':2e-4,'adapter_change_max':1e-5,'longest_holdout_passed':True}
        contract.validate_probe_evidence(valid)
        for key,value in [('optimizer_step_was_skipped',True),('learning_rate',0),('adapter_change_max',0),
                          ('loss',float('nan')),('gradient_finite',False),('gradient_nonzero',False),
                          ('adapter_finite',False),('longest_holdout_passed',False),('optimizer_attempts',2)]:
            with self.subTest(key=key),self.assertRaises(ValueError):contract.validate_probe_evidence(dict(valid,**{key:value}))

    def test_checkpoint_content_binding_rejects_mixed_state(self):
        folder=self.root/'checkpoint-10';folder.mkdir();run={'SYNTHETIC':'RUN'}
        for name,value in [('run-contract.json',run),('trainer_state.json',{'global_step':10})]:
            (folder/name).write_text(contract.canonical(value),encoding='utf-8')
        for name in ('optimizer.pt','scheduler.pt','adapter_model.safetensors'):(folder/name).write_bytes(b'SYNTHETIC NOT WEIGHTS')
        (folder/'checkpoint-hashes.json').write_text(contract.canonical(contract.checkpoint_hashes(folder)),encoding='utf-8')
        contract.validate_checkpoint(folder,run)
        (folder/'adapter_model.safetensors').write_bytes(b'SYNTHETIC MIXED STATE')
        with self.assertRaisesRegex(ValueError,'content hash'):contract.validate_checkpoint(folder,run)

    def gguf_fixture(self):
        config={'model_type':'qwen3','hidden_size':32,'intermediate_size':64,'head_dim':16,
                'num_attention_heads':2,'num_key_value_heads':1,'num_hidden_layers':1,'vocab_size':8,'tie_word_embeddings':True}
        tokens=[f'SYNTHETIC TOKEN {i}' for i in range(8)];vocab={token:i for i,token in enumerate(tokens)}
        metadata={'GGUF.version':3,'general.file_type':15,'general.architecture':'qwen3',
                  'qwen3.block_count':1,'qwen3.embedding_length':32,'qwen3.feed_forward_length':64,
                  'qwen3.attention.head_count':2,'qwen3.attention.head_count_kv':1,
                  'tokenizer.chat_template':'SYNTHETIC TEMPLATE','tokenizer.ggml.tokens':tokens,
                  'tokenizer.ggml.padding_token_id':7,'tokenizer.ggml.eos_token_id':6}
        shapes={'token_embd.weight':[32,8],'output_norm.weight':[32]}
        block={'attn_q':[32,32],'attn_k':[32,16],'attn_v':[32,16],'attn_output':[32,32],
               'ffn_gate':[32,64],'ffn_up':[32,64],'ffn_down':[64,32],
               'attn_norm':[32],'ffn_norm':[32],'attn_q_norm':[16],'attn_k_norm':[16]}
        shapes.update({'blk.0.'+key+'.weight':value for key,value in block.items()})
        tensors=[];offset=4096
        for name,shape in shapes.items():
            elements=shape[0]*(shape[1] if len(shape)>1 else 1);kind=12 if len(shape)>1 else 0
            size=elements//256*144 if kind==12 else elements*4
            tensors.append(SimpleNamespace(name=name,shape=shape,n_elements=elements,tensor_type=kind,n_bytes=size,data_offset=offset))
            offset=((offset+size+31)//32)*32
        reader=SimpleNamespace(fields={key:SimpleNamespace(contents=lambda value=value:value) for key,value in metadata.items()},
                               tensors=tensors,alignment=32,data_offset=4096)
        return reader,offset,config,vocab,'SYNTHETIC TEMPLATE',{'padding':7,'eos':6,'bos':None}

    def test_gguf_full_layout_bounds_vocabulary_template_and_quantization(self):
        args=self.gguf_fixture();self.assertEqual(contract.validate_gguf_reader(*args)['tensor_count'],13)
        reader,*rest=self.gguf_fixture();reader.tensors=[]
        with self.assertRaisesRegex(ValueError,'tensor table'):contract.validate_gguf_reader(reader,*rest)
        for field,value in [('general.architecture','llama'),('tokenizer.chat_template','WRONG'),
                            ('tokenizer.ggml.tokens',['WRONG']*8),('tokenizer.ggml.padding_token_id',6)]:
            reader,*rest=self.gguf_fixture();reader.fields[field]=SimpleNamespace(contents=lambda:value)
            with self.subTest(field=field),self.assertRaises(ValueError):contract.validate_gguf_reader(reader,*rest)
        for attr,value in [('shape',[32,7]),('data_offset',0),('n_bytes',10**9),('tensor_type',99)]:
            reader,*rest=self.gguf_fixture();setattr(reader.tensors[0],attr,value)
            with self.subTest(attr=attr),self.assertRaises(ValueError):contract.validate_gguf_reader(reader,*rest)
        reader,*rest=self.gguf_fixture();reader.tensors[1].data_offset=reader.tensors[0].data_offset
        with self.assertRaisesRegex(ValueError,'overlap'):contract.validate_gguf_reader(reader,*rest)
        reader,*rest=self.gguf_fixture()
        for tensor in reader.tensors:tensor.tensor_type=0
        with self.assertRaisesRegex(ValueError,'mostly Q4'):contract.validate_gguf_reader(reader,*rest)

    def test_mock_converter_sibling_return_discovery_dedup_stale_and_escape(self):
        outputs=self.root/'outputs';outputs.mkdir();requested=outputs/'gguf'
        sibling=outputs/'gguf_gguf';artifact=sibling/'SYNTHETIC-NOT-A-MODEL.gguf'
        def convert(*args,**kwargs):
            sibling.mkdir();artifact.write_bytes(b'SYNTHETIC FORMAT FIXTURE ONLY')
            return {'gguf_directory':str(sibling),'gguf_files':[str(artifact),str(artifact)]}
        converter=Mock(side_effect=convert)
        result=converter(str(requested),quantization_method='q4_k_m')
        converter.assert_called_once_with(str(requested),quantization_method='q4_k_m')
        self.assertEqual(contract.discover_gguf_exports(requested,outputs,result),[artifact.resolve()])
        self.assertEqual(contract.discover_gguf_exports(requested,outputs),[artifact.resolve()])
        result['gguf_files']=[artifact.name]
        self.assertEqual(contract.discover_gguf_exports(requested,outputs,result),[artifact.resolve()])
        with self.assertRaisesRegex(ValueError,'pre-existing'):
            contract.discover_gguf_exports(requested,outputs,result,{artifact})
        with self.assertRaisesRegex(ValueError,'escapes'):
            contract.discover_gguf_exports(requested,outputs,{'gguf_directory':str(self.root)})

    def test_notebook_cells_have_deterministic_schema_ids(self):
        notebook=builder.build_notebook(self.root)
        ids=[cell['id'] for cell in notebook['cells']]
        self.assertEqual(len(ids),len(set(ids)))

    def test_checked_in_scaffold_matches_generator(self):
        self.assertEqual((contract.ROOT / builder.NOTEBOOK).read_text(encoding='utf-8'),builder.notebook_text(contract.ROOT))


if __name__ == '__main__':
    unittest.main()
