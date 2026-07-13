import difflib

def get_diff(old_content, new_content):
    old_lines = old_content.splitlines()
    new_lines = new_content.splitlines()
    diff = difflib.unified_diff(old_lines,new_lines,lineterm='')
    return list(diff)