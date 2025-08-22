import re
import uuid

_slug_re = re.compile(r'[^a-z0-9\-]+')


def slugify(value, max_len=100):
    v = (value or '').strip().lower()
    v = v.replace(' ', '-')
    v = _slug_re.sub('-', v)
    v = re.sub(r'-{2,}', '-', v).strip('-')
    return v[:max_len] or 'item'


def ensure_unique_name(base_name, is_taken, suffix_seed=None, max_tries=50):
    name = slugify(base_name)
    if not is_taken(name):
        return name
    seed = slugify(suffix_seed or str(uuid.uuid4())[:8])
    for i in range(1, max_tries + 1):
        cand = f"{name}-migrated-{seed[:8]}{('-'+str(i)) if i > 1 else ''}"
        if not is_taken(cand):
            return cand
    # fallback
    while True:
        cand = f"{name}-migrated-{uuid.uuid4().hex[:12]}"
        if not is_taken(cand):
            return cand
