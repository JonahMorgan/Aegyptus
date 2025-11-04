"""
Lemma Network Builder V2 - Ego-centric approach

Creates one network per lemma (form + etymology), containing:
1. The lemma itself (main form with hieroglyphs)
2. Alternative forms (hieroglyphic/spelling variants)
3. Direct descendants (Demotic/Coptic) - as LEAF nodes (no further expansion)
4. Alternative forms of descendants
5. Parent words (for compounds) - as LEAF nodes (no further expansion)

Each network is ego-centric - focused on ONE lemma, not merged into mega-networks.
"""

import json
import re
from collections import defaultdict


class EgocentricLemmaNetworkBuilder:
    """Build ego-centric lemma networks - one per lemma etymology"""
    
    def __init__(self):
        self.networks = []  # List of networks (not dict by ID)
        self.next_node_id = 0
        self.next_network_id = 0
        
        # Egyptian chronological periods (for sorting)
        self.egyptian_periods = [
            'Predynastic', 'Early Dynastic', 'Old Kingdom', 'First Intermediate Period',
            'Middle Kingdom', 'Second Intermediate Period', 'New Kingdom',
            'Third Intermediate Period', 'Late Period', 'Ptolemaic', 'Roman'
        ]
    
    def get_new_node_id(self):
        """Generate a new unique node ID"""
        node_id = f"N{self.next_node_id:05d}"
        self.next_node_id += 1
        return node_id
    
    def get_new_network_id(self):
        """Generate a new unique network ID"""
        network_id = f"NET{self.next_network_id:05d}"
        self.next_network_id += 1
        return network_id
    
    def create_node(self, language, form, pos='unknown', meanings=None, 
                    hieroglyphs=None, transliteration=None, period=None, 
                    dialect=None, etymology_index=None, definition_index=None):
        """Create a node dictionary"""
        # Dialect can be a string or list
        if dialect and not isinstance(dialect, list):
            dialect = [dialect]
        
        return {
            'id': self.get_new_node_id(),
            'language': language,
            'form': form,
            'transliteration': transliteration or form,
            'hieroglyphs': hieroglyphs,
            'part_of_speech': pos,
            'meanings': meanings or [],
            'period': period,
            'dialects': dialect or [],  # Changed to plural and always a list
            'etymology_index': etymology_index,
            'definition_index': definition_index
        }
    
    def add_dialect_to_node(self, node, dialect):
        """Add a dialect to a node's dialect list if not already present"""
        if dialect and dialect not in node.get('dialects', []):
            if 'dialects' not in node:
                node['dialects'] = []
            node['dialects'].append(dialect)
    
    def create_edge(self, from_id, to_id, edge_type, notes=''):
        """Create an edge dictionary"""
        return {
            'from': from_id,
            'to': to_id,
            'type': edge_type,
            'notes': notes
        }
    
    def extract_period_from_date(self, date_str):
        """Extract standardized period from date string"""
        if not date_str:
            return None
        
        # Check for known periods
        for period in self.egyptian_periods:
            if period.lower() in date_str.lower():
                return period
        
        # Extract dynasty numbers
        dynasty_match = re.search(r'(\d+)(?:st|nd|rd|th)\s+Dynasty', date_str, re.IGNORECASE)
        if dynasty_match:
            return f"{dynasty_match.group(1)}th Dynasty"
        
        return date_str  # Return as-is if we can't standardize
    
    def extract_hieroglyphs_from_params(self, params):
        """Extract hieroglyphs from template parameters (e.g., head parameter)"""
        if not params:
            return None
        
        # If params is a string, parse it
        if isinstance(params, str):
            # Look for head=<hiero>...</hiero> or head=hieroglyphs pattern
            match = re.search(r'head=<hiero>([^<]+)</hiero>', params)
            if match:
                return match.group(1)
            
            # Look for head=something (without hiero tags)
            match = re.search(r'head=([^|]+)', params)
            if match:
                return match.group(1).strip()
        
        # If params is a dict
        elif isinstance(params, dict):
            head = params.get('head', '')
            if head:
                # Extract hieroglyphs from <hiero> tags
                match = re.search(r'<hiero>([^<]+)</hiero>', head)
                if match:
                    return match.group(1)
                # If no tags, the whole head might be hieroglyphs
                return head
        
        return None
    
    def build_networks_from_parsed_data(self, egy_data, dem_data, cop_data):
        """
        Build ego-centric lemma networks.
        
        Strategy:
        1. For each Egyptian lemma etymology, create ONE network
        2. Add alternative forms to that network
        3. Find descendants (Demotic/Coptic) and add them as leaf nodes
        4. Add alternative forms of descendants
        5. For compounds, add parent words as leaf nodes
        
        Returns: List of network dictionaries
        """
        print("Building ego-centric lemma networks...")
        print("="*80)
        
        # First pass: Build Egyptian lemma networks
        print("\n1. Building Egyptian lemma networks...")
        egy_networks = self.build_egyptian_networks(egy_data)
        print(f"   Created {len(egy_networks)} Egyptian lemma networks")
        
        # Second pass: Add descendants to Egyptian networks
        print("\n2. Adding Demotic descendants to Egyptian networks...")
        dem_count = self.add_demotic_descendants(egy_networks, egy_data, dem_data)
        print(f"   Added {dem_count} Demotic descendant nodes")
        
        print("\n3. Adding Coptic descendants to Egyptian networks...")
        cop_count = self.add_coptic_descendants(egy_networks, egy_data, cop_data)
        print(f"   Added {cop_count} Coptic descendant nodes")
        
        # Third pass: Create standalone networks for Demotic/Coptic lemmas without Egyptian ancestors
        print("\n4. Creating standalone Demotic networks...")
        dem_standalone = self.build_demotic_standalone_networks(dem_data, egy_data)
        print(f"   Created {len(dem_standalone)} standalone Demotic networks")
        
        print("\n5. Creating standalone Coptic networks...")
        cop_standalone = self.build_coptic_standalone_networks(cop_data, egy_data, dem_data)
        print(f"   Created {len(cop_standalone)} standalone Coptic networks")
        
        # Combine all networks
        self.networks = egy_networks + dem_standalone + cop_standalone
        
        print(f"\n{'='*80}")
        print(f"Total networks created: {len(self.networks)}")
        print(f"  - Egyptian-rooted: {len(egy_networks)}")
        print(f"  - Demotic-rooted: {len(dem_standalone)}")
        print(f"  - Coptic-rooted: {len(cop_standalone)}")
        
        return self.networks
    
    def build_egyptian_networks(self, egy_data):
        """
        Build one network per Egyptian lemma etymology.
        Each network contains the main form + alternative forms.
        """
        networks = []
        
        for lemma_form, entry in egy_data.items():
            etymologies = entry.get('etymologies', [])
            
            for etym_idx, etymology in enumerate(etymologies):
                # Create network for this etymology
                network = {
                    'network_id': self.get_new_network_id(),
                    'root_lemma': lemma_form,
                    'root_language': 'egy',
                    'root_etymology_index': etym_idx,
                    'nodes': [],
                    'edges': []
                }
                
                # Track main nodes for each POS to create VARIANT edges between them
                pos_main_nodes = []
                
                # Track which descendants/derived terms we've added to avoid duplicates
                added_descendants = set()  # Track (language, form) pairs
                added_derived_terms = set()  # Track Egyptian derived forms
                
                # Process each definition in this etymology
                for defn_idx, defn in enumerate(etymology.get('definitions', [])):
                    pos = defn.get('part_of_speech', 'unknown')
                    meanings = defn.get('definitions', [])
                    
                    # Skip if this is "alternative form of" another word
                    if self.is_alternative_form_of(meanings):
                        continue
                    
                    # Extract hieroglyphs from definition or parameters
                    hieroglyphs = defn.get('hieroglyphs')
                    if not hieroglyphs:
                        params = defn.get('parameters', {})
                        hieroglyphs = self.extract_hieroglyphs_from_params(params)
                    
                    # Strip <hiero> tags if present
                    if hieroglyphs:
                        hieroglyphs = re.sub(r'</?hiero>', '', hieroglyphs).strip()
                    
                    # Create main lemma node for this POS
                    main_node = self.create_node(
                        language='egy',
                        form=lemma_form,
                        pos=pos,
                        meanings=meanings,
                        hieroglyphs=hieroglyphs,
                        etymology_index=etym_idx,
                        definition_index=defn_idx  # Track which definition this is
                    )
                    network['nodes'].append(main_node)
                    pos_main_nodes.append(main_node)
                    
                    # Add alternative forms as variant nodes
                    alt_forms = defn.get('alternative_forms', [])
                    for alt in alt_forms:
                        alt_hieroglyphs = alt.get('hieroglyphs')
                        # Strip <hiero> tags from alternative forms
                        if alt_hieroglyphs:
                            alt_hieroglyphs = re.sub(r'</?hiero>', '', alt_hieroglyphs).strip()
                        
                        alt_translit = alt.get('transliteration') or alt.get('form') or lemma_form
                        period = self.extract_period_from_date(alt.get('date'))
                        
                        # Create variant node
                        variant_node = self.create_node(
                            language='egy',
                            form=alt_translit,
                            pos=pos,
                            meanings=meanings,  # Same meanings as main form
                            hieroglyphs=alt_hieroglyphs,
                            transliteration=alt_translit,
                            period=period,
                            etymology_index=etym_idx,
                            definition_index=defn_idx
                        )
                        network['nodes'].append(variant_node)
                        
                        # Create VARIANT edge from main to alternative
                        period_str = period or 'undated'
                        edge = self.create_edge(
                            from_id=main_node['id'],
                            to_id=variant_node['id'],
                            edge_type='VARIANT',
                            notes=f'Hieroglyphic variant ({period_str})'
                        )
                        network['edges'].append(edge)
                    
                    # Add descendants listed in this definition (hierarchical)
                    descendants = defn.get('descendants', [])
                    
                    def process_descendants_recursive(desc_list, parent_node, parent_lang):
                        """Recursively process descendants and their children"""
                        for desc in desc_list:
                            desc_lang = desc.get('language', '')
                            desc_word = desc.get('word', '').split('<')[0].strip()
                            desc_children = desc.get('children', [])
                            
                            if not desc_word:
                                continue
                            
                            # Map language codes to our standard codes
                            lang_map = {
                                'egx-dem': 'dem',
                                'cop-akh': 'cop',
                                'cop-sah': 'cop',
                                'cop-boh': 'cop',
                                'cop-fay': 'cop',
                                'cop-lyc': 'cop',
                                'cop-old': 'cop',  # Old Coptic
                                'cop-oxy': 'cop'   # Oxyrhynchite Coptic
                            }
                            
                            standard_lang = lang_map.get(desc_lang, desc_lang)
                            
                            # Process Egyptian-family languages (dem, cop) with full descendant tracking
                            # Process other languages (Greek, Arabic, etc.) as leaf nodes only
                            if standard_lang in ['dem', 'cop']:
                                # Check if node already exists
                                desc_key = (standard_lang, desc_word)
                                existing_node = next((n for n in network['nodes'] 
                                                     if n['language'] == standard_lang and n['form'] == desc_word), None)
                                
                                if existing_node:
                                    # Node exists - add dialect info and create edge if needed
                                    if standard_lang == 'cop':
                                        self.add_dialect_to_node(existing_node, desc_lang)
                                    
                                    # Create edge from parent if not already connected
                                    edge_exists = any(e['from'] == parent_node['id'] and e['to'] == existing_node['id'] 
                                                     for e in network['edges'])
                                    if not edge_exists:
                                        edge = self.create_edge(
                                            from_id=parent_node['id'],
                                            to_id=existing_node['id'],
                                            edge_type='DESCENDS',
                                            notes=f'{parent_lang.title()} → {standard_lang.title()}'
                                        )
                                        network['edges'].append(edge)
                                    
                                    # Process children
                                    if desc_children:
                                        process_descendants_recursive(desc_children, existing_node, standard_lang)
                                
                                elif desc_key not in added_descendants:
                                    # Node doesn't exist - create it
                                    added_descendants.add(desc_key)
                                    
                                    desc_node = self.create_node(
                                        language=standard_lang,
                                        form=desc_word,
                                        pos=pos,  # Assume same POS as parent
                                        meanings=[],  # No meaning info from desc template
                                        dialect=desc_lang if standard_lang == 'cop' else None
                                    )
                                    network['nodes'].append(desc_node)
                                    
                                    # Create DESCENDS edge from parent to this descendant
                                    edge = self.create_edge(
                                        from_id=parent_node['id'],
                                        to_id=desc_node['id'],
                                        edge_type='DESCENDS',
                                        notes=f'{parent_lang.title()} → {standard_lang.title()}'
                                    )
                                    network['edges'].append(edge)
                                    
                                    # Recursively process children of this descendant
                                    if desc_children:
                                        process_descendants_recursive(desc_children, desc_node, standard_lang)
                            
                            else:
                                # Non-Egyptian language (Greek, Arabic, etc.) - add as leaf node
                                # Also add their immediate children as additional leaf nodes
                                desc_key = (standard_lang, desc_word)
                                
                                # Check if already added
                                existing_node = next((n for n in network['nodes'] 
                                                     if n['language'] == standard_lang and n['form'] == desc_word), None)
                                
                                if not existing_node and desc_key not in added_descendants:
                                    added_descendants.add(desc_key)
                                    
                                    # Create leaf node for non-Egyptian descendant
                                    desc_node = self.create_node(
                                        language=standard_lang,
                                        form=desc_word,
                                        pos=pos,
                                        meanings=[],
                                        dialect=None
                                    )
                                    network['nodes'].append(desc_node)
                                    
                                    # Create DESCENDS edge from parent
                                    edge = self.create_edge(
                                        from_id=parent_node['id'],
                                        to_id=desc_node['id'],
                                        edge_type='DESCENDS',
                                        notes=f'{parent_lang.title()} → {standard_lang.title()}'
                                    )
                                    network['edges'].append(edge)
                                    
                                    # Add immediate children as leaf nodes (one level only)
                                    if desc_children:
                                        for child in desc_children:
                                            child_lang = child.get('language', '')
                                            child_word = child.get('word', '')
                                            if child_lang and child_word:
                                                child_key = (child_lang, child_word)
                                                if child_key not in added_descendants:
                                                    added_descendants.add(child_key)
                                                    
                                                    child_node = self.create_node(
                                                        language=child_lang,
                                                        form=child_word,
                                                        pos=pos,
                                                        meanings=[],
                                                        dialect=None
                                                    )
                                                    network['nodes'].append(child_node)
                                                    
                                                    # Edge from non-Egyptian parent to child
                                                    edge = self.create_edge(
                                                        from_id=desc_node['id'],
                                                        to_id=child_node['id'],
                                                        edge_type='DESCENDS',
                                                        notes=f'{standard_lang.title()} → {child_lang.title()}'
                                                    )
                                                    network['edges'].append(edge)
                                    
                                elif existing_node:
                                    # Node exists - just add edge if needed
                                    edge_exists = any(e['from'] == parent_node['id'] and e['to'] == existing_node['id'] 
                                                     for e in network['edges'])
                                    if not edge_exists:
                                        edge = self.create_edge(
                                            from_id=parent_node['id'],
                                            to_id=existing_node['id'],
                                            edge_type='DESCENDS',
                                            notes=f'{parent_lang.title()} → {standard_lang.title()}'
                                        )
                                        network['edges'].append(edge)
                    
                    # Start recursive processing with main_node as root
                    process_descendants_recursive(descendants, main_node, 'egy')
                    
                    # Add derived terms listed in this definition
                    derived_terms = defn.get('derived_terms', [])
                    for derived_form in derived_terms:
                        if not derived_form or derived_form == lemma_form:
                            continue
                        
                        # Skip if already added
                        if derived_form in added_derived_terms:
                            continue
                        added_derived_terms.add(derived_form)
                        
                        # Create derived term node (Egyptian)
                        derived_node = self.create_node(
                            language='egy',
                            form=derived_form,
                            pos='unknown',  # We don't know the POS
                            meanings=[f'Derived from {lemma_form}'],
                            etymology_index=etym_idx
                        )
                        network['nodes'].append(derived_node)
                        
                        # Create DERIVED edge
                        edge = self.create_edge(
                            from_id=main_node['id'],
                            to_id=derived_node['id'],
                            edge_type='DERIVED',
                            notes=f'Derived term'
                        )
                        network['edges'].append(edge)
                
                # Process etymology components (for compound words)
                # If this lemma is a compound, add its component words to the network
                etymology_components = etymology.get('etymology_components', [])
                if etymology_components and pos_main_nodes:
                    # Use the first main node as the compound word node
                    compound_node = pos_main_nodes[0]
                    
                    for component in etymology_components:
                        component_form = component.get('form', '')
                        if not component_form or component_form == lemma_form:
                            continue
                        
                        # Look for this component in other networks or create a stub node
                        component_network = self.find_egyptian_network(networks, component_form)
                        
                        # Check if we already have this component in the current network
                        existing_component = next((n for n in network['nodes'] 
                                                  if n['language'] == 'egy' and n['form'] == component_form), None)
                        
                        if existing_component:
                            component_node = existing_component
                        elif component_network and component_network['nodes']:
                            # Use the first node from the component's network as reference
                            # Create a copy in this network
                            ref_node = component_network['nodes'][0]
                            component_node = self.create_node(
                                language='egy',
                                form=component_form,
                                pos=ref_node.get('part_of_speech', 'unknown'),
                                meanings=ref_node.get('meanings', []),
                                hieroglyphs=ref_node.get('hieroglyphs'),
                                etymology_index=ref_node.get('etymology_index')
                            )
                            network['nodes'].append(component_node)
                        else:
                            # Create stub node for component
                            component_node = self.create_node(
                                language='egy',
                                form=component_form,
                                pos='unknown',
                                meanings=[f'Component of {lemma_form}'],
                                etymology_index=etym_idx
                            )
                            network['nodes'].append(component_node)
                        
                        # Create COMPONENT edge from component to compound
                        edge = self.create_edge(
                            from_id=component_node['id'],
                            to_id=compound_node['id'],
                            edge_type='COMPONENT',
                            notes=f'Component of compound word'
                        )
                        network['edges'].append(edge)
                
                # Process etymology ancestors (borrowed/derived from other languages)
                # Add source words from Greek, Latin, Semitic, etc.
                etymology_ancestors = etymology.get('etymology_ancestors', [])
                if etymology_ancestors and pos_main_nodes:
                    # Use the first main node as the target
                    target_node = pos_main_nodes[0]
                    
                    for ancestor in etymology_ancestors:
                        ancestor_lang = ancestor.get('language', '')
                        ancestor_form = ancestor.get('form', '')
                        ancestor_type = ancestor.get('type', 'der')  # bor, der, inh
                        
                        if not ancestor_form or not ancestor_lang:
                            continue
                        
                        # Skip if it's from Egyptian/Demotic (those are handled differently)
                        if ancestor_lang in ['egy', 'egx-dem', 'dem']:
                            continue
                        
                        # Check if we already have this ancestor in the network
                        existing_ancestor = next((n for n in network['nodes'] 
                                                 if n['language'] == ancestor_lang and n['form'] == ancestor_form), None)
                        
                        if not existing_ancestor:
                            # Create node for foreign language ancestor
                            ancestor_node = self.create_node(
                                language=ancestor_lang,
                                form=ancestor_form,
                                pos='unknown',
                                meanings=[f'Source of {lemma_form}'],
                                etymology_index=None
                            )
                            network['nodes'].append(ancestor_node)
                        else:
                            ancestor_node = existing_ancestor
                        
                        # Create edge from ancestor to descendant
                        # Type can be BORROWED, DERIVED, or INHERITED
                        edge_type = 'BORROWED' if ancestor_type in ['bor', 'borrowed'] else 'DERIVED'
                        if ancestor_type in ['inh', 'inherited']:
                            edge_type = 'INHERITED'
                        
                        edge = self.create_edge(
                            from_id=ancestor_node['id'],
                            to_id=target_node['id'],
                            edge_type=edge_type,
                            notes=f'{ancestor_lang.title()} → Egy'
                        )
                        network['edges'].append(edge)
                
                # Create VARIANT edges between different POS main nodes
                # (e.g., verb wꜥb ↔ adjective wꜥb ↔ noun wꜥb)
                if len(pos_main_nodes) > 1:
                    for i in range(len(pos_main_nodes) - 1):
                        pos1 = pos_main_nodes[i]['part_of_speech']
                        pos2 = pos_main_nodes[i + 1]['part_of_speech']
                        edge = self.create_edge(
                            from_id=pos_main_nodes[i]['id'],
                            to_id=pos_main_nodes[i + 1]['id'],
                            edge_type='VARIANT',
                            notes=f'Part-of-speech variant: {pos1} ↔ {pos2}'
                        )
                        network['edges'].append(edge)
                
                # Only add network if it has nodes
                if network['nodes']:
                    networks.append(network)
        
        return networks
    
    def is_alternative_form_of(self, meanings):
        """Check if meanings indicate this is an alternative form of another word"""
        if not meanings:
            return False
        
        first_meaning = meanings[0].lower()
        return (first_meaning.startswith('alternative form of') or 
                first_meaning.startswith('alternative spelling of'))
    
    def find_egyptian_network(self, networks, lemma_form, etym_idx=None):
        """Find the Egyptian network for a given lemma and etymology"""
        for network in networks:
            if (network['root_language'] == 'egy' and 
                network['root_lemma'] == lemma_form):
                if etym_idx is None or network['root_etymology_index'] == etym_idx:
                    return network
        return None
    
    def find_best_ancestor_match(self, nodes, ancestor_form, descendant_pos, descendant_meanings):
        """
        Find the best matching Egyptian ancestor node for a descendant.
        Prefers POS match, then falls back to any matching form.
        
        This handles cases where one Egyptian etymology has multiple POS variants
        (e.g., verb/adj/noun wꜥb) and descendants should attach to the right one.
        """
        # Filter to Egyptian nodes with matching form
        egy_nodes = [n for n in nodes if n['language'] == 'egy' and n['form'] == ancestor_form]
        
        if not egy_nodes:
            return None
        
        # If only one match, use it
        if len(egy_nodes) == 1:
            return egy_nodes[0]
        
        # Try to match by POS
        pos_matches = [n for n in egy_nodes if n.get('part_of_speech') == descendant_pos]
        if pos_matches:
            return pos_matches[0]
        
        # Try to match by meaning similarity (simple keyword match)
        if descendant_meanings:
            descendant_text = ' '.join(descendant_meanings).lower()
            best_match = None
            best_score = 0
            
            for node in egy_nodes:
                node_meanings = node.get('meanings', [])
                if node_meanings:
                    node_text = ' '.join(node_meanings).lower()
                    # Simple keyword overlap
                    common_words = set(descendant_text.split()) & set(node_text.split())
                    if len(common_words) > best_score:
                        best_score = len(common_words)
                        best_match = node
            
            if best_match:
                return best_match
        
        # Fall back to first match (prefer nodes without definition_index, i.e., older entries)
        return min(egy_nodes, key=lambda n: n.get('definition_index', 0))
    
    def add_demotic_descendants(self, egy_networks, egy_data, dem_data):
        """
        Add Demotic descendants to their Egyptian ancestor networks.
        Demotic words are added as LEAF nodes (no further expansion).
        """
        count = 0
        
        for lemma_form, entry in dem_data.items():
            etymologies = entry.get('etymologies', [])
            
            for etym_idx, etymology in enumerate(etymologies):
                # Look for Egyptian ancestor in etymology text
                egy_ancestor = self.extract_egyptian_ancestor(etymology.get('etymology_text', ''))
                
                if egy_ancestor:
                    # Find the Egyptian network to attach to
                    egy_network = self.find_egyptian_network(egy_networks, egy_ancestor)
                    
                    if egy_network:
                        # Add Demotic descendant as leaf node
                        for defn in etymology.get('definitions', []):
                            pos = defn.get('part_of_speech', 'unknown')
                            meanings = defn.get('definitions', [])
                            
                            # Check if this Demotic word already exists in the network
                            existing_dem = next((n for n in egy_network['nodes'] 
                                               if n['language'] == 'dem' and n['form'] == lemma_form), None)
                            
                            if existing_dem:
                                # Node exists - update meanings if they were empty
                                if not existing_dem.get('meanings'):
                                    existing_dem['meanings'] = meanings
                                # Update part_of_speech if it was unknown
                                if existing_dem.get('part_of_speech') in [None, 'unknown'] and pos not in [None, 'unknown']:
                                    existing_dem['part_of_speech'] = pos
                                # Set etymology_index if not already set
                                if existing_dem.get('etymology_index') is None:
                                    existing_dem['etymology_index'] = etym_idx
                                dem_node = existing_dem
                            else:
                                # Create new node
                                dem_node = self.create_node(
                                    language='dem',
                                    form=lemma_form,
                                    pos=pos,
                                    meanings=meanings,
                                    etymology_index=etym_idx
                                )
                                egy_network['nodes'].append(dem_node)
                                count += 1
                            
                            # Find the best matching Egyptian ancestor node
                            # Prefer matching by POS, then fall back to any Egyptian node with the form
                            egy_root = self.find_best_ancestor_match(
                                egy_network['nodes'],
                                egy_ancestor,
                                pos,
                                meanings
                            )
                            
                            if egy_root:
                                # Check if edge already exists
                                edge_exists = any(e['from'] == egy_root['id'] and e['to'] == dem_node['id'] 
                                                 for e in egy_network['edges'])
                                if not edge_exists:
                                    edge = self.create_edge(
                                        from_id=egy_root['id'],
                                        to_id=dem_node['id'],
                                        edge_type='DESCENDS',
                                        notes='Egyptian → Demotic'
                                    )
                                    egy_network['edges'].append(edge)
        
        return count
    
    def extract_egyptian_ancestor(self, etym_text):
        """Extract Egyptian ancestor form from etymology text"""
        if not etym_text:
            return None
        
        # Look for {{inh|dem|egy|form}} or similar patterns
        match = re.search(r'\{\{(?:inh|der|bor)\|(?:dem|egx-dem)\|egy\|([^|}]+)', etym_text)
        if match:
            ancestor = match.group(1).strip()
            # Remove any HTML tags
            ancestor = re.sub(r'<[^>]+>', '', ancestor)
            return ancestor
        
        return None
    
    def add_coptic_descendants(self, egy_networks, egy_data, cop_data):
        """
        Add Coptic descendants to their Egyptian ancestor networks.
        Coptic words are added as LEAF nodes (no further expansion).
        """
        count = 0
        
        for lemma_form, entry in cop_data.items():
            etymologies = entry.get('etymologies', [])
            
            for etym_idx, etymology in enumerate(etymologies):
                # Look for Egyptian ancestor in etymology text
                egy_ancestor = self.extract_coptic_egyptian_ancestor(etymology.get('etymology_text', ''))
                
                if egy_ancestor:
                    # Find the Egyptian network to attach to
                    egy_network = self.find_egyptian_network(egy_networks, egy_ancestor)
                    
                    if egy_network:
                        # Add Coptic descendant as leaf node
                        for defn in etymology.get('definitions', []):
                            pos = defn.get('part_of_speech', 'unknown')
                            meanings = defn.get('definitions', [])
                            dialect = self.extract_coptic_dialect(lemma_form, defn)
                            
                            # Check if this Coptic word already exists in the network
                            existing_cop = next((n for n in egy_network['nodes'] 
                                               if n['language'] == 'cop' and n['form'] == lemma_form), None)
                            
                            if existing_cop:
                                # Node exists - update dialect and meanings
                                if dialect:
                                    self.add_dialect_to_node(existing_cop, dialect)
                                # Update meanings if they were empty
                                if not existing_cop.get('meanings'):
                                    existing_cop['meanings'] = meanings
                                # Update part_of_speech if it was unknown
                                if existing_cop.get('part_of_speech') in [None, 'unknown'] and pos not in [None, 'unknown']:
                                    existing_cop['part_of_speech'] = pos
                                # Set etymology_index if not already set
                                if existing_cop.get('etymology_index') is None:
                                    existing_cop['etymology_index'] = etym_idx
                                # Don't increment count or add new node
                                cop_node = existing_cop
                            else:
                                # Create new node
                                cop_node = self.create_node(
                                    language='cop',
                                    form=lemma_form,
                                    pos=pos,
                                    meanings=meanings,
                                    dialect=dialect,
                                    etymology_index=etym_idx
                                )
                                egy_network['nodes'].append(cop_node)
                                count += 1
                            
                            # Find the best matching Egyptian ancestor node
                            # Prefer matching by POS, then fall back to any Egyptian node with the form
                            egy_root = self.find_best_ancestor_match(
                                egy_network['nodes'],
                                egy_ancestor,
                                pos,
                                meanings
                            )
                            
                            if egy_root:
                                # Check if edge already exists
                                edge_exists = any(e['from'] == egy_root['id'] and e['to'] == cop_node['id'] 
                                                 for e in egy_network['edges'])
                                if not edge_exists:
                                    edge = self.create_edge(
                                        from_id=egy_root['id'],
                                        to_id=cop_node['id'],
                                        edge_type='DESCENDS',
                                        notes='Egyptian → Coptic'
                                    )
                                    egy_network['edges'].append(edge)
        
        return count
    
    def extract_coptic_egyptian_ancestor(self, etym_text):
        """Extract Egyptian ancestor form from Coptic etymology text"""
        if not etym_text:
            return None
        
        # Look for {{inh|cop|egy|form}} or similar patterns
        match = re.search(r'\{\{(?:inh|der|bor)\|cop[^|]*\|egy\|([^|}]+)', etym_text)
        if match:
            ancestor = match.group(1).strip()
            # Remove any HTML tags
            ancestor = re.sub(r'<[^>]+>', '', ancestor)
            return ancestor
        
        return None
    
    def extract_coptic_dialect(self, lemma_form, defn):
        """Extract Coptic dialect from definition or parameters"""
        # Check parameters for dialect info
        params = defn.get('parameters', {})
        if 'dialect' in params:
            return params['dialect']
        
        # Common Coptic dialect abbreviations
        if any(d in lemma_form for d in ['ⲃ', 'ⲥ', 'ⲁ', 'ⲗ', 'ⲫ']):
            # Could detect based on Coptic letters, but this is complex
            pass
        
        return None
    
    def build_demotic_standalone_networks(self, dem_data, egy_data):
        """Build standalone networks for Demotic lemmas without Egyptian ancestors"""
        networks = []
        
        for lemma_form, entry in dem_data.items():
            etymologies = entry.get('etymologies', [])
            
            for etym_idx, etymology in enumerate(etymologies):
                # Check if this has an Egyptian ancestor
                egy_ancestor = self.extract_egyptian_ancestor(etymology.get('etymology_text', ''))
                
                # Only create standalone network if no Egyptian ancestor
                if not egy_ancestor:
                    network = {
                        'network_id': self.get_new_network_id(),
                        'root_lemma': lemma_form,
                        'root_language': 'dem',
                        'root_etymology_index': etym_idx,
                        'nodes': [],
                        'edges': []
                    }
                    
                    for defn in etymology.get('definitions', []):
                        pos = defn.get('part_of_speech', 'unknown')
                        meanings = defn.get('definitions', [])
                        
                        dem_node = self.create_node(
                            language='dem',
                            form=lemma_form,
                            pos=pos,
                            meanings=meanings
                        )
                        network['nodes'].append(dem_node)
                    
                    if network['nodes']:
                        networks.append(network)
        
        return networks
    
    def build_coptic_standalone_networks(self, cop_data, egy_data, dem_data):
        """Build standalone networks for Coptic lemmas without Egyptian ancestors"""
        networks = []
        
        for lemma_form, entry in cop_data.items():
            etymologies = entry.get('etymologies', [])
            
            for etym_idx, etymology in enumerate(etymologies):
                # Check if this has an Egyptian ancestor
                egy_ancestor = self.extract_coptic_egyptian_ancestor(etymology.get('etymology_text', ''))
                
                # Only create standalone network if no Egyptian ancestor
                if not egy_ancestor:
                    network = {
                        'network_id': self.get_new_network_id(),
                        'root_lemma': lemma_form,
                        'root_language': 'cop',
                        'root_etymology_index': etym_idx,
                        'nodes': [],
                        'edges': []
                    }
                    
                    pos_main_nodes = []
                    
                    for defn in etymology.get('definitions', []):
                        pos = defn.get('part_of_speech', 'unknown')
                        meanings = defn.get('definitions', [])
                        dialect = self.extract_coptic_dialect(lemma_form, defn)
                        
                        cop_node = self.create_node(
                            language='cop',
                            form=lemma_form,
                            pos=pos,
                            meanings=meanings,
                            dialect=dialect,
                            etymology_index=etym_idx
                        )
                        network['nodes'].append(cop_node)
                        pos_main_nodes.append(cop_node)
                    
                    # Process etymology components for Coptic compound words
                    etymology_components = etymology.get('etymology_components', [])
                    if etymology_components and pos_main_nodes:
                        # Use the first main node as the compound word node
                        compound_node = pos_main_nodes[0]
                        
                        for component in etymology_components:
                            component_form = component.get('form', '')
                            if not component_form or component_form == lemma_form:
                                continue
                            
                            # Check if we already have this component in the current network
                            existing_component = next((n for n in network['nodes'] 
                                                      if n['language'] == 'cop' and n['form'] == component_form), None)
                            
                            if not existing_component:
                                # Create stub node for component
                                component_node = self.create_node(
                                    language='cop',
                                    form=component_form,
                                    pos='unknown',
                                    meanings=[f'Component of {lemma_form}'],
                                    dialect=None
                                )
                                network['nodes'].append(component_node)
                            else:
                                component_node = existing_component
                            
                            # Create COMPONENT edge from component to compound
                            edge = self.create_edge(
                                from_id=component_node['id'],
                                to_id=compound_node['id'],
                                edge_type='COMPONENT',
                                notes=f'Component of compound word'
                            )
                            network['edges'].append(edge)
                    
                    # Process etymology ancestors (borrowed/derived from other languages)
                    # Add source words from Greek, Latin, etc.
                    etymology_ancestors = etymology.get('etymology_ancestors', [])
                    if etymology_ancestors and pos_main_nodes:
                        # Use the first main node as the target
                        target_node = pos_main_nodes[0]
                        
                        for ancestor in etymology_ancestors:
                            ancestor_lang = ancestor.get('language', '')
                            ancestor_form = ancestor.get('form', '')
                            ancestor_type = ancestor.get('type', 'der')  # bor, der, inh
                            
                            if not ancestor_form or not ancestor_lang:
                                continue
                            
                            # Skip if it's from Coptic/Egyptian/Demotic (handled differently)
                            if ancestor_lang in ['cop', 'egy', 'egx-dem', 'dem']:
                                continue
                            
                            # Check if we already have this ancestor in the network
                            existing_ancestor = next((n for n in network['nodes'] 
                                                     if n['language'] == ancestor_lang and n['form'] == ancestor_form), None)
                            
                            if not existing_ancestor:
                                # Create node for foreign language ancestor
                                ancestor_node = self.create_node(
                                    language=ancestor_lang,
                                    form=ancestor_form,
                                    pos='unknown',
                                    meanings=[f'Source of {lemma_form}'],
                                    dialect=None
                                )
                                network['nodes'].append(ancestor_node)
                            else:
                                ancestor_node = existing_ancestor
                            
                            # Create edge from ancestor to descendant
                            edge_type = 'BORROWED' if ancestor_type in ['bor', 'borrowed'] else 'DERIVED'
                            if ancestor_type in ['inh', 'inherited']:
                                edge_type = 'INHERITED'
                            
                            edge = self.create_edge(
                                from_id=ancestor_node['id'],
                                to_id=target_node['id'],
                                edge_type=edge_type,
                                notes=f'{ancestor_lang.title()} → Cop'
                            )
                            network['edges'].append(edge)
                    
                    if network['nodes']:
                        networks.append(network)
        
        return networks
    
    def export_networks(self, output_file):
        """Export networks to JSON file"""
        print(f"\nExporting {len(self.networks)} networks to {output_file}...")
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(self.networks, f, ensure_ascii=False, indent=2)
        
        # Print statistics
        total_nodes = sum(len(net['nodes']) for net in self.networks)
        total_edges = sum(len(net['edges']) for net in self.networks)
        
        print(f"Export complete!")
        print(f"  Total networks: {len(self.networks)}")
        print(f"  Total nodes: {total_nodes}")
        print(f"  Total edges: {total_edges}")
        print(f"  Average nodes per network: {total_nodes/len(self.networks):.1f}")
        print(f"  Average edges per network: {total_edges/len(self.networks):.1f}")


def main():
    print("Lemma Network Builder V2 - Ego-centric Approach")
    print("="*80)
    print()
    
    print("Loading parsed Wiktionary data...")
    
    with open('egyptian_lemmas_parsed_mwp.json', 'r', encoding='utf-8') as f:
        egy_data = json.load(f)
    
    with open('demotic_lemmas_parsed_mwp.json', 'r', encoding='utf-8') as f:
        dem_data = json.load(f)
    
    with open('coptic_lemmas_parsed_mwp.json', 'r', encoding='utf-8') as f:
        cop_data = json.load(f)
    
    print(f"Loaded {len(egy_data)} Egyptian, {len(dem_data)} Demotic, {len(cop_data)} Coptic lemmas")
    
    # Build networks
    builder = EgocentricLemmaNetworkBuilder()
    networks = builder.build_networks_from_parsed_data(egy_data, dem_data, cop_data)
    
    # Export
    builder.export_networks('lemma_networks_v2.json')
    
    print("\n" + "="*80)
    print("Network building complete!")
    print("\nThe output file 'lemma_networks_v2.json' contains:")
    print("- Each network is ego-centric, focused on ONE lemma")
    print("- Nodes: the lemma, its variants, and direct descendants (as leaf nodes)")
    print("- Edges: VARIANT (spelling/hieroglyphic), DESCENDS (cross-language)")
    print("\nThis can be used to visualize individual lemma evolution without sprawl.")


if __name__ == '__main__':
    main()
