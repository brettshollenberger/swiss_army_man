import re

def underscore(string):
    # This pattern identifies capital letters that are either at the start of the string or preceded by other letters.
    pattern = r'(?<!^)(?=[A-Z])'
    
    # Replace capital letters identified by the pattern with an underscore and the lowercase version of the letter.
    underscore_string = re.sub(pattern, '_', string).lower()
    
    return underscore_string