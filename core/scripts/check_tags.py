
import sys
import re

def check_tags(filename):
    with open(filename, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Remove style and script blocks
    content = re.sub(r'<style.*?>.*?</style>', '', content, flags=re.DOTALL)
    content = re.sub(r'<script.*?>.*?</script>', '', content, flags=re.DOTALL)
    content = re.sub(r'{%.*?%}', '', content, flags=re.DOTALL)
    content = re.sub(r'{{.*?}}', '', content, flags=re.DOTALL)
    
    # SVG tags and other void tags
    void_tags = {'img', 'br', 'hr', 'input', 'link', 'meta', 'source', 'area', 'base', 'col', 'embed', 'keygen', 'param', 'track', 'wbr', 'path', 'circle', 'rect', 'ellipse', 'line', 'polyline', 'polygon', 'stop', 'use', 'animate', 'feGaussianBlur', 'feComposite'}
    
    tags = re.findall(r'<(/?)([a-zA-Z0-9_-]+)', content)
    stack = []
    
    for closing, name in tags:
        name = name.lower()
        if name in void_tags:
            continue
        if not closing:
            stack.append(name)
        else:
            if not stack:
                print(f"Error: Unexpected closing tag </{name}>")
                continue
            last = stack.pop()
            if last != name:
                print(f"Error: Mismatched tag <{last}> closed by </{name}>")
    
    if stack:
        print(f"Error: Unclosed tags: {stack}")
    else:
        print("Tags are balanced.")

if __name__ == "__main__":
    check_tags(sys.argv[1])
