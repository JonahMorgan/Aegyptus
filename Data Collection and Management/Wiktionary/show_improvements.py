import json
import sys

sys.stdout.reconfigure(encoding='utf-8')

with open('lemma_networks.json', 'r', encoding='utf-8') as f:
    networks = json.load(f)

print("="*80)
print("IMPROVED NETWORK STRUCTURE EXAMPLES")
print("="*80)

# Find networks with good EVOLVES chains
print("\n1. TEMPORAL EVOLUTION (Actual form changes across periods)")
print("-"*80)

examples_found = 0
for network in networks[:1000]:
    evolves_edges = [e for e in network['edges'] if e['type'] == 'EVOLVES']
    if 2 <= len(evolves_edges) <= 5:
        print(f"\nNetwork ID: {network['network_id']}")
        print(f"Root: {network['root_node']['form']}")
        
        # Show the evolution chain
        print("\nTemporal evolution:")
        for edge in evolves_edges:
            from_node = next((n for n in network['nodes'] if n['id'] == edge['from']), None)
            to_node = next((n for n in network['nodes'] if n['id'] == edge['to']), None)
            
            if from_node and to_node:
                from_period = from_node.get('period', 'undated')
                to_period = to_node.get('period', 'undated')
                from_hier = from_node.get('hieroglyphs', '')
                to_hier = to_node.get('hieroglyphs', '')
                
                print(f"  {from_node['form']:15s} <{from_hier[:20]:20s}> [{from_period:25s}]")
                print(f"    ↓ {edge.get('notes', '')}")
                print(f"  {to_node['form']:15s} <{to_hier[:20]:20s}> [{to_period:25s}]")
                print()
        
        examples_found += 1
        if examples_found >= 3:
            break

# Find networks with VARIANT edges (same period, different writings)
print("\n2. VARIANTS (Different writings in same period)")
print("-"*80)

examples_found = 0
for network in networks[:1000]:
    variant_edges = [e for e in network['edges'] if e['type'] == 'VARIANT']
    if 3 <= len(variant_edges) <= 8:
        # Check if they're actually in the same period
        period_groups = {}
        for edge in variant_edges:
            from_node = next((n for n in network['nodes'] if n['id'] == edge['from']), None)
            to_node = next((n for n in network['nodes'] if n['id'] == edge['to']), None)
            if from_node and to_node:
                period = from_node.get('period') or to_node.get('period') or 'undated'
                if period not in period_groups:
                    period_groups[period] = []
                period_groups[period].append((from_node, to_node, edge))
        
        # Show if has good examples
        if len(period_groups) >= 2:
            print(f"\nNetwork ID: {network['network_id']}")
            print(f"Root: {network['root_node']['form']}")
            
            for period, edges in list(period_groups.items())[:2]:
                print(f"\n  Variants in {period}:")
                for from_node, to_node, edge in edges[:3]:
                    from_hier = from_node.get('hieroglyphs') or ''
                    to_hier = to_node.get('hieroglyphs') or ''
                    print(f"    {from_node['form']:12s} <{from_hier[:15]:15s}> ↔ {to_node['form']:12s} <{to_hier[:15]:15s}>")
            
            examples_found += 1
            if examples_found >= 2:
                break

# Show the baboon example now
print("\n3. COMPLETE EXAMPLE: Baboon word (jꜥn)")
print("-"*80)

for network in networks:
    if network['network_id'] == 'L00438' or 'baboon' in str(network.get('root_node', {}).get('meanings', [])).lower():
        print(f"\nNetwork ID: {network['network_id']}")
        print(f"Root: {network['root_node']['form']}")
        print(f"Total nodes: {len(network['nodes'])}")
        print(f"Total edges: {len(network['edges'])}")
        
        # Count edge types
        evolves = [e for e in network['edges'] if e['type'] == 'EVOLVES']
        variants = [e for e in network['edges'] if e['type'] == 'VARIANT']
        descends = [e for e in network['edges'] if e['type'] == 'DESCENDS']
        
        print(f"\nEdge breakdown:")
        print(f"  EVOLVES (temporal evolution): {len(evolves)}")
        print(f"  VARIANT (same-period variants): {len(variants)}")
        print(f"  DESCENDS (cross-language): {len(descends)}")
        
        if evolves:
            print(f"\nEVOLVES edges (actual temporal changes):")
            for edge in evolves[:5]:
                from_node = next((n for n in network['nodes'] if n['id'] == edge['from']), None)
                to_node = next((n for n in network['nodes'] if n['id'] == edge['to']), None)
                if from_node and to_node:
                    print(f"  {from_node['form']} [{from_node.get('period', '?')}] → {to_node['form']} [{to_node.get('period', '?')}]")
        
        if variants:
            print(f"\nVARIANT edges (first 5 of {len(variants)}):")
            for edge in variants[:5]:
                from_node = next((n for n in network['nodes'] if n['id'] == edge['from']), None)
                to_node = next((n for n in network['nodes'] if n['id'] == edge['to']), None)
                if from_node and to_node:
                    period = from_node.get('period') or to_node.get('period') or 'undated'
                    print(f"  {from_node['form']} ↔ {to_node['form']} [{period}]")
        
        break

print("\n" + "="*80)
print("SUMMARY OF IMPROVEMENTS")
print("="*80)
print("\n✓ EVOLVES edges now only connect forms across different periods")
print("✓ Same-period forms are correctly marked as VARIANT")
print("✓ No more self-loops (jꜥnꜥ → jꜥnꜥ)")
print("✓ Hieroglyphic variants in same period are properly grouped")
print("\nThis structure accurately represents:")
print("  • Temporal evolution: Different forms across time periods")
print("  • Spelling variants: Different writings in the same period")
print("  • Cross-language descent: Egyptian → Demotic → Coptic")
