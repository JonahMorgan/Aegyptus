import mwclient

site = mwclient.Site('en.wiktionary.org')
page = site.pages['ꜣbyt']
text = page.text()

# Find the descendants section
lines = text.split('\n')
in_desc = False
desc_lines = []
for i, line in enumerate(lines):
    if 'Descendants' in line:
        in_desc = True
    elif in_desc:
        if line.startswith('===') or line.startswith('=='):
            break
        desc_lines.append(line)

print("Raw Descendants section from Wiktionary:")
print('\n'.join(desc_lines[:40]))
