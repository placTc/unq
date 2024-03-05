import random
import string

def generate_random_string(length: int) -> str:
    return ''.join(random.choice(string.ascii_lowercase) for i in range(length))