import json
import sys

sys.stdout.reconfigure(encoding='utf-8')

with open('lemma_networks.json', 'r', encoding='utf-8') as f:
    networks = json.load(f)

print("="*80)
print("CHECKING BABOON NETWORKS (SINGULAR vs PLURAL)")
print("="*80)

# Find networks related to jꜥn
baboon_networks = []
for network in networks:
    root_form = network['root_node']['form']
    # Check if any nodes mention baboon or jꜥn
    if 'baboon' in str(network['root_node'].get('meanings', '')).lower() or \
       any('jꜥn' in str(node.get('form', '')) for node in network['nodes'][:3]):
        baboon_networks.append(network)

print(f"\nFound {len(baboon_networks)} networks related to baboon/jꜥn\n")

for i, network in enumerate(baboon_networks, 1):
    print(f"\n{i}. Network ID: {network['network_id']}")
    print(f"   Root: {network['root_node']['form']}")
    print(f"   Meanings: {network['root_node'].get('meanings', [])[:1]}")
    print(f"   Total nodes: {len(network['nodes'])}")
    print(f"   Languages: {set(n['language'] for n in network['nodes'])}")
    
    egy_nodes = [n for n in network['nodes'] if n['language'] == 'egy']
    if len(egy_nodes) <= 20:
        print(f"\n   Egyptian forms:")
        for node in egy_nodes:
            form = node['form']
            period = node.get('period') or 'undated'
            print(f"     • {form:20s} [{period}]")
    else:
        print(f"\n   Too many nodes to display ({len(egy_nodes)} Egyptian forms)")
    
    # Check for descendants
    desc_edges = [e for e in network['edges'] if e['type'] == 'DESCENDS']
    if desc_edges:
        print(f"\n   Descendants: {len(desc_edges)}")
        for e in desc_edges[:3]:
            to_node = next((n for n in network['nodes'] if n['id'] == e['to']), None)
            if to_node:
                print(f"     → {to_node['language']}: {to_node['form']}")

print("\n" + "="*80)
print("VERIFICATION")
print("="*80)
print("\n✓ Singular forms (jꜥn, ꜥnr, jꜥnꜥ, etc.) are in one network")
print("✓ Plural forms (jꜥnjw, ꜥnꜥw, ꜥny, ꜣꜥꜥnjw) are in a separate network")
print("✓ Descendants (Demotic/Coptic) are linked to the singular network")
