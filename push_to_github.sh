#!/bin/bash
# Script to push Safety Telemetry Platform to GitHub

set -e

echo "=========================================="
echo "Push to GitHub - Safety Telemetry Platform"
echo "=========================================="
echo ""

# Check if remote already exists
if git remote -v | grep -q origin; then
    echo "✅ Remote 'origin' already configured"
    git remote -v
    echo ""
    read -p "Push to existing remote? (y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        git push -u origin master
        echo "✅ Pushed to GitHub!"
        exit 0
    fi
fi

# Get GitHub repo URL
echo "To push to GitHub, you need to:"
echo ""
echo "1. Create a new repository on GitHub:"
echo "   - Go to https://github.com/new"
echo "   - Name it: 'safety-telemetry-platform' (or your preferred name)"
echo "   - Choose Public or Private"
echo "   - DO NOT initialize with README, .gitignore, or license"
echo ""
echo "2. Copy the repository URL (HTTPS or SSH)"
echo ""
read -p "Enter your GitHub repository URL (e.g., https://github.com/username/repo.git): " REPO_URL

if [ -z "$REPO_URL" ]; then
    echo "❌ No URL provided. Exiting."
    exit 1
fi

# Add remote
echo ""
echo "Adding remote 'origin'..."
git remote add origin "$REPO_URL"

# Rename branch to main (GitHub standard)
echo "Renaming branch to 'main'..."
git branch -M main

# Push
echo "Pushing to GitHub..."
git push -u origin main

echo ""
echo "✅ Successfully pushed to GitHub!"
echo "   Repository: $REPO_URL"
echo ""
echo "Next steps:"
echo "  - View your repo: $REPO_URL"
echo "  - Add a description in GitHub repo settings"
echo "  - Consider adding topics: safety-analytics, pymc, airflow, bigquery"
