import json
import sys
from collections import Counter

sys.stdout.reconfigure(encoding='utf-8')

with open('lemma_networks.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

# Find the standalone Coptic network
cop_standalone = [n for n in data if n['root_node']['language'] == 'cop' and n['root_node']['form'] == 'ⲁⲓⲁⲓ'][0]

print("="*80)
print("STANDALONE COPTIC NETWORK IN lemma_networks.json")
print("="*80)
print(f"\nNetwork ID: {cop_standalone['network_id']}")
print(f"Root: {cop_standalone['root_node']['form']} ({cop_standalone['root_node']['language']})")
print(f"Total nodes: {len(cop_standalone['nodes'])}")
print(f"Total edges: {len(cop_standalone['edges'])}")

print("\nEdge types:")
edge_types = Counter(e['type'] for e in cop_standalone['edges'])
for etype, count in edge_types.items():
    print(f"  {etype}: {count}")

print("\nAll nodes:")
for node in cop_standalone['nodes']:
    dialect_str = f" [{node['dialect']}]" if node.get('dialect') else ""
    print(f"  {node['language']} | {node['form']}{dialect_str}")

if cop_standalone['edges']:
    print("\nFirst 10 edges:")
    for e in cop_standalone['edges'][:10]:
        print(f"  {e}")
else:
    print("\n✓ NO DESCENDS edges (as expected - missing Demotic ancestor)")

print("\n" + "="*80)
print("VERIFICATION")
print("="*80)
print(f"\n✓ Standalone Coptic network EXISTS in lemma_networks.json")
print(f"✓ Network ID: {cop_standalone['network_id']}")
print(f"✓ Root is Coptic (not Egyptian or Demotic)")
print(f"✓ Contains {len(cop_standalone['nodes'])} nodes (main form + dialectal variants)")
if not any(e['type'] == 'DESCENDS' for e in cop_standalone['edges']):
    print(f"✓ NO DESCENDS edges (missing Demotic ancestor handled correctly)")
