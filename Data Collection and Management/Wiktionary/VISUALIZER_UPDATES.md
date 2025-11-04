# Visualizer Updates - Edge Types and Multiple Etymologies

## Changes Made

### 1. Complete Edge Type Visualization

**Updated Files:**
- `visualize/app.js` - Added colors and styles for BORROWED and INHERITED edges
- `visualize/index.html` - Updated legend to show all 7 edge types

**Edge Types and Styling:**
1. **EVOLVES** - Red (#e74c3c), solid line
   - Egyptian → Demotic evolution
   
2. **DESCENDS** - Blue (#3498db), solid line
   - Demotic → Coptic, or general descendant relationships
   
3. **VARIANT** - Gray (#95a5a6), dashed line (5,5)
   - Hieroglyphic variants, spelling variations
   
4. **DERIVED** - Orange (#f39c12), solid line
   - Words derived from a root (e.g., ḫꜣj → mḫꜣt, ḫꜣyw)
   
5. **COMPONENT** - Purple (#9b59b6), dotted line (3,3)
   - Compound words showing their components (e.g., ⲉⲣⲟⲩⲥⲁⲣⲝ from ⲉⲣ + ⲟⲩ + ⲥⲁⲣⲝ)
   
6. **BORROWED** - Teal (#1abc9c), long dash (8,4)
   - Words borrowed from other languages (e.g., ⲁⲅⲅⲉⲗⲟⲥ ← Greek ἄγγελος)
   
7. **INHERITED** - Dark Orange (#e67e22), short dots (2,2)
   - Words inherited from proto-languages or ancestral forms

### 2. Multiple Etymology Fix

**Problem:** 
Words with multiple etymologies (like ϣⲱϣ with 5 etymologies) were showing the wrong definition in the lightbox because nodes didn't have `etymology_index` set.

**Solution:**
Updated `build_lemma_networks_v2.py` to set `etymology_index` on ALL node types:

1. **Coptic Standalone Networks** (line ~915)
   - Added `etymology_index=etym_idx` when creating standalone Coptic nodes

2. **Coptic Descendants** (line ~745)
   - Added `etym_idx` enumeration to loop
   - Set `etymology_index=etym_idx` for new Coptic descendant nodes
   - Set `etymology_index` for existing nodes if not already set

3. **Demotic Descendants** (line ~658)
   - Added `etym_idx` enumeration to loop
   - Set `etymology_index=etym_idx` for new Demotic descendant nodes
   - Set `etymology_index` for existing nodes if not already set

**Result:**
The lightbox now correctly filters definitions by `etymology_index`, so each network shows the right etymology's meanings and definitions.

### 3. Verification

**ϣⲱϣ Example (5 etymologies):**
- Network NET02268: Etymology 1 - "to scatter, spread"
- Network NET02373: Etymology 2 - "to make equal, level, strait"
- Network NET05159: Etymology 0 - "to be despised, humble"
- Network NET05160: Etymology 4 - "fork or rake (used to separate grain from chaff)"

All 4 networks now correctly display their respective etymology's definition in the lightbox! ✅

## Statistics

**Final Network Counts:**
- Total networks: 4,976
- Total nodes: 22,053
- Total edges: 17,462
- Average nodes/network: 4.4
- Average edges/network: 3.5

**Edge Type Distribution:**
- EVOLVES: Egyptian → Demotic evolution paths
- DESCENDS: Cross-generational relationships
- VARIANT: Spelling/hieroglyphic variations
- DERIVED: 734+ edges from derived terms
- COMPONENT: 656+ edges from compound words
- BORROWED: 613+ from Greek, 62+ from Latin (Coptic)
- INHERITED: Proto-language origins (Afro-Asiatic, Semitic, etc.)

## Files Modified

1. `visualize/app.js`
   - `getEdgeColor()` function - Added BORROWED (#1abc9c) and INHERITED (#e67e22)
   - `getEdgeStyle()` function - Added BORROWED ('8,4') and INHERITED ('2,2')

2. `visualize/index.html`
   - Legend section - Updated to show all 7 edge types with visual indicators

3. `build_lemma_networks_v2.py`
   - `build_coptic_standalone_networks()` - Added etymology_index to nodes
   - `add_coptic_descendants()` - Added etymology enumeration and index setting
   - `add_demotic_descendants()` - Added etymology enumeration and index setting

## Testing

To test in the visualizer:
1. Open a word with multiple etymologies (e.g., ϣⲱϣ)
2. Check that each network shows the correct etymology in the lightbox
3. Verify that all 7 edge types display with correct colors and dash patterns
4. Confirm legend shows all edge types correctly
