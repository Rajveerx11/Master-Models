# Load the 4-bit base at a T4-safe context and retain only complete records.
# Nothing is truncated: records above the cap are excluded as whole trajectories.
import unsloth
from unsloth import FastLanguageModel, is_bfloat16_supported
from unsloth.chat_templates import train_on_responses_only
from datasets import Dataset
from collections import Counter

BASE_MODEL = 'unsloth/Qwen3-8B'
MAX_SEQ = 4096

# Never attempt a second model load after an OOM. Colab/IPython can retain the
# failed traceback and its CUDA tensors even after del/gc/empty_cache.
free_vram, total_vram = torch.cuda.mem_get_info()
free_vram_gib = free_vram / 1024**3
if free_vram_gib < 10.0:
    raise RuntimeError(
        f'Only {free_vram_gib:.2f} GiB GPU memory is free. A previous model is still '
        'resident. Use Runtime > Disconnect and delete runtime, reopen the '
        'v7_t4_safe notebook, and Run all from a fresh runtime.'
    )
print(f'Fresh-runtime VRAM check passed: {free_vram_gib:.2f} GiB free.')

model, tokenizer = FastLanguageModel.from_pretrained(
    model_name=BASE_MODEL,
    max_seq_length=MAX_SEQ,
    load_in_4bit=True,
)
pinned_template = template_path.read_text(encoding='utf-8')
tokenizer.chat_template = pinned_template
assert tokenizer.chat_template.strip() == pinned_template.strip()

def read_jsonl(path):
    return [
        json.loads(line)
        for line in path.read_text(encoding='utf-8').splitlines()
        if line.strip()
    ]

train_rows = read_jsonl(WORK / 'datasets/frontend-stack/final/train.jsonl')
eval_rows = read_jsonl(WORK / 'datasets/frontend-stack/final/holdout.jsonl')
assert len(train_rows) == 384 and len(eval_rows) == 20
assert Counter(row['source'] for row in train_rows) == Counter({
    'frontend-stack': 230,
    'hermes-function-calling-v1': 77,
    'databricks-dolly-15k': 77,
})
assert hashlib.sha256(
    (WORK / 'datasets/frontend-stack/final/train.jsonl').read_bytes()
).hexdigest() == 'f4c36ca2b83d98137841777eb2d64024d929c82fdacfad75292607be5777d19d'
assert hashlib.sha256(
    (WORK / 'datasets/frontend-stack/final/holdout.jsonl').read_bytes()
).hexdigest() == '8d59b5c22ee6df65d8b1843d0bdf08dc352aa6640efee07d8fc6d17158485372'

def render_bounded_rows(rows, label):
    texts = []
    lengths = []
    retained_sources = []
    dropped = 0
    for row in rows:
        text = tokenizer.apply_chat_template(
            row['messages'],
            tools=row.get('tools') or None,
            tokenize=False,
            add_generation_prompt=False,
            enable_thinking=False,
        )
        if row.get('tools') and '<tools>' not in text:
            raise RuntimeError('Tool-bearing record rendered without <tools>')
        length = len(tokenizer(text, add_special_tokens=False).input_ids) + 1
        if length > MAX_SEQ:
            dropped += 1
            continue
        texts.append(text)
        lengths.append(length)
        retained_sources.append(row['source'])
    if not texts:
        raise RuntimeError(f'{label}: token cap rejected every record')
    print(
        f'{label}: retained {len(texts)}/{len(rows)} complete records; '
        f'dropped {dropped}; token range {min(lengths)}-{max(lengths)}; '
        f'sources {dict(Counter(retained_sources))}'
    )
    return Dataset.from_dict({'text': texts}), lengths

train_ds, train_lengths = render_bounded_rows(train_rows, 'train')
eval_ds, eval_lengths = render_bounded_rows(eval_rows, 'holdout')
assert max(train_lengths) <= MAX_SEQ
assert max(eval_lengths) <= MAX_SEQ
print(
    f'Guards passed: {len(train_ds)} train / {len(eval_ds)} holdout | '
    f'MAX_SEQ={MAX_SEQ}'
)
