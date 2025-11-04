"""
Extract ego-centric networks from the full lemma network graph.

An ego network is centered around a specific node (lemma) and includes only:
- The ego node itself
- All nodes within N degrees of separation
- All edges connecting those nodes

This is useful for:
- Visualizing a single word's etymology without overwhelming detail
- Training models on focused etymological relationships
- Understanding a specific word's evolution path
"""

import json
from collections import deque
from typing import Dict, List, Set, Tuple


def find_node_in_networks(networks: List[Dict], language: str, form: str) -> Tuple[int, str]:
    """
    Find which network contains a specific node.
    
    Returns:
        (network_index, node_id) or (None, None) if not found
    """
    for net_idx, network in enumerate(networks):
        for node in network['nodes']:
            if node['language'] == language and node['form'] == form:
                return net_idx, node['id']
    return None, None


def extract_ego_network(network: Dict, ego_node_id: str, max_degrees: int = 2) -> Dict:
    """
    Extract an ego-centric network around a specific node.
    
    Args:
        network: Full network dictionary with 'nodes' and 'edges'
        ego_node_id: ID of the central node
        max_degrees: Maximum degrees of separation to include (default: 2)
    
    Returns:
        New network dictionary with only nodes within max_degrees
    """
    # Build adjacency list for BFS (undirected graph)
    adjacency = {}
    for edge in network['edges']:
        from_id = edge['from']
        to_id = edge['to']
        
        if from_id not in adjacency:
            adjacency[from_id] = []
        if to_id not in adjacency:
            adjacency[to_id] = []
        
        adjacency[from_id].append(to_id)
        adjacency[to_id].append(from_id)
    
    # BFS to find all nodes within max_degrees
    visited = {ego_node_id: 0}  # node_id -> distance from ego
    queue = deque([(ego_node_id, 0)])
    
    while queue:
        node_id, distance = queue.popleft()
        
        if distance >= max_degrees:
            continue
        
        # Visit neighbors
        for neighbor_id in adjacency.get(node_id, []):
            if neighbor_id not in visited:
                visited[neighbor_id] = distance + 1
                queue.append((neighbor_id, distance + 1))
    
    # Extract nodes within max_degrees
    included_node_ids = set(visited.keys())
    ego_nodes = [n for n in network['nodes'] if n['id'] in included_node_ids]
    
    # Extract edges where both endpoints are included
    ego_edges = [
        e for e in network['edges']
        if e['from'] in included_node_ids and e['to'] in included_node_ids
    ]
    
    # Create new network
    ego_network = {
        'network_id': f"ego_{ego_node_id}",
        'ego_node': ego_node_id,
        'max_degrees': max_degrees,
        'nodes': ego_nodes,
        'edges': ego_edges,
        'root_node': network.get('root_node')  # Preserve original root info
    }
    
    return ego_network


def extract_ancestry_path_network(network: Dict, ego_node_id: str, 
                                  include_siblings: bool = True,
                                  include_descendants: bool = False) -> Dict:
    """
    Extract only the direct ancestry path for a node.
    
    Args:
        network: Full network dictionary
        ego_node_id: ID of the target node
        include_siblings: Include variant forms and siblings at same level
        include_descendants: Include words that descended FROM this word
    
    Returns:
        Network with only direct ancestry chain
    """
    # Build directed adjacency lists
    ancestors = {}  # node -> list of ancestor nodes
    descendants = {}  # node -> list of descendant nodes
    siblings = {}  # node -> list of sibling/variant nodes
    
    for edge in network['edges']:
        from_id = edge['from']
        to_id = edge['to']
        edge_type = edge['type']
        
        # Ancestry edges (DESCENDS, EVOLVES, COMPONENT)
        if edge_type in ['DESCENDS', 'EVOLVES', 'COMPONENT']:
            if to_id not in ancestors:
                ancestors[to_id] = []
            ancestors[to_id].append(from_id)
            
            if from_id not in descendants:
                descendants[from_id] = []
            descendants[from_id].append(to_id)
        
        # Sibling edges (VARIANT, DERIVED)
        elif edge_type in ['VARIANT', 'DERIVED']:
            if to_id not in siblings:
                siblings[to_id] = []
            if from_id not in siblings:
                siblings[from_id] = []
            siblings[to_id].append(from_id)
            siblings[from_id].append(to_id)
    
    # Trace ancestry chain backwards
    included_nodes = {ego_node_id}
    to_process = [ego_node_id]
    
    while to_process:
        node_id = to_process.pop()
        
        # Add all ancestors
        for ancestor_id in ancestors.get(node_id, []):
            if ancestor_id not in included_nodes:
                included_nodes.add(ancestor_id)
                to_process.append(ancestor_id)
        
        # Add siblings if requested
        if include_siblings:
            for sibling_id in siblings.get(node_id, []):
                if sibling_id not in included_nodes:
                    included_nodes.add(sibling_id)
                    # Also get siblings' ancestors
                    to_process.append(sibling_id)
    
    # Add descendants if requested
    if include_descendants:
        to_process = [ego_node_id]
        while to_process:
            node_id = to_process.pop()
            for desc_id in descendants.get(node_id, []):
                if desc_id not in included_nodes:
                    included_nodes.add(desc_id)
                    to_process.append(desc_id)
    
    # Extract nodes and edges
    path_nodes = [n for n in network['nodes'] if n['id'] in included_nodes]
    path_edges = [
        e for e in network['edges']
        if e['from'] in included_nodes and e['to'] in included_nodes
    ]
    
    path_network = {
        'network_id': f"ancestry_{ego_node_id}",
        'ego_node': ego_node_id,
        'type': 'ancestry_path',
        'include_siblings': include_siblings,
        'include_descendants': include_descendants,
        'nodes': path_nodes,
        'edges': path_edges,
        'root_node': network.get('root_node')
    }
    
    return path_network


def generate_all_ego_networks(input_file: str = 'lemma_networks.json',
                              output_file: str = 'lemma_networks_ego.json',
                              max_degrees: int = 2):
    """
    Generate ego networks for every lemma in the dataset.
    
    Args:
        input_file: Path to full networks JSON
        output_file: Path to save ego networks
        max_degrees: Maximum degrees of separation
    """
    print(f"Loading full networks from {input_file}...")
    with open(input_file, 'r', encoding='utf-8') as f:
        networks = json.load(f)
    
    print(f"Generating ego networks (max_degrees={max_degrees})...")
    
    ego_networks = []
    total_nodes = 0
    
    for net_idx, network in enumerate(networks):
        if net_idx % 500 == 0:
            print(f"  Processing network {net_idx}/{len(networks)}...")
        
        # Generate ego network for the root node
        root_node = network.get('root_node')
        if root_node and root_node.get('id'):
            ego_net = extract_ego_network(network, root_node['id'], max_degrees)
            ego_networks.append(ego_net)
            total_nodes += len(ego_net['nodes'])
    
    print(f"\nGenerated {len(ego_networks)} ego networks")
    print(f"Total nodes: {total_nodes}")
    print(f"Average nodes per network: {total_nodes / len(ego_networks):.1f}")
    
    print(f"\nSaving to {output_file}...")
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(ego_networks, f, ensure_ascii=False, indent=2)
    
    print("Done!")


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='Extract ego-centric networks from lemma networks')
    parser.add_argument('--input', default='lemma_networks.json', help='Input networks file')
    parser.add_argument('--output', default='lemma_networks_ego.json', help='Output ego networks file')
    parser.add_argument('--degrees', type=int, default=2, help='Maximum degrees of separation')
    parser.add_argument('--mode', choices=['ego', 'ancestry'], default='ego',
                       help='Network extraction mode: ego (N-degree) or ancestry (direct path)')
    parser.add_argument('--language', help='Extract network for specific language:form (e.g., cop:ⲣⲁⲥϯ)')
    
    args = parser.parse_args()
    
    if args.language:
        # Extract single ego network for specified node
        lang, form = args.language.split(':', 1)
        
        with open(args.input, 'r', encoding='utf-8') as f:
            networks = json.load(f)
        
        net_idx, node_id = find_node_in_networks(networks, lang, form)
        
        if net_idx is None:
            print(f"Error: Node {lang}:{form} not found in networks")
            return
        
        print(f"Found {lang}:{form} in network {net_idx}, node ID: {node_id}")
        
        if args.mode == 'ego':
            print(f"Extracting ego network (max_degrees={args.degrees})...")
            result = extract_ego_network(networks[net_idx], node_id, args.degrees)
        else:
            print("Extracting ancestry path network...")
            result = extract_ancestry_path_network(networks[net_idx], node_id,
                                                   include_siblings=True,
                                                   include_descendants=True)
        
        print(f"\nResult:")
        print(f"  Nodes: {len(result['nodes'])}")
        print(f"  Edges: {len(result['edges'])}")
        
        output_file = f"{lang}_{form}_network.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
        
        print(f"\nSaved to {output_file}")
        
        # Print node list
        print("\nNodes in network:")
        for node in result['nodes']:
            print(f"  {node['language']}:{node['form']}")
    
    else:
        # Generate ego networks for all lemmas
        generate_all_ego_networks(args.input, args.output, args.degrees)


if __name__ == '__main__':
    main()
