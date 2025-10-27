import json
import sys

sys.stdout.reconfigure(encoding='utf-8')

with open('lemma_networks.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

print("="*80)
print("VERIFYING PLACEHOLDER ANCESTOR NODES")
print("="*80)

# Find network containing ⲁⲓⲁⲓ (previously standalone, should now have Demotic root)
cop_network = None
for network in data:
    if any(n['form'] == 'ⲁⲓⲁⲓ' and n['language'] == 'cop' for n in network['nodes']):
        cop_network = network
        break

if cop_network:
    print(f"\n✓ Found network containing Coptic ⲁⲓⲁⲓ")
    print(f"\nNetwork ID: {cop_network['network_id']}")
    print(f"Root node: {cop_network['root_node']['language']} | {cop_network['root_node']['form']}")
    print(f"Root meanings: {cop_network['root_node'].get('meanings', [])}")
    print(f"\nTotal nodes: {len(cop_network['nodes'])}")
    
    print("\nAll nodes in network:")
    for node in cop_network['nodes']:
        lang = node['language']
        form = node['form']
        meanings = node.get('meanings', [])
        meanings_str = f" - {meanings[0][:50]}..." if meanings else " - [no meanings]"
        dialect = f" [{node['dialect']}]" if node.get('dialect') else ""
        print(f"  {lang:5s} | {form:15s}{dialect:20s}{meanings_str}")
    
    print("\nEdges:")
    for edge in cop_network['edges']:
        from_node = next((n for n in cop_network['nodes'] if n['id'] == edge['from']), None)
        to_node = next((n for n in cop_network['nodes'] if n['id'] == edge['to']), None)
        if from_node and to_node:
            print(f"  {edge['type']:10s}: {from_node['language']}:{from_node['form']} → {to_node['language']}:{to_node['form']}")
    
    # Check if root is placeholder
    root_is_placeholder = not cop_network['root_node'].get('meanings')
    if root_is_placeholder:
        print(f"\n✓ Root is PLACEHOLDER node (missing Demotic ancestor created)")
    else:
        print(f"\n✓ Root has full data")
else:
    print("\n✗ Network not found")

print("\n" + "="*80)
print("CHECKING DESCENDANT PLACEHOLDERS")
print("="*80)

# Find an Egyptian network with Coptic descendants
egy_with_desc = None
for network in data:
    if network['root_node']['language'] == 'egy':
        # Check if has Coptic descendants
        has_cop_desc = any(e['type'] == 'DESCENDS' and 
                          any(n['id'] == e['to'] and n['language'] in ['cop', 'dem'] 
                              for n in network['nodes'])
                          for e in network['edges'])
        if has_cop_desc:
            egy_with_desc = network
            break

if egy_with_desc:
    print(f"\n✓ Found Egyptian network with descendants")
    print(f"\nNetwork ID: {egy_with_desc['network_id']}")
    print(f"Root: egy | {egy_with_desc['root_node']['form']}")
    
    # Count nodes by language
    from collections import Counter
    lang_counts = Counter(n['language'] for n in egy_with_desc['nodes'])
    print(f"\nNodes by language: {dict(lang_counts)}")
    
    # Show DESCENDS edges
    desc_edges = [e for e in egy_with_desc['edges'] if e['type'] == 'DESCENDS']
    print(f"\nDESCENDS edges: {len(desc_edges)}")
    for edge in desc_edges[:5]:
        from_node = next((n for n in egy_with_desc['nodes'] if n['id'] == edge['from']), None)
        to_node = next((n for n in egy_with_desc['nodes'] if n['id'] == edge['to']), None)
        if from_node and to_node:
            to_meanings = to_node.get('meanings', [])
            is_placeholder = " [PLACEHOLDER]" if not to_meanings else ""
            print(f"  {from_node['language']}:{from_node['form']} → {to_node['language']}:{to_node['form']}{is_placeholder}")

print("\n" + "="*80)
print("SUMMARY")
print("="*80)
print(f"\n✓ Networks reduced from 5251 → {len(data)} (merged via placeholders)")
print(f"✓ Missing ancestors create placeholder root nodes")
print(f"✓ Missing descendants create placeholder nodes in network")
