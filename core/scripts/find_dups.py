
import re
from collections import Counter

def find_duplicates(filename):
    with open(filename, 'r', encoding='utf-8') as f:
        content = f.read()
    ids = re.findall(r'id=[\'\"]([^\'\"]*)[\'\"]', content)
    counts = Counter(ids)
    duplicates = {i: c for i, c in counts.items() if c > 1}
    if duplicates:
        print(f"Duplicate IDs in {filename}: {duplicates}")
    else:
        print(f"No duplicate IDs in {filename}")

find_duplicates(r'f:\fullclone\agrosense.io\core\templates\core\base.html')
find_duplicates(r'f:\fullclone\agrosense.io\core\templates\core\dashboard.html')
