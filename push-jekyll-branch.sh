#!/bin/bash
# Script to push the jekyll-visualization branch to GitHub

echo "======================================"
echo "Push Jekyll Visualization Branch"
echo "======================================"
echo ""

# Check if we're in a git repository
if [ ! -d ".git" ]; then
    echo "Error: This script must be run from the root of the git repository"
    exit 1
fi

# Check if the jekyll-visualization branch exists
if ! git rev-parse --verify jekyll-visualization >/dev/null 2>&1; then
    echo "Error: The jekyll-visualization branch does not exist"
    echo "Please ensure the branch was created correctly"
    exit 1
fi

echo "Checking out jekyll-visualization branch..."
git checkout jekyll-visualization

if [ $? -ne 0 ]; then
    echo "Error: Failed to checkout jekyll-visualization branch"
    exit 1
fi

echo ""
echo "Branch checked out successfully!"
echo ""
echo "Files in this branch:"
git ls-files | head -20
echo "... and $(git ls-files | wc -l) files total"
echo ""

echo "Pushing to origin..."
git push -u origin jekyll-visualization

if [ $? -eq 0 ]; then
    echo ""
    echo "======================================"
    echo "SUCCESS!"
    echo "======================================"
    echo ""
    echo "The jekyll-visualization branch has been pushed to GitHub."
    echo ""
    echo "Next steps:"
    echo "1. Go to https://github.com/JonahMorgan/Aegyptus/settings/pages"
    echo "2. Under 'Build and deployment':"
    echo "   - Source: Deploy from a branch"
    echo "   - Branch: jekyll-visualization"
    echo "   - Folder: / (root)"
    echo "3. Click 'Save'"
    echo ""
    echo "Your visualization will be available at:"
    echo "https://jonahmorgan.github.io/Aegyptus/"
    echo ""
else
    echo ""
    echo "======================================"
    echo "FAILED!"
    echo "======================================"
    echo ""
    echo "Failed to push the branch to GitHub."
    echo "You may need to push manually or check your Git credentials."
    exit 1
fi
