import re

def is_valid_email(email):
    return bool(re.match(r"^[^@]+@[^@]+\.[^@]+$", email))

def is_valid_phone(phone):
    return phone.isdigit() and 7 <= len(phone) <= 20

def is_valid_name(name):
    return bool(re.match(r"^[A-Z ]+$", name))