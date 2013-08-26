import re

def smart_remove_char(string):
    """Remove dots from a string. It's trying to be smart and not remove dots after a caps letter."""
    #string1 = re.sub(r'([^.A-Z])\.([^.0-9 ])', r'\1 \2', string)
    #string2 = re.sub(r'([^.A-Z])\.([^.0-9 ])', r'\1 \2', string1)
    string1 = string
    string2 = string1
    
    i_stuffs = re.compile(re.escape('vostfr'), re.IGNORECASE)
    string3 = i_stuffs.sub('', string2)
    string4 = string3.strip('"')
    string5 = string4.strip("'")
    string6 = string5.replace("\n", "")
    string7 = string6.replace("/", " ")
    return string6
