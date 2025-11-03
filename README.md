# Egyptian Lemma Network Visualizer

An interactive web application for visualizing the evolution of Egyptian words across 4,000 years of history (Egyptian → Demotic → Coptic).

This branch contains the visualization website optimized for deployment on Jekyll-based platforms like GitHub Pages.

## Features

✨ **Interactive Network Graphs**
- Force-directed graph visualization using D3.js
- Zoom and pan to explore large networks
- Drag nodes to rearrange the layout

🔍 **Powerful Search**
- Search by word form or meaning
- Live suggestions as you type
- Random network exploration

📊 **Rich Metadata Display**
- Color-coded by language (Egyptian, Demotic, Coptic)
- Different edge types: EVOLVES (temporal), DESCENDS (cross-language), VARIANT (spelling)
- Hover over nodes to see full information (meanings, period, dialect, hieroglyphs)

🎨 **Beautiful UI**
- Modern, responsive design
- Statistics dashboard
- Legend and color coding

## Deployment

### GitHub Pages

This branch is optimized for GitHub Pages deployment:

1. Go to your repository settings
2. Navigate to "Pages" section
3. Select this branch (`jekyll-visualization`) as the source
4. The visualization will be available at `https://[username].github.io/[repository-name]/`

### Local Testing

You can test the visualization locally using Python's built-in HTTP server:

```bash
# Clone this branch
git clone -b jekyll-visualization https://github.com/JonahMorgan/Aegyptus.git
cd Aegyptus

# Start a simple HTTP server
python -m http.server 8000
```

Then open http://localhost:8000 in your browser.

## How to Use

1. **Search for a lemma**: Type a word form or meaning in the search box
   - Example: `baboon`, `ⲁⲓⲁⲓ`, `ꜣw`
   
2. **Browse suggestions**: Click on a suggestion to visualize that network

3. **Explore random networks**: Click "Random Network" to see a random lemma

4. **Interact with the graph**:
   - **Zoom**: Scroll to zoom in/out
   - **Pan**: Click and drag empty space to move the view
   - **Move nodes**: Click and drag nodes to rearrange
   - **Hover**: Hover over nodes to see detailed information

## Network Structure

### Node Colors
- 🔴 **Red**: Egyptian (Old Kingdom → Greco-Roman Period, ~2686 BCE - 395 CE)
- 🔵 **Teal**: Demotic (~650 BCE - 452 CE)
- 🟢 **Light Green**: Coptic (~200 CE - 1300 CE, still used liturgically)
- ⚪ **Gray**: Other languages (borrowed words, foreign origins)

### Edge Types
- **━ EVOLVES** (Red): Same language, different time period
- **━ DESCENDS** (Blue): Cross-language inheritance (Egyptian → Demotic → Coptic)
- **┄ VARIANT** (Gray dashed): Same time/language, different spelling or dialect

### Special Markers
- **Gold border**: Root node (earliest or most representative form)
- **Larger circle**: Root node
- **Labels**: Show period (Egyptian) or dialect (Coptic)

## Data Source

The visualizer loads data from JSON files in the same directory:
- `lemma_networks.json` - **4,945 networks** representing distinct lemmas with **14,725+ nodes** and **8,930+ edges**
- `egyptian_lemmas_parsed_mwp.json` - Detailed Egyptian lemma data
- `demotic_lemmas_parsed_mwp.json` - Detailed Demotic lemma data
- `coptic_lemmas_parsed_mwp.json` - Detailed Coptic lemma data

## Example Networks to Explore

Try searching for:
- `baboon` - See the evolution from Egyptian jꜥn through multiple periods
- `ⲁⲓⲁⲓ` - Coptic word with missing Demotic ancestor (placeholder node)
- `ꜣw` - Egyptian word with descendants in Demotic and Coptic
- `water`, `house`, `god` - Common concepts across all periods

## Technical Details

### Technologies
- **D3.js v7**: Force-directed graph visualization
- **Vanilla JavaScript**: No frameworks, pure JS
- **HTML5/CSS3**: Modern, responsive UI

### Performance
- Handles networks with 100+ nodes smoothly
- Force simulation automatically stabilizes
- Efficient search across 14,725 nodes

### Browser Compatibility
- Chrome/Edge (recommended)
- Firefox
- Safari
- Any modern browser with ES6 support

## File Structure

```
/ (root)
├── index.html                        # Main HTML page
├── app.js                            # Visualization logic and D3 code
├── lemma_networks.json               # Network data
├── egyptian_lemmas_parsed_mwp.json   # Egyptian lemma details
├── demotic_lemmas_parsed_mwp.json    # Demotic lemma details
├── coptic_lemmas_parsed_mwp.json     # Coptic lemma details
├── hiero_images/                     # Hieroglyphic image files
│   └── hiero_*.png                   # Individual hieroglyph images
└── README.md                         # This file
```

## Troubleshooting

**Problem**: Network data doesn't load
- **Solution**: Make sure all JSON files are in the same directory as index.html
- Check browser console (F12) for errors

**Problem**: Search not working
- **Solution**: Wait for data to finish loading (see stats panel)

**Problem**: Graph is too crowded
- **Solution**: Use zoom to focus on specific areas
- Drag nodes apart to spread them out

**Problem**: Hieroglyphs not displaying
- **Solution**: Ensure the `hiero_images/` directory is present with all PNG files

## Credits

Created for the Aegyptus Transformer project to visualize Egyptian language evolution data from Wiktionary.

Data pipeline:
1. Wiktionary scraping → JSON
2. mwparserfromhell parsing → Structured data
3. Network building → Graph representation
4. D3.js visualization → Interactive exploration
