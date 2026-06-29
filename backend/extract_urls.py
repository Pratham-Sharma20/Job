import re

with open('ms_careers.html', 'r', encoding='utf-8') as f:
    html = f.read()

urls = set(re.findall(r'https?://[^\s\"\'<>]+', html))
with open('ms_urls.txt', 'w', encoding='utf-8') as f:
    f.write('\n'.join(sorted(urls)))
