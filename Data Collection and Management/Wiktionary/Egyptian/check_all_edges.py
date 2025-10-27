import json
import sys

sys.stdout.reconfigure(encoding='utf-8')

with open('lemma_networks.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

# Find baboon network
baboon = [n for n in data if n['network_id'] == 'L00974'][0]

print("Baboon Network - ALL EDGES")
print("="*80)

print("\n1. ALL NODES:")
for node in baboon['nodes']:
    lang = node['language']
    form = node['form']
    period = node.get('period') or node.get('dialect') or 'undated'
    node_id = node['id']
    print(f"  {node_id:10s} | {lang:8s} | {form:15s} [{period}]")

print("\n2. ALL EDGES BY TYPE:")

print("\nEVOLVES edges (temporal evolution within Egyptian):")
evolves_edges = [e for e in baboon['edges'] if e['type'] == 'EVOLVES']
for e in evolves_edges:
    from_node = next((n for n in baboon['nodes'] if n['id'] == e['from']), None)
    to_node = next((n for n in baboon['nodes'] if n['id'] == e['to']), None)
    if from_node and to_node:
        print(f"  {from_node['id']} → {to_node['id']} | {from_node['form']:15s} → {to_node['form']}")

print(f"\nVARIANT edges (spelling/hieroglyphic variants):")
variant_edges = [e for e in baboon['edges'] if e['type'] == 'VARIANT']
for e in variant_edges:
    from_node = next((n for n in baboon['nodes'] if n['id'] == e['from']), None)
    to_node = next((n for n in baboon['nodes'] if n['id'] == e['to']), None)
    if from_node and to_node:
        print(f"  {from_node['id']} → {to_node['id']} | {from_node['form']:15s} → {to_node['form']}")

print(f"\nDESCENDS edges (cross-language/first attestation):")
descends_edges = [e for e in baboon['edges'] if e['type'] == 'DESCENDS']
for e in descends_edges:
    from_node = next((n for n in baboon['nodes'] if n['id'] == e['from']), None)
    to_node = next((n for n in baboon['nodes'] if n['id'] == e['to']), None)
    if from_node and to_node:
        print(f"  {from_node['id']} → {to_node['id']} | {from_node['language']:8s} {from_node['form']:15s} → {to_node['language']:8s} {to_node['form']}")

print("\n3. DISCONNECTED NODES (not in any edge):")
all_edge_node_ids = set()
for e in baboon['edges']:
    all_edge_node_ids.add(e['from'])
    all_edge_node_ids.add(e['to'])

disconnected = [n for n in baboon['nodes'] if n['id'] not in all_edge_node_ids]
for node in disconnected:
    lang = node['language']
    form = node['form']
    period = node.get('period') or node.get('dialect') or 'undated'
    node_id = node['id']
    print(f"  {node_id:10s} | {lang:8s} | {form:15s} [{period}]")
