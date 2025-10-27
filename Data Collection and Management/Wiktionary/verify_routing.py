import json
import sys

sys.stdout.reconfigure(encoding='utf-8')

with open('lemma_networks.json', 'r', encoding='utf-8') as f:
    networks = json.load(f)

print("="*80)
print("VERIFYING BABOON NETWORK STRUCTURE")
print("="*80)

# Find the baboon network
baboon_network = None
for network in networks:
    if any('baboon' in str(n.get('meanings', '')).lower() for n in network['nodes'][:5]):
        baboon_network = network
        break

if baboon_network:
    print(f"\nNetwork ID: {baboon_network['network_id']}")
    print(f"Root node: {baboon_network['root_node']['language']} | {baboon_network['root_node']['form']}")
    print(f"Total nodes: {len(baboon_network['nodes'])}")
    
    # Group nodes by language
    from collections import defaultdict
    by_lang = defaultdict(list)
    for node in baboon_network['nodes']:
        by_lang[node['language']].append(node)
    
    print(f"\nNodes by language:")
    for lang in ['egy', 'dem', 'cop']:
        if lang in by_lang:
            print(f"  {lang}: {len(by_lang[lang])} nodes")
            for node in by_lang[lang][:5]:
                period = node.get('period') or node.get('dialect') or 'undated'
                print(f"    - {node['form']} [{period}]")
            if len(by_lang[lang]) > 5:
                print(f"    ... and {len(by_lang[lang]) - 5} more")
    
    # Check DESCENDS edges
    print(f"\nDESCENDS edges:")
    desc_edges = [e for e in baboon_network['edges'] if e['type'] == 'DESCENDS']
    for edge in desc_edges:
        from_node = next((n for n in baboon_network['nodes'] if n['id'] == edge['from']), None)
        to_node = next((n for n in baboon_network['nodes'] if n['id'] == edge['to']), None)
        if from_node and to_node:
            print(f"  {from_node['language']}:{from_node['form']} → {to_node['language']}:{to_node['form']}")
    
    # Verify: Are Coptic nodes connecting through Demotic?
    print(f"\nVERIFYING COPTIC ROUTING:")
    coptic_parent_edges = [e for e in desc_edges if to_node and to_node['language'] in ['cop', 'cop-boh', 'cop-sah', 'cop-akh']]
    for edge in coptic_parent_edges[:10]:
        from_node = next((n for n in baboon_network['nodes'] if n['id'] == edge['from']), None)
        to_node = next((n for n in baboon_network['nodes'] if n['id'] == edge['to']), None)
        if from_node:
            if from_node['language'] == 'dem':
                print(f"  ✓ {to_node['form']} (Coptic) → {from_node['form']} (Demotic)")
            elif from_node['language'] == 'egy':
                print(f"  ⚠ {to_node['form']} (Coptic) → {from_node['form']} (Egyptian) - should go through Demotic!")

print("\n" + "="*80)
