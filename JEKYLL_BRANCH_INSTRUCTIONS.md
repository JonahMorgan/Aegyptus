# Jekyll Visualization Branch Created

## Overview

A new orphan branch called `jekyll-visualization` has been created that contains only the files necessary for the Egyptian Lemma Network Visualizer to run inside a Jekyll-based website (such as GitHub Pages).

## What Was Done

1. **Created an orphan branch**: The `jekyll-visualization` branch has no shared history with the main repository branches, making it completely independent.

2. **Moved visualization files to root**: All visualization files from `Data Collection and Management/Wiktionary/visualize/` have been moved to the root directory of the branch.

3. **Updated file paths**: Modified `app.js` to load data files from the current directory (changed `../` to `./` in all fetch calls).

4. **Included necessary data files**:
   - `index.html` - Main visualization page
   - `app.js` - Visualization JavaScript code
   - `lemma_networks.json` - Network data (12MB)
   - `egyptian_lemmas_parsed_mwp.json` - Egyptian lemma details (12MB)
   - `demotic_lemmas_parsed_mwp.json` - Demotic lemma details (291KB)
   - `coptic_lemmas_parsed_mwp.json` - Coptic lemma details (6MB)
   - `hiero_images/` - Directory with 753 hieroglyphic PNG images
   - `README.md` - Updated documentation for Jekyll deployment

5. **Branch is committed but NOT pushed**: The branch exists locally and needs to be pushed to the remote repository.

## Next Steps

### To Push the Branch to GitHub

The branch is committed locally but not yet pushed to GitHub. To push it, run:

```bash
git checkout jekyll-visualization
git push -u origin jekyll-visualization
```

### To Deploy on GitHub Pages

Once the branch is pushed:

1. Go to your repository on GitHub
2. Navigate to Settings → Pages
3. Under "Build and deployment":
   - Source: Select "Deploy from a branch"
   - Branch: Select `jekyll-visualization` and `/ (root)`
   - Click "Save"

4. GitHub Pages will automatically build and deploy the visualization
5. The visualization will be available at: `https://jonahmorgan.github.io/Aegyptus/`

### To Test Locally

You can test the visualization locally before pushing:

```bash
git checkout jekyll-visualization
python -m http.server 8000
```

Then open `http://localhost:8000` in your browser.

## Branch Structure

The `jekyll-visualization` branch contains only these files:

```
/ (root)
├── index.html                        # Main HTML page
├── app.js                            # Visualization logic
├── lemma_networks.json               # Network data
├── egyptian_lemmas_parsed_mwp.json   # Egyptian lemma details
├── demotic_lemmas_parsed_mwp.json    # Demotic lemma details
├── coptic_lemmas_parsed_mwp.json     # Coptic lemma details
├── hiero_images/                     # 753 hieroglyphic images
│   └── hiero_*.png
└── README.md                         # Documentation
```

Total: 760 files (7 data/docs + 753 images)

## What This Branch Does NOT Contain

The `jekyll-visualization` branch does NOT contain:
- The main Aegyptus Translator code
- Wiktionary scraping scripts
- Data processing scripts
- Any other files from the repository

This keeps the branch clean and focused solely on serving the visualization website.

## Maintenance

To update the visualization in the future:

1. Make changes in the main repository's `Data Collection and Management/Wiktionary/visualize/` directory
2. Cherry-pick or manually apply those changes to the `jekyll-visualization` branch
3. Remember to update file paths if they reference parent directories
4. Push the updates to GitHub to redeploy on GitHub Pages
