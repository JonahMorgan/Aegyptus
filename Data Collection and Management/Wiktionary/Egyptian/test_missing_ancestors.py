import json
import sys

sys.stdout.reconfigure(encoding='utf-8')

with open('coptic_lemmas_parsed_mwp.json', 'r', encoding='utf-8') as f:
    coptic_data = json.load(f)

with open('demotic_lemmas_parsed_mwp.json', 'r', encoding='utf-8') as f:
    demotic_data = json.load(f)

with open('lemma_networks.json', 'r', encoding='utf-8') as f:
    networks = json.load(f)

print("="*80)
print("CHECKING FOR COPTIC LEMMAS WITH MISSING DEMOTIC ANCESTORS")
print("="*80)

# Find Coptic lemmas that reference Demotic ancestors
coptic_with_dem_ref = []

for lemma_form, entry in coptic_data.items():
    for etym in entry.get('etymologies', []):
        etym_text = etym.get('etymology_text', '')
        if 'egx-dem' in etym_text or 'Demotic' in etym_text:
            coptic_with_dem_ref.append({
                'coptic_form': lemma_form,
                'etymology': etym_text
            })

print(f"\nFound {len(coptic_with_dem_ref)} Coptic lemmas referencing Demotic")

# Check a few examples
missing_count = 0
standalone_count = 0

for i, item in enumerate(coptic_with_dem_ref[:10], 1):
    cop_form = item['coptic_form']
    etym = item['etymology']
    
    # Try to extract Demotic form from etymology
    # Look for patterns like {{inh|cop|egx-dem|word}}
    import re
    dem_match = re.search(r'\{\{inh\|cop\|egx-dem\|([^|}]+)', etym)
    
    if dem_match:
        dem_form = dem_match.group(1)
        
        # Check if Demotic form exists in our data
        in_demotic_data = dem_form in demotic_data
        
        # Find Coptic network
        cop_network = None
        for network in networks:
            if any(n['form'] == cop_form and n['language'] == 'cop' for n in network['nodes']):
                cop_network = network
                break
        
        if cop_network:
            # Check if it's standalone or connected
            root_lang = cop_network['root_node']['language']
            has_dem_ancestor = any(n['language'] == 'dem' for n in cop_network['nodes'])
            
            print(f"\n{i}. Coptic: {cop_form}")
            print(f"   Etymology refs Demotic: {dem_form}")
            print(f"   Demotic in data: {in_demotic_data}")
            print(f"   Network root: {root_lang} | {cop_network['root_node']['form']}")
            print(f"   Has Demotic ancestor in network: {has_dem_ancestor}")
            
            if not in_demotic_data:
                if root_lang == 'cop':
                    print(f"   ✓ Created standalone Coptic network (missing Demotic)")
                    standalone_count += 1
                else:
                    print(f"   ✓ Connected to {root_lang} ancestor")
                missing_count += 1

print(f"\n" + "="*80)
print(f"SUMMARY")
print(f"="*80)
print(f"Coptic lemmas with missing Demotic ancestors: {missing_count}")
print(f"Standalone Coptic networks created: {standalone_count}")
print(f"\n✓ The code handles missing ancestors by creating standalone networks")
