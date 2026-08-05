from trl import SFTConfig, SFTTrainer
import gc

# PEFT 0.18.1 can detect Colab's preinstalled TorchAO, then import an API that
# some TorchAO builds do not export. This model is BitsAndBytes 4-bit, not
# TorchAO-quantized, so skip only that irrelevant PEFT dispatcher.
import peft.tuners.lora.torchao as peft_torchao_dispatch
peft_torchao_dispatch.is_torchao_available = lambda: False
print('PEFT compatibility: TorchAO dispatcher disabled (BitsAndBytes path retained).')

# If the previous failed call partially inserted an adapter, reload the clean
# 4-bit base before retrying. On a fresh Run all this branch does nothing.
partial_lora = any(hasattr(module, 'lora_A') for module in model.modules())
if partial_lora:
    print('Partial LoRA injection detected; reloading the clean base model.')
    del model
    gc.collect()
    torch.cuda.empty_cache()
    model, tokenizer = FastLanguageModel.from_pretrained(
        model_name=BASE_MODEL,
        max_seq_length=MAX_SEQ,
        load_in_4bit=True,
    )
    tokenizer.chat_template = pinned_template
    assert tokenizer.chat_template.strip() == pinned_template.strip()

model = FastLanguageModel.get_peft_model(
    model,
    r=16,
    lora_alpha=32,
    lora_dropout=0.0,
    bias='none',
    target_modules=[
        'q_proj', 'k_proj', 'v_proj', 'o_proj',
        'gate_proj', 'up_proj', 'down_proj',
    ],
    use_gradient_checkpointing='unsloth',
    random_state=731,
)

run_config = {
    'repo_commit': REPO_COMMIT,
    'base_model': BASE_MODEL,
    'max_seq_length': MAX_SEQ,
    'train_sha256': 'f4c36ca2b83d98137841777eb2d64024d929c82fdacfad75292607be5777d19d',
    'holdout_sha256': '8d59b5c22ee6df65d8b1843d0bdf08dc352aa6640efee07d8fc6d17158485372',
    'template_sha256': '0958f6ebb716badab20903885efa1a26ee5a8d2ce9162bfcfe982ff43cff4077',
    'epochs': 2.0,
    'learning_rate': 2e-4,
    'effective_batch': 16,
    'save_steps': 1,
    'seed': 731,
}

config_path = DRIVE_ROOT / f'run_config-{MAX_SEQ}.json'
if config_path.exists():
    if json.loads(config_path.read_text()) != run_config:
        raise RuntimeError(
            'Checkpoint config differs from this notebook; use a new DRIVE_ROOT.'
        )
else:
    config_path.write_text(json.dumps(run_config, indent=2), encoding='utf-8')

trainer = SFTTrainer(
    model=model,
    processing_class=tokenizer,
    train_dataset=train_ds,
    eval_dataset=eval_ds,
    args=SFTConfig(
        output_dir=str(TRAINER_OUT),
        dataset_text_field='text',
        max_length=MAX_SEQ,
        per_device_train_batch_size=1,
        per_device_eval_batch_size=1,
        gradient_accumulation_steps=16,
        num_train_epochs=2.0,
        learning_rate=2e-4,
        lr_scheduler_type='cosine',
        warmup_ratio=0.05,
        logging_steps=1,
        eval_strategy='steps',
        eval_steps=8,
        save_strategy='steps',
        save_steps=1,
        save_total_limit=2,
        optim='paged_adamw_8bit',
        fp16=not is_bfloat16_supported(),
        bf16=is_bfloat16_supported(),
        weight_decay=0.01,
        seed=731,
        report_to='none',
    ),
)

trainer = train_on_responses_only(
    trainer,
    instruction_part='<|im_start|>user\n',
    response_part='<|im_start|>assistant\n',
)

def checkpoint_step(path):
    try:
        return int(path.name.rsplit('-', 1)[-1])
    except ValueError:
        return -1

def checkpoint_is_complete(path):
    required = [
        path / 'trainer_state.json',
        path / 'optimizer.pt',
        path / 'scheduler.pt',
    ]
    weights = [
        path / 'adapter_model.safetensors',
        path / 'adapter_model.bin',
        path / 'model.safetensors',
        path / 'pytorch_model.bin',
    ]
    if not all(item.is_file() and item.stat().st_size > 0 for item in required):
        return False
    if not any(item.is_file() and item.stat().st_size > 0 for item in weights):
        return False
    try:
        json.loads((path / 'trainer_state.json').read_text(encoding='utf-8'))
    except (OSError, json.JSONDecodeError):
        return False
    return True

checkpoint_candidates = sorted(
    TRAINER_OUT.glob('checkpoint-*'),
    key=checkpoint_step,
    reverse=True,
)
resume_checkpoint = next(
    (str(path) for path in checkpoint_candidates if checkpoint_is_complete(path)),
    None,
)
skipped_checkpoints = [
    str(path) for path in checkpoint_candidates if not checkpoint_is_complete(path)
]
if skipped_checkpoints:
    print('Ignoring incomplete checkpoints:', skipped_checkpoints)
print('Resume checkpoint:', resume_checkpoint or 'none (fresh run)')
