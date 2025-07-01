def is_valid_email(email):
    return "@" in email and "." in email

def is_float(value):
    try:
        float(value)
        return True
    except:
        return False

def is_integer(value):
    try:
        int(value)
        return True
    except:
        return False
