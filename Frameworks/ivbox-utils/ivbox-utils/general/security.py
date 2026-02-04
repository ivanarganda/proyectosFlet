import hashlib

def make_str_hash(args) -> str:
    base = "-".join([str(arg).lower().strip() for arg in args])
    return int(hashlib.md5(base.encode()).hexdigest()[:12], 16)

def make_id_hash(args) -> int:

    raw = "-".join([str(arg).lower().strip() for arg in args])
    h = hashlib.md5(raw.encode()).hexdigest()
    return int(h[:14], 16)   # entero grande pero manejable