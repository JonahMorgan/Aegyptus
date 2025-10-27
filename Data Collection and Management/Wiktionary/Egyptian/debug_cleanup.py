import json
import sys

sys.stdout.reconfigure(encoding='utf-8')

# Load network
with open('lemma_networks.json', 'r', encoding='utf-8') as f:
    networks_list = json.load(f)
    # Convert to dict by network_id
    networks = {n['network_id']: n for n in networks_list}

print("Testing cleanup logic on baboon network")
print("="*60)

network_id = 'L00974'
network = networks[network_id]

print(f"Network has_demotic_descendant: {network.get('has_demotic_descendant', False)}")
print(f"Total edges before: {len(network['edges'])}")

edges_to_remove = []
for i, edge in enumerate(network['edges']):
    if edge['type'] != 'DESCENDS':
        continue
    
    source_node = next((n for n in network['nodes'] if n['id'] == edge['from']), None)
    target_node = next((n for n in network['nodes'] if n['id'] == edge['to']), None)
    
    if not source_node or not target_node:
        continue
    
    # Check if it's Egyptian→Coptic
    is_egy = source_node['language'] == 'egy'
    is_cop = target_node['language'].startswith('cop')
    
    print(f"Edge {i}: {source_node['language']} → {target_node['language']} | egy={is_egy}, cop={is_cop}, remove={is_egy and is_cop}")
    
    if is_egy and is_cop:
        edges_to_remove.append(i)

print(f"\nEdges to remove: {len(edges_to_remove)}")
print(f"Indices: {edges_to_remove}")
