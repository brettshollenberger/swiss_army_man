def is_numeric(value):
    try:
        float(value)
        return True
    except (ValueError, TypeError):
        return False