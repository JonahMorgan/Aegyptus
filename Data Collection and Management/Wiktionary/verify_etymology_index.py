import json

# Load networks
with open('lemma_networks_v2.json', 'r', encoding='utf-8') as f:
    networks = json.load(f)

# Find ϣⲱϣ networks
target_form = "ϣⲱϣ"
found_networks = []

for net in networks:
    for node in net['nodes']:
        if node['form'] == target_form:
            found_networks.append({
                'network_id': net['network_id'],
                'node': node
            })
            break

print(f"\nFound {len(found_networks)} networks containing '{target_form}':\n")

for item in found_networks:
    net_id = item['network_id']
    node = item['node']
    etym_idx = node.get('etymology_index', 'MISSING')
    
    print(f"Network {net_id}:")
    print(f"  Form: {node['form']}")
    print(f"  Language: {node['language']}")
    print(f"  POS: {node.get('pos', 'N/A')}")
    print(f"  Etymology Index: {etym_idx}")
    print(f"  Meanings: {node.get('meanings', [])[:1]}")  # Show first meaning
    print()

# Also check if all networks with ϣⲱϣ have etymology_index
missing_etym_index = [item for item in found_networks if item['node'].get('etymology_index') is None]

if missing_etym_index:
    print(f"❌ WARNING: {len(missing_etym_index)} nodes missing etymology_index")
else:
    print(f"✅ SUCCESS: All {len(found_networks)} nodes have etymology_index set")
