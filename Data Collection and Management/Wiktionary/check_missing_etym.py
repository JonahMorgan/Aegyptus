import json

# Load networks
with open('lemma_networks_v2.json', 'r', encoding='utf-8') as f:
    networks = json.load(f)

# Find the two problematic networks
net1 = [n for n in networks if n['network_id'] == 'NET02268'][0]
net2 = [n for n in networks if n['network_id'] == 'NET02373'][0]

print("NET02268:")
print(f"  Root: {net1['root_lemma']} ({net1['root_language']})")
print(f"  Root Etymology Index: {net1.get('root_etymology_index', 'N/A')}")
print(f"  Nodes: {len(net1['nodes'])}")
print(f"  Edges: {len(net1['edges'])}")
print(f"\n  Nodes:")
for node in net1['nodes']:
    print(f"    - {node['form']} ({node['language']}) - etym_idx={node.get('etymology_index', 'None')}")
print(f"\n  Edges: {net1['edges']}")

print("\n" + "="*60)
print("\nNET02373:")
print(f"  Root: {net2['root_lemma']} ({net2['root_language']})")
print(f"  Root Etymology Index: {net2.get('root_etymology_index', 'N/A')}")
print(f"  Nodes: {len(net2['nodes'])}")
print(f"  Edges: {len(net2['edges'])}")
print(f"\n  Nodes:")
for node in net2['nodes']:
    print(f"    - {node['form']} ({node['language']}) - etym_idx={node.get('etymology_index', 'None')}")
print(f"\n  Edges: {net2['edges']}")
