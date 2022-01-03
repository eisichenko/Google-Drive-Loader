INVALID_CHARACTERS = '/\\:*?<>"'  # for compatibility with android


def is_valid_name(name: str) -> bool:
    for c in INVALID_CHARACTERS:
        if c in name:
            return False
    return True
