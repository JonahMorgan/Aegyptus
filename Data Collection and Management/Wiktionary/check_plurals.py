import json
import sys

sys.stdout.reconfigure(encoding='utf-8')

# Check the baboon example
with open('egyptian_lemmas_parsed_mwp.json', 'r', encoding='utf-8') as f:
    egy_data = json.load(f)

lemma = 'jꜥn'
if lemma in egy_data:
    entry = egy_data[lemma]
    print(f"Lemma: {lemma}")
    
    for i, etym in enumerate(entry['etymologies']):
        print(f"\nEtymology {i+1}:")
        for j, defn in enumerate(etym['definitions']):
            print(f"\n  Part of speech: {defn['part_of_speech']}")
            print(f"  Definitions: {defn['definitions'][:2]}")
            
            alt_forms = defn.get('alternative_forms', [])
            print(f"\n  Alternative forms ({len(alt_forms)} total):")
            
            for k, af in enumerate(alt_forms, 1):
                translit = af.get('transliteration', af.get('form', '?'))
                hieroglyphs = af.get('hieroglyphs', '')
                date = af.get('date', 'NO DATE')
                title = af.get('title', '')
                note = af.get('note', '')
                
                # Check if this is a plural
                info = f"{title} {note}".lower()
                is_plural = 'plural' in info or 'pl' in info
                
                marker = " [PLURAL]" if is_plural else ""
                print(f"    {k:2d}. {translit:20s} <{hieroglyphs[:30]:30s}> [{date:30s}]{marker}")
                if title:
                    print(f"        Title: {title[:80]}")
                if note:
                    print(f"        Note: {note[:80]}")

# Check the current network
with open('lemma_networks.json', 'r', encoding='utf-8') as f:
    networks = json.load(f)

print("\n" + "="*80)
print("CURRENT NETWORK FOR jꜥn")
print("="*80)

for network in networks:
    if network['root_node']['form'] == 'jꜥnjw' or network['root_node']['form'] == 'jꜥn':
        print(f"\nNetwork ID: {network['network_id']}")
        print(f"Root: {network['root_node']['form']}")
        print(f"Total nodes: {len(network['nodes'])}")
        
        print("\nAll node forms:")
        for node in network['nodes']:
            lang = node['language']
            form = node['form']
            period = node.get('period') or 'undated'
            hier = node.get('hieroglyphs') or ''
            print(f"  {lang} | {form:20s} | {period:30s} | <{hier[:40]}>")
        
        break
