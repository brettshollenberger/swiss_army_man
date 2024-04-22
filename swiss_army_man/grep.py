import re

def grep(data, search):
    pattern = re.compile(search)
    return [col for col in data if pattern.search(col)]