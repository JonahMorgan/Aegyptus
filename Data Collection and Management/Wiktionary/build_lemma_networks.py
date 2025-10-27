"""
Lemma Network Builder for Egyptian Language Evolution

This script builds temporal networks showing how Egyptian words evolved across time:
- Egyptian (Old Kingdom ~2686 BCE → Greco-Roman Period ~395 CE)
- Demotic (~650 BCE → ~452 CE)
- Coptic (~200 CE → ~1300 CE, still used liturgically)

Key Design Decisions:
1. LEMMA UNIFICATION: Alternative forms are treated as the same lemma
   - Egyptian alt forms with different dates → same lemma in different periods
   - Coptic alt forms with different dialects → same lemma in different regions
   
2. TEMPORAL TRACKING: Three types of relationships
   - EVOLVES: Same language, different time period (via dated alt forms)
   - DESCENDS: Cross-language inheritance (Egyptian → Demotic → Coptic)
   - VARIANT: Same time/language, different spelling (undated alt forms, dialects)

3. NETWORK STRUCTURE: Graph-based representation
   - Nodes: {lemma, language, period/dialect, part_of_speech, meaning}
   - Edges: {relationship_type, confidence, notes}

Output: JSON with lemma networks suitable for training a temporal translation model
"""

import json
import re
from collections import defaultdict
import sys

sys.stdout.reconfigure(encoding='utf-8')

class LemmaNetworkBuilder:
    def __init__(self):
        self.networks = {}  # lemma_id -> network graph
        self.lemma_index = {}  # (language, form) -> lemma_id
        self.next_id = 0
        
        # Time period ordering (approximate)
        self.egyptian_periods = [
            'Old Kingdom', 'First Intermediate Period', 'Middle Kingdom',
            'Second Intermediate Period', 'New Kingdom', 'Third Intermediate Period',
            'Late Period', 'Ptolemaic Period', 'Greco-Roman Period',
            'Pyramid Texts', 'Coffin Texts', 'Book of the Dead'
        ]
        
    def get_or_create_node_id(self, language, form, period=None, dialect=None, hieroglyphs=None):
        """Get existing node ID or create new one"""
        # Include hieroglyphs to distinguish variants with same transliteration
        key = (language, form, period or '', dialect or '', hieroglyphs or '')
        if key not in self.lemma_index:
            self.lemma_index[key] = f"L{self.next_id:05d}"
            self.next_id += 1
        return self.lemma_index[key]
    
    def create_node(self, node_id, language, form, part_of_speech, meanings, 
                    period=None, dialect=None, hieroglyphs=None, transliteration=None):
        """Create a node in the network"""
        return {
            'id': node_id,
            'language': language,
            'form': form,
            'transliteration': transliteration,
            'hieroglyphs': hieroglyphs,
            'part_of_speech': part_of_speech,
            'meanings': meanings,
            'period': period,
            'dialect': dialect
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
        dynasty_match = re.search(r'(\d+)(?:st|nd|rd|th)\s+Dynasty', date_str)
        if dynasty_match:
            return f"{dynasty_match.group(1)}th Dynasty"
        
        return date_str  # Return as-is if we can't standardize
    
    def get_period_rank(self, period):
        """Get chronological ranking of a period (lower = earlier)"""
        if not period:
            return 999
        
        # Textual periods
        period_rankings = {
            'Pyramid Texts': 1,
            'Old Kingdom': 2,
            'First Intermediate Period': 3,
            'Middle Kingdom': 4,
            'Coffin Texts': 4,  # Middle Kingdom era
            'Second Intermediate Period': 5,
            'New Kingdom': 6,
            'Book of the Dead': 6,  # New Kingdom era
            'Third Intermediate Period': 7,
            'Late Period': 8,
            'Late Egyptian': 8,
            'Ptolemaic Period': 9,
            'Greco-Roman Period': 10,
        }
        
        # Check if period is in our known rankings
        for known_period, rank in period_rankings.items():
            if known_period.lower() in period.lower():
                return rank
        
        # Dynasty numbers (approximate chronology)
        dynasty_match = re.search(r'(\d+)(?:st|nd|rd|th)', period)
        if dynasty_match:
            dynasty_num = int(dynasty_match.group(1))
            # Map dynasties to approximate periods
            if dynasty_num <= 6:
                return 2  # Old Kingdom
            elif dynasty_num <= 11:
                return 3  # First Intermediate Period
            elif dynasty_num <= 13:
                return 4  # Middle Kingdom
            elif dynasty_num <= 17:
                return 5  # Second Intermediate Period
            elif dynasty_num <= 20:
                return 6  # New Kingdom
            elif dynasty_num <= 25:
                return 7  # Third Intermediate Period
            elif dynasty_num <= 31:
                return 8  # Late Period
            else:
                return 9  # Ptolemaic/Greco-Roman
        
        # Default: unknown period
        return 500
    
    def parse_etymology_for_ancestor(self, etymology_text, current_lang):
        """Extract ancestor language and form from etymology text"""
        # Pattern: {{inh|current_lang|ancestor_lang|ancestor_form|...}}
        pattern = r'\{\{inh\|' + re.escape(current_lang) + r'\|([^|]+)\|([^|}\s]+)'
        match = re.search(pattern, etymology_text)
        
        if match:
            ancestor_lang = match.group(1).strip()
            ancestor_form = match.group(2).strip()
            # Remove HTML/hieroglyphs
            ancestor_form = re.sub(r'<hiero>.*?</hiero>', '', ancestor_form)
            return ancestor_lang, ancestor_form
        
        # Also check for {{m|lang|form}} patterns
        pattern2 = r'\{\{m\|([^|]+)\|([^|}\s]+)'
        match2 = re.search(pattern2, etymology_text)
        if match2:
            return match2.group(1).strip(), match2.group(2).strip()
        
        return None, None
    
    def build_networks_from_parsed_data(self, egy_data, dem_data, cop_data):
        """Build lemma networks from all three language datasets"""
        
        print("Building lemma networks...")
        print("="*80)
        
        # Process Egyptian lemmas
        print("\n1. Processing Egyptian lemmas...")
        egy_count = self.process_egyptian_lemmas(egy_data)
        print(f"   Created {egy_count} Egyptian nodes")
        
        # Process Demotic lemmas (with links to Egyptian)
        print("\n2. Processing Demotic lemmas...")
        dem_count = self.process_demotic_lemmas(dem_data, egy_data)
        print(f"   Created {dem_count} Demotic nodes")
        
        # Process Coptic lemmas (with links to Demotic and Egyptian)
        print("\n3. Processing Coptic lemmas...")
        cop_count = self.process_coptic_lemmas(cop_data, dem_data, egy_data)
        print(f"   Created {cop_count} Coptic nodes")
        
        # Cleanup: Remove direct Egyptian→Coptic edges when Demotic descendant exists
        print("\n4. Cleaning up routing (removing direct Egyptian→Coptic edges where Demotic exists)...")
        removed_edges = self.cleanup_coptic_routing()
        print(f"   Removed {removed_edges} direct Egyptian→Coptic edges")
        
        print(f"\nTotal networks created: {len(self.networks)}")
        return self.networks
    
    def process_egyptian_lemmas(self, egy_data):
        """Process Egyptian lemmas with temporal evolution via alternative forms"""
        node_count = 0
        
        for lemma_form, entry in egy_data.items():
            for etym in entry.get('etymologies', []):
                for defn in etym.get('definitions', []):
                    pos = defn.get('part_of_speech', 'unknown')
                    meanings = defn.get('definitions', [])
                    
                    # Collect all forms (main + alternatives), separating by inflection
                    # Key: (inflection_type, base_form) - e.g., ('plural', 'jꜥnw') or ('singular', '')
                    forms_by_inflection = {}
                    
                    # Main lemma form (singular/base form)
                    main_id = self.get_or_create_node_id('egy', lemma_form)
                    main_node = self.create_node(
                        main_id, 'egy', lemma_form, pos, meanings
                    )
                    
                    inflection_key = ('base', '')
                    if inflection_key not in forms_by_inflection:
                        forms_by_inflection[inflection_key] = []
                    
                    forms_by_inflection[inflection_key].append({
                        'id': main_id,
                        'node': main_node,
                        'period': None,
                        'period_rank': 999  # Undated = lowest priority
                    })
                    
                    # Alternative forms - check if they're inflections (plural, dual, etc.)
                    for alt_form in defn.get('alternative_forms', []):
                        alt_hieroglyphs = alt_form.get('hieroglyphs')
                        alt_translit = alt_form.get('transliteration', alt_form.get('form'))
                        period = self.extract_period_from_date(alt_form.get('date'))
                        title = alt_form.get('title', '')
                        note = alt_form.get('note', '')
                        
                        # Detect inflection type from title/note
                        inflection_info = f"{title} {note}".lower()
                        inflection_type = 'base'
                        inflection_form = ''
                        
                        if 'plural' in inflection_info or 'pl.' in inflection_info:
                            inflection_type = 'plural'
                            # Try to extract the plural form from title
                            # Pattern: "writings of plural {{m-self|egy|lemma|plural_form}}"
                            import re
                            plural_match = re.search(r'\{\{m-self\|egy\|[^|]+\|([^}]+)\}\}', title)
                            if plural_match:
                                inflection_form = plural_match.group(1)
                            else:
                                inflection_form = alt_translit
                        elif 'dual' in inflection_info:
                            inflection_type = 'dual'
                            inflection_form = alt_translit
                        elif 'feminine' in inflection_info or 'fem.' in inflection_info:
                            inflection_type = 'feminine'
                            inflection_form = alt_translit
                        
                        inflection_key = (inflection_type, inflection_form)
                        
                        alt_id = self.get_or_create_node_id('egy', alt_translit, period=period, hieroglyphs=alt_hieroglyphs)
                        alt_node = self.create_node(
                            alt_id, 'egy', alt_translit, pos, meanings,
                            period=period,
                            hieroglyphs=alt_hieroglyphs,
                            transliteration=alt_translit
                        )
                        
                        # Get period rank for sorting
                        period_rank = self.get_period_rank(period) if period else 999
                        
                        if inflection_key not in forms_by_inflection:
                            forms_by_inflection[inflection_key] = []
                        
                        forms_by_inflection[inflection_key].append({
                            'id': alt_id,
                            'node': alt_node,
                            'period': period,
                            'period_rank': period_rank,
                            'note': note,
                            'title': title
                        })
                    
                    # Create separate networks for each inflection type
                    for (inflection_type, inflection_form), all_forms in forms_by_inflection.items():
                        # Determine network ID based on inflection
                        if inflection_type == 'base':
                            network_id = main_id
                            network_label = lemma_form
                        else:
                            # For inflections, use the inflection form as base
                            # Create a unique network ID for this inflection
                            inflection_base = inflection_form if inflection_form else f"{lemma_form}_{inflection_type}"
                            network_id = self.get_or_create_node_id('egy', inflection_base, dialect=inflection_type)
                            network_label = f"{inflection_base} ({inflection_type})"
                        
                        # Find or create network
                        if network_id not in self.networks:
                            # Use main lemma form (undated) as root if available, otherwise earliest dated form
                            # The main lemma is always first in all_forms list (added before alternatives)
                            root_node = all_forms[0]['node']  # This is always the main lemma form
                            
                            self.networks[network_id] = {
                                'root_node': root_node,
                                'nodes': [],
                                'edges': [],
                                'has_demotic_descendant': False  # Track if Egyptian has Demotic descendant
                            }
                        
                        network = self.networks[network_id]
                        
                        # Add all nodes (avoiding duplicates)
                        for form_data in all_forms:
                            if not any(n['id'] == form_data['id'] for n in network['nodes']):
                                network['nodes'].append(form_data['node'])
                                node_count += 1
                        
                        # Create edges between dated forms
                        # Group forms by period to find temporal evolution
                        by_period = {}
                        for form_data in all_forms:
                            period_rank = form_data.get('period_rank', 999)
                            if period_rank not in by_period:
                                by_period[period_rank] = []
                            by_period[period_rank].append(form_data)
                        
                        # Get distinct periods in chronological order
                        sorted_periods = sorted(by_period.keys())
                        
                        # Connect undated root to earliest dated form (DESCENDS from lemma to first attestation)
                        undated_forms = by_period.get(999, [])
                        dated_periods = [p for p in sorted_periods if p < 500]
                        
                        if undated_forms and dated_periods:
                            # Connect root (undated main lemma) to earliest dated form
                            root_form = undated_forms[0]  # Main lemma (should be first)
                            earliest_period = dated_periods[0]
                            earliest_forms = by_period[earliest_period]
                            
                            if earliest_forms:
                                edge = {
                                    'from': root_form['id'],
                                    'to': earliest_forms[0]['id'],
                                    'type': 'DESCENDS',
                                    'notes': f"First attestation in {earliest_forms[0].get('period', 'dated period')}"
                                }
                                network['edges'].append(edge)
                        
                        # For EVOLVES edges: Only connect if transliteration changes across periods
                        # This represents actual phonetic/spelling evolution, not just variant writings
                        for i in range(len(dated_periods) - 1):
                            current_period = dated_periods[i]
                            next_period = dated_periods[i + 1]
                            
                            current_forms = by_period[current_period]
                            next_forms = by_period[next_period]
                            
                            # Get unique transliterations for each period
                            current_translits = {f['node']['form'] for f in current_forms}
                            next_translits = {f['node']['form'] for f in next_forms}
                            
                            # If transliterations changed between periods, it's evolution
                            if current_translits != next_translits:
                                # Connect representative forms from each period
                                # Pick first form from each unique transliteration group
                                for curr_form in current_forms:
                                    curr_translit = curr_form['node']['form']
                                    # Find if this transliteration appears in next period
                                    matching_next = [f for f in next_forms if f['node']['form'] == curr_translit]
                                    
                                    if matching_next:
                                        # Same transliteration continues - connect first instances
                                        edge = {
                                            'from': curr_form['id'],
                                            'to': matching_next[0]['id'],
                                            'type': 'EVOLVES',
                                            'notes': f"Continues from {curr_form.get('period', '?')} to {matching_next[0].get('period', '?')}"
                                        }
                                        network['edges'].append(edge)
                                        break  # Only connect once per transliteration group
                                
                                # Also connect forms where transliteration changed
                                # Find forms unique to current period that don't continue
                                for curr_form in current_forms:
                                    curr_translit = curr_form['node']['form']
                                    if curr_translit not in next_translits:
                                        # This form disappeared or changed - try to find closest match
                                        # For now, connect to the most common form in next period
                                        if next_forms:
                                            # Find most common transliteration in next period
                                            from collections import Counter
                                            next_translit_counts = Counter(f['node']['form'] for f in next_forms)
                                            most_common_translit = next_translit_counts.most_common(1)[0][0]
                                            most_common_form = next((f for f in next_forms if f['node']['form'] == most_common_translit), None)
                                            
                                            if most_common_form:
                                                edge = {
                                                    'from': curr_form['id'],
                                                    'to': most_common_form['id'],
                                                    'type': 'EVOLVES',
                                                    'notes': f"Form change: {curr_translit} → {most_common_translit}"
                                                }
                                                network['edges'].append(edge)
                                                break  # Only connect once
                        
                        # Create VARIANT edges: Different forms in the same period
                        for period_rank, forms in by_period.items():
                            if len(forms) > 1:
                                # Group by transliteration within this period
                                by_translit_in_period = {}
                                for form_data in forms:
                                    translit = form_data['node']['form']
                                    if translit not in by_translit_in_period:
                                        by_translit_in_period[translit] = []
                                    by_translit_in_period[translit].append(form_data)
                                
                                # Connect different hieroglyphic writings of same transliteration (true variants)
                                for translit, translit_forms in by_translit_in_period.items():
                                    if len(translit_forms) > 1:
                                        # Connect all to first one as the canonical form
                                        canonical = translit_forms[0]
                                        for variant in translit_forms[1:]:
                                            edge = {
                                                'from': canonical['id'],
                                                'to': variant['id'],
                                                'type': 'VARIANT',
                                                'notes': f"Hieroglyphic variant in {variant.get('period', 'same period')}"
                                            }
                                            network['edges'].append(edge)
                                
                                # Connect different transliterations in same period (spelling variants)
                                if len(by_translit_in_period) > 1:
                                    # Pick most common as canonical
                                    canonical_translit = max(by_translit_in_period.items(), key=lambda x: len(x[1]))[0]
                                    canonical_form = by_translit_in_period[canonical_translit][0]
                                    
                                    for translit, translit_forms in by_translit_in_period.items():
                                        if translit != canonical_translit:
                                            edge = {
                                                'from': canonical_form['id'],
                                                'to': translit_forms[0]['id'],
                                                'type': 'VARIANT',
                                                'notes': f"Spelling variant in {translit_forms[0].get('period', 'same period')}"
                                            }
                                            network['edges'].append(edge)
                        
                        # Add descendants (to Demotic/Coptic) - only from base form network
                        if inflection_type == 'base':
                            # Determine which Egyptian node should be the parent for descendants
                            # Use the latest dated form if available, otherwise the main undated form
                            dated_periods = [p for p in sorted_periods if p < 500]
                            
                            if dated_periods:
                                # Get the latest (highest ranked) period
                                latest_period = dated_periods[-1]
                                latest_forms = by_period[latest_period]
                                # Use the first form from the latest period as the parent
                                parent_egy_id = latest_forms[0]['id']
                            else:
                                # No dated forms, use the main undated lemma
                                parent_egy_id = main_id
                            
                            for desc in defn.get('descendants', []):
                                desc_lang = desc.get('language')
                                desc_word = desc.get('word')
                                
                                if desc_lang and desc_word:
                                    # Map language codes
                                    if desc_lang == 'egx-dem':
                                        desc_lang_code = 'dem'
                                        # Mark that this Egyptian network has a Demotic descendant
                                        network['has_demotic_descendant'] = True
                                    elif desc_lang == 'cop':
                                        desc_lang_code = 'cop'
                                    else:
                                        desc_lang_code = desc_lang
                                    
                                    # Create placeholder descendant node if not exists
                                    desc_id = self.get_or_create_node_id(desc_lang_code, desc_word)
                                    
                                    # Add node to network if not already there
                                    if not any(n['id'] == desc_id for n in network['nodes']):
                                        desc_node = self.create_node(desc_id, desc_lang_code, desc_word, pos, [])
                                        network['nodes'].append(desc_node)
                                    
                                    # Create edge from latest Egyptian form (not root)
                                    # Note: Egyptian→Coptic edges will be rerouted through Demotic
                                    # in cleanup_coptic_routing() if Demotic exists
                                    edge = {
                                        'from': parent_egy_id,
                                        'to': desc_id,
                                        'type': 'DESCENDS',
                                        'target_language': desc_lang
                                    }
                                    network['edges'].append(edge)
        
        return node_count
    
    def process_demotic_lemmas(self, dem_data, egy_data):
        """Process Demotic lemmas with inheritance from Egyptian"""
        node_count = 0
        
        for lemma_form, entry in dem_data.items():
            for etym in entry.get('etymologies', []):
                etym_text = etym.get('etymology_text', '')
                
                # Find Egyptian ancestor
                ancestor_lang, ancestor_form = self.parse_etymology_for_ancestor(etym_text, 'egx-dem')
                
                for defn in etym.get('definitions', []):
                    pos = defn.get('part_of_speech', 'unknown')
                    meanings = defn.get('definitions', [])
                    
                    # Create Demotic node
                    dem_id = self.get_or_create_node_id('dem', lemma_form)
                    dem_node = self.create_node(dem_id, 'dem', lemma_form, pos, meanings)
                    
                    # If has Egyptian ancestor, add to that network
                    if ancestor_lang == 'egy' and ancestor_form:
                        # Find the Egyptian network
                        egy_id = self.get_or_create_node_id('egy', ancestor_form)
                        
                        if egy_id in self.networks:
                            network = self.networks[egy_id]
                        else:
                            # Create a minimal network if ancestor not found
                            network = {
                                'root_node': self.create_node(egy_id, 'egy', ancestor_form, pos, []),
                                'nodes': [self.create_node(egy_id, 'egy', ancestor_form, pos, [])],
                                'edges': [],
                                'has_demotic_descendant': False
                            }
                            self.networks[egy_id] = network
                        
                        # Mark that this network now has a Demotic descendant
                        network['has_demotic_descendant'] = True
                        
                        # Find the latest Egyptian form in the network to connect from
                        # This should be the most recent dated Egyptian node
                        egy_nodes = [n for n in network['nodes'] if n['language'] == 'egy']
                        
                        # Find the node with the latest period (highest rank among dated forms)
                        latest_egy_node = None
                        latest_rank = -1
                        
                        for egy_node in egy_nodes:
                            period = egy_node.get('period')
                            if period:
                                rank = self.get_period_rank(period)
                                if rank < 500 and rank > latest_rank:  # Dated form (not undated 999)
                                    latest_rank = rank
                                    latest_egy_node = egy_node
                        
                        # If no dated forms found, use the root node
                        if not latest_egy_node:
                            latest_egy_node = network['root_node']
                        
                        parent_egy_id = latest_egy_node['id']
                        
                        # Add Demotic node to network (update placeholder if exists)
                        existing_node = next((n for n in network['nodes'] if n['id'] == dem_id), None)
                        if existing_node:
                            # Update placeholder node with full data
                            existing_node['part_of_speech'] = pos
                            existing_node['meanings'] = meanings
                        else:
                            network['nodes'].append(dem_node)
                            node_count += 1
                        
                        # Create inheritance edge from latest Egyptian form (check if already exists)
                        edge_exists = any(e.get('from') == parent_egy_id and e.get('to') == dem_id 
                                        for e in network['edges'])
                        if not edge_exists:
                            edge = {
                                'from': parent_egy_id,
                                'to': dem_id,
                                'type': 'DESCENDS',
                                'etymology_snippet': etym_text[:200]
                            }
                            network['edges'].append(edge)
                    else:
                        # Standalone Demotic word (no known Egyptian ancestor)
                        if dem_id not in self.networks:
                            self.networks[dem_id] = {
                                'root_node': dem_node,
                                'nodes': [dem_node],
                                'edges': [],
                                'has_demotic_descendant': False
                            }
                            network = self.networks[dem_id]
                            node_count += 1
                    
                    # Add descendants (to Coptic)
                    for desc in defn.get('descendants', []):
                        desc_lang = desc.get('language')
                        desc_word = desc.get('word')
                        
                        if desc_lang and desc_word:
                            if network:
                                # Map language codes
                                desc_lang_code = 'cop' if desc_lang == 'cop' else desc_lang
                                
                                # Create placeholder descendant node
                                desc_id = self.get_or_create_node_id(desc_lang_code, desc_word)
                                
                                # Add node to network if not already there
                                if not any(n['id'] == desc_id for n in network['nodes']):
                                    desc_node = self.create_node(desc_id, desc_lang_code, desc_word, pos, [])
                                    network['nodes'].append(desc_node)
                                
                                edge = {
                                    'from': dem_id,
                                    'to': desc_id,
                                    'type': 'DESCENDS',
                                    'target_language': desc_lang
                                }
                                network['edges'].append(edge)
        
        return node_count
    
    def process_coptic_lemmas(self, cop_data, dem_data, egy_data):
        """Process Coptic lemmas with dialectal variants and inheritance"""
        node_count = 0
        
        for lemma_form, entry in cop_data.items():
            for etym in entry.get('etymologies', []):
                etym_text = etym.get('etymology_text', '')
                
                # Find ancestor (Demotic or Egyptian)
                ancestor_lang_dem, ancestor_form_dem = self.parse_etymology_for_ancestor(etym_text, 'cop')
                
                for defn in etym.get('definitions', []):
                    pos = defn.get('part_of_speech', 'unknown')
                    meanings = defn.get('definitions', [])
                    
                    # Create main Coptic node
                    cop_id = self.get_or_create_node_id('cop', lemma_form)
                    cop_node = self.create_node(cop_id, 'cop', lemma_form, pos, meanings)
                    
                    # Find the network to add to
                    network = None
                    parent_id = None
                    
                    # Try Demotic ancestor first
                    if ancestor_lang_dem == 'egx-dem' and ancestor_form_dem:
                        parent_id = self.get_or_create_node_id('dem', ancestor_form_dem)
                        network = self.networks.get(parent_id)
                        
                        # Create network with placeholder Demotic node if not found
                        if not network:
                            parent_node = self.create_node(parent_id, 'dem', ancestor_form_dem, pos, [])
                            network = {
                                'root_node': parent_node,
                                'nodes': [parent_node],
                                'edges': [],
                                'has_demotic_descendant': False
                            }
                            self.networks[parent_id] = network
                    
                    # Try Egyptian ancestor
                    if not network and ancestor_lang_dem == 'egy' and ancestor_form_dem:
                        parent_id = self.get_or_create_node_id('egy', ancestor_form_dem)
                        network = self.networks.get(parent_id)
                        
                        # Check if Egyptian network has a Demotic descendant
                        # If so, Coptic should connect through Demotic, not directly to Egyptian
                        if network and network.get('has_demotic_descendant', False):
                            # Find the Demotic node(s) in this network
                            demotic_nodes = [n for n in network['nodes'] if n['language'] == 'dem']
                            if demotic_nodes:
                                # Connect through the first Demotic descendant instead
                                parent_id = demotic_nodes[0]['id']
                                # Network stays the same, but parent changes to Demotic
                        elif not network:
                            # Create network with placeholder Egyptian node if not found
                            parent_node = self.create_node(parent_id, 'egy', ancestor_form_dem, pos, [])
                            network = {
                                'root_node': parent_node,
                                'nodes': [parent_node],
                                'edges': [],
                                'has_demotic_descendant': False
                            }
                            self.networks[parent_id] = network
                    
                    # Create standalone if no ancestor mentioned at all
                    if not network:
                        network = {
                            'root_node': cop_node,
                            'nodes': [cop_node],
                            'edges': [],
                            'has_demotic_descendant': False
                        }
                        self.networks[cop_id] = network
                        parent_id = None
                    
                    # Add Coptic node (update placeholder if exists, otherwise add new)
                    existing_node = next((n for n in network['nodes'] if n['id'] == cop_id), None)
                    if existing_node:
                        # Update placeholder node with full data
                        existing_node['part_of_speech'] = pos
                        existing_node['meanings'] = meanings
                    else:
                        network['nodes'].append(cop_node)
                        node_count += 1
                    
                    # Create inheritance edge if has parent
                    if parent_id:
                        # Check if edge already exists
                        edge_exists = any(e.get('from') == parent_id and e.get('to') == cop_id 
                                        for e in network['edges'])
                        if not edge_exists:
                            edge = {
                                'from': parent_id,
                                'to': cop_id,
                                'type': 'DESCENDS',
                                'etymology_snippet': etym_text[:200]
                            }
                            network['edges'].append(edge)
                    
                    # Add dialectal variants
                    for alt_form in defn.get('alternative_forms', []):
                        alt_form_text = alt_form.get('form')
                        dialect = alt_form.get('dialect')
                        
                        if alt_form_text:
                            alt_id = self.get_or_create_node_id('cop', alt_form_text, dialect=dialect)
                            alt_node = self.create_node(
                                alt_id, 'cop', alt_form_text, pos, meanings,
                                dialect=dialect
                            )
                            
                            if not any(n['id'] == alt_id for n in network['nodes']):
                                network['nodes'].append(alt_node)
                                node_count += 1
                            
                            # Create variant edge
                            edge = {
                                'from': cop_id,
                                'to': alt_id,
                                'type': 'VARIANT',
                                'dialect': dialect
                            }
                            network['edges'].append(edge)
        
        return node_count
    
    def export_networks(self, output_file):
        """Export networks to JSON file"""
        # Convert to list format for easier processing
        networks_list = []
        for network_id, network in self.networks.items():
            network['network_id'] = network_id
            networks_list.append(network)
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(networks_list, f, ensure_ascii=False, indent=2)
        
        print(f"\nExported {len(networks_list)} networks to {output_file}")
        
        # Print statistics
        total_nodes = sum(len(n['nodes']) for n in networks_list)
        total_edges = sum(len(n['edges']) for n in networks_list)
        
        print(f"\nStatistics:")
        print(f"  Total networks: {len(networks_list)}")
        print(f"  Total nodes: {total_nodes}")
        print(f"  Total edges: {total_edges}")
        
        # Count by relationship type
        edge_types = defaultdict(int)
        for network in networks_list:
            for edge in network['edges']:
                edge_types[edge['type']] += 1
        
        print(f"\nEdge types:")
        for edge_type, count in sorted(edge_types.items()):
            print(f"  {edge_type}: {count}")
        
        # Count nodes by language
        lang_counts = defaultdict(int)
        for network in networks_list:
            for node in network['nodes']:
                lang_counts[node['language']] += 1
        
        print(f"\nNodes by language:")
        for lang, count in sorted(lang_counts.items()):
            print(f"  {lang}: {count}")
    
    def cleanup_coptic_routing(self):
        """
        Reroute Egyptian→Coptic DESCENDS edges through Demotic when Demotic descendant exists.
        Instead of removing these edges, we change them to go Demotic→Coptic.
        """
        rerouted_count = 0
        
        for network_id, network in self.networks.items():
            # Only process networks with Demotic descendants
            if not network.get('has_demotic_descendant', False):
                continue
            
            # Find the Demotic node(s) in this network
            demotic_nodes = [n for n in network['nodes'] if n['language'] == 'dem']
            if not demotic_nodes:
                continue
            
            # Use first Demotic node as the new parent for Coptic
            demotic_id = demotic_nodes[0]['id']
            
            # Find all Egyptian→Coptic DESCENDS edges and reroute them
            for edge in network['edges']:
                if edge['type'] != 'DESCENDS':
                    continue
                
                # Get source and target nodes
                source_node = next((n for n in network['nodes'] if n['id'] == edge['from']), None)
                target_node = next((n for n in network['nodes'] if n['id'] == edge['to']), None)
                
                if not source_node or not target_node:
                    continue
                
                # Check if it's Egyptian→Coptic (including dialect variants like cop-boh, cop-sah)
                if source_node['language'] == 'egy' and target_node['language'].startswith('cop'):
                    # Check if Demotic→Coptic edge already exists
                    edge_exists = any(
                        e['type'] == 'DESCENDS' and 
                        e['from'] == demotic_id and 
                        e['to'] == edge['to']
                        for e in network['edges']
                    )
                    
                    if not edge_exists:
                        # Reroute: change source from Egyptian to Demotic
                        edge['from'] = demotic_id
                        rerouted_count += 1
                    else:
                        # Edge already exists, mark this one for removal
                        edge['_remove'] = True
            
            # Remove any marked duplicate edges
            network['edges'] = [e for e in network['edges'] if not e.get('_remove', False)]
        
        return rerouted_count

def main():
    # Load the three parsed files
    print("Loading parsed Wiktionary data...")
    
    with open('egyptian_lemmas_parsed_mwp.json', 'r', encoding='utf-8') as f:
        egy_data = json.load(f)
    
    with open('demotic_lemmas_parsed_mwp.json', 'r', encoding='utf-8') as f:
        dem_data = json.load(f)
    
    with open('coptic_lemmas_parsed_mwp.json', 'r', encoding='utf-8') as f:
        cop_data = json.load(f)
    
    print(f"Loaded {len(egy_data)} Egyptian, {len(dem_data)} Demotic, {len(cop_data)} Coptic lemmas")
    
    # Build networks
    builder = LemmaNetworkBuilder()
    networks = builder.build_networks_from_parsed_data(egy_data, dem_data, cop_data)
    
    # Export
    builder.export_networks('lemma_networks.json')
    
    print("\n" + "="*80)
    print("Network building complete!")
    print("\nThe output file 'lemma_networks.json' contains:")
    print("- Each network represents a lemma's evolution across time/languages")
    print("- Nodes: word forms in different languages/periods/dialects")
    print("- Edges: EVOLVES (temporal), DESCENDS (cross-language), VARIANT (spelling)")
    print("\nThis can be used to train a model that translates between:")
    print("- Different periods of Egyptian (Old Kingdom → New Kingdom → Late Period)")
    print("- Egyptian → Demotic → Coptic")
    print("- Different Coptic dialects (Sahidic, Bohairic, etc.)")

if __name__ == '__main__':
    main()
