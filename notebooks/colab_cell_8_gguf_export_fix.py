# Export or recover the Q4_K_M GGUF, copy it to the final output, verify it,
# clean temporary merge files, and start the download when Drive is disabled.
import gc
import hashlib
import json
import os
import shutil
from pathlib import Path

# Unsloth uses SAVE_DIRECTORY for merged HF weights, but writes GGUF files to
# SAVE_DIRECTORY + "_gguf". The previous cell searched the wrong directory.
MERGED_DIR = Path('/content/frontend-stack-gguf')
UNSLOTH_GGUF_DIR = Path(str(MERGED_DIR) + '_gguf')

def discover_ggufs(*roots):
    discovered = {}
    for root in roots:
        root = Path(root)
        if root.is_file() and root.suffix.lower() == '.gguf':
            discovered[str(root.resolve())] = root.resolve()
        elif root.is_dir():
            for candidate in root.rglob('*'):
                if candidate.is_file() and candidate.suffix.lower() == '.gguf':
                    discovered[str(candidate.resolve())] = candidate.resolve()
    return sorted(discovered.values(), key=lambda path: str(path).lower())

def is_q4_k_m(path):
    normalized = path.name.lower().replace('-', '_').replace('.', '_')
    return 'q4_k_m' in normalized

def valid_gguf(path):
    if not path.is_file() or path.stat().st_size < 1024**3:
        return False
    with path.open('rb') as handle:
        return handle.read(4) == b'GGUF'

# A previous export can be complete even though the old discovery check failed.
all_ggufs = discover_ggufs(UNSLOTH_GGUF_DIR, MERGED_DIR)
q4_ggufs = [path for path in all_ggufs if is_q4_k_m(path) and valid_gguf(path)]
reused_previous_export = len(q4_ggufs) == 1

if reused_previous_export:
    src_gguf = q4_ggufs[0]
    print('Reusing completed GGUF from the previous cell:', src_gguf)
else:
    if q4_ggufs:
        raise RuntimeError(f'Expected one valid Q4_K_M GGUF, found: {q4_ggufs}')

    # No usable prior Q4 file. Remove only these known temporary export folders,
    # then perform one clean conversion and trust Unsloth's returned file paths.
    for temporary in (MERGED_DIR, UNSLOTH_GGUF_DIR):
        if temporary.exists():
            shutil.rmtree(temporary)
    free_gib = shutil.disk_usage('/content').free / 1024**3
    if free_gib < 22:
        raise RuntimeError(
            f'Only {free_gib:.1f} GiB disk is free; clean the Colab runtime or '
            'enable Drive before repeating the 8B merge/quantization.'
        )

    MERGED_DIR.mkdir(parents=True)
    gc.collect()
    torch.cuda.empty_cache()
    export_result = model.save_pretrained_gguf(
        str(MERGED_DIR),
        tokenizer,
        quantization_method='q4_k_m',
        maximum_memory_usage=0.5,
    )
    print('Unsloth export directory:', export_result.get('gguf_directory'))
    returned_paths = [Path(path) for path in export_result.get('gguf_files', [])]
    all_ggufs = discover_ggufs(
        *returned_paths,
        Path(export_result.get('gguf_directory', UNSLOTH_GGUF_DIR)),
        UNSLOTH_GGUF_DIR,
        MERGED_DIR,
    )
    q4_ggufs = [path for path in all_ggufs if is_q4_k_m(path) and valid_gguf(path)]
    if len(q4_ggufs) != 1:
        raise RuntimeError(
            'GGUF conversion returned, but exactly one valid Q4_K_M artifact was '
            f'not found. Returned={returned_paths}; discovered={all_ggufs}'
        )
    src_gguf = q4_ggufs[0]

GGUF_OUT.mkdir(parents=True, exist_ok=True)
dst_gguf = GGUF_OUT / 'frontend-stack-qwen3-8b-q4_k_m.gguf'
partial_gguf = dst_gguf.with_suffix(dst_gguf.suffix + '.partial')
if partial_gguf.exists():
    partial_gguf.unlink()
shutil.copy2(src_gguf, partial_gguf)
if partial_gguf.stat().st_size != src_gguf.stat().st_size:
    raise RuntimeError('GGUF copy size mismatch')
with partial_gguf.open('rb') as handle:
    if handle.read(4) != b'GGUF':
        raise RuntimeError('Copied artifact does not have a GGUF header')
os.replace(partial_gguf, dst_gguf)

def sha256_file(path):
    digest = hashlib.sha256()
    with path.open('rb') as handle:
        for chunk in iter(lambda: handle.read(8 * 1024 * 1024), b''):
            digest.update(chunk)
    return digest.hexdigest()

artifact = {
    'path': str(dst_gguf),
    'bytes': dst_gguf.stat().st_size,
    'sha256': sha256_file(dst_gguf),
    'quantization': 'Q4_K_M',
    'reused_previous_export': reused_previous_export,
    'storage': 'google-drive' if DRIVE_AVAILABLE else 'temporary-runtime',
    'notebook_revision': NOTEBOOK_REVISION,
}
(GGUF_OUT / 'artifact.json').write_text(
    json.dumps(artifact, indent=2),
    encoding='utf-8',
)
print(json.dumps(artifact, indent=2))

# The final verified copy is independent, so remove large temporary merged and
# quantization folders to reclaim Colab disk space.
for temporary in (MERGED_DIR, UNSLOTH_GGUF_DIR):
    if temporary.exists() and temporary.resolve() not in dst_gguf.resolve().parents:
        shutil.rmtree(temporary)
print('Temporary export directories cleaned.')

if DRIVE_AVAILABLE:
    print('Done. Verified GGUF is syncing to Google Drive.')
else:
    print('Starting browser download. Keep this tab open until it finishes.')
    from google.colab import files
    files.download(str(dst_gguf))
