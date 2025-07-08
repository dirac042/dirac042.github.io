#!/bin/bash
set -euo pipefail

# Change to script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Set paths
sourceEn="/Users/dirac042/Documents/dirac042/POSTS/en"
sourceKo="/Users/dirac042/Documents/dirac042/POSTS/ko"
destEn="/Users/dirac042/Desktop/dirac042/content/en/posts/"
destKo="/Users/dirac042/Desktop/dirac042/content/ko/posts/"

# GitHub repo
myrepo="https://github.com/dirac042/dirac042.github.io.git"

# Check for required commands
for cmd in git rsync python3 hugo; do
  if ! command -v $cmd &>/dev/null; then
    echo "$cmd is not installed or not in PATH."
    exit 1
  fi
done

# Initialize Git if needed
if [ ! -d ".git" ]; then
  echo "Initializing Git repository..."
  git init
  git remote add origin $myrepo
else
  echo "Git repository already initialized."
  if ! git remote | grep -q 'origin'; then
    echo "Adding remote origin..."
    git remote add origin $myrepo
  fi
fi

# Sync Obsidian to Hugo
echo "Syncing posts..."
for pair in "$sourceEn:$destEn" "$sourceKo:$destKo"; do
  src="${pair%%:*}"
  dst="${pair##*:}"
  if [ ! -d "$src" ]; then
    echo "Source path does not exist: $src"
    exit 1
  fi
  if [ ! -d "$dst" ]; then
    echo "Destination path does not exist: $dst"
    exit 1
  fi
  rsync -av --delete "$src" "$dst"
done

# Process image links
echo "Processing image links in Markdown files..."
if [ ! -f "images.py" ]; then
  echo "Python script images.py not found."
  exit 1
fi

python3 images.py || {
  echo "Image processing failed."
  exit 1
}

# Build Hugo site
echo "Building Hugo site..."
hugo || {
  echo "Hugo build failed."
  exit 1
}

# Git workflow with experimental branch
echo "Starting Git commit and branch process..."

# Ask for commit message
read -rp "Commit message: " commit_msg

# Generate temp branch name
timestamp=$(date +'%Y%m%d-%H%M%S')
branch_name="test-${timestamp}"

# Create and switch to new branch
git checkout -b "$branch_name"

# Add & commit
git add .
if git diff --cached --quiet; then
  echo "No changes to commit."
else
  git commit -m "$commit_msg"
  echo "Committed to branch $branch_name."
fi

echo ""
echo "✅ You are now on branch '$branch_name'."
echo "👉 Inspect your site locally or test this branch before merging."

# Prompt to merge
read -rp "Merge '$branch_name' into 'master' and push? (y/N): " confirm_merge
if [[ "$confirm_merge" =~ ^[Yy]$ ]]; then
  git checkout master
  git merge "$branch_name"
  git push origin master
  echo "✅ Merged and pushed to master."
else
  echo "❗️Merge skipped. You're still on branch '$branch_name'."
fi
