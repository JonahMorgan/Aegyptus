import json
import sys

sys.stdout.reconfigure(encoding='utf-8')

with open('lemma_networks.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

# Find baboon network
baboon = [n for n in data if n['network_id'] == 'L00974'][0]

print("Baboon Network edges by type:")
print("="*60)

print("\nEVOLVES edges (temporal evolution within Egyptian):")
evolves_edges = [e for e in baboon['edges'] if e['type'] == 'EVOLVES']
for e in evolves_edges:
    from_node = next((n for n in baboon['nodes'] if n['id'] == e['from']), None)
    to_node = next((n for n in baboon['nodes'] if n['id'] == e['to']), None)
    if from_node and to_node:
        print(f"  {from_node['form']:15s} [{from_node.get('period', 'undated'):20s}] → {to_node['form']:15s} [{to_node.get('period', 'undated')}]")

print(f"\nDESCENDS edges (cross-language):")
edges = [e for e in baboon['edges'] if e['type'] == 'DESCENDS']
for e in edges:
    from_node = next((n for n in baboon['nodes'] if n['id'] == e['from']), None)
    to_node = next((n for n in baboon['nodes'] if n['id'] == e['to']), None)
    
    if from_node and to_node:
        print(f"  {from_node['language']:8s} {from_node['form']:15s} → {to_node['language']:8s} {to_node['form']}")
