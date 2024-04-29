def is_numeric(value):
    try:
        float(value)
        return True
    except (ValueError, TypeError):
        return False

def is_present(value):
    return value is not None and len(str(value)) > 0