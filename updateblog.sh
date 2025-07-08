#!/bin/bash
set -euo pipefail

# Change to the script's directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Set variables for Obsidian to Hugo copy
sourceEn="/Users/dirac042/Documents/dirac042/POSTS/en/"
sourceKo="/Users/dirac042/Documents/dirac042/POSTS/ko/"
destEn="/Users/dirac042/Desktop/dirac042/content/en/posts/"
destKo="/Users/dirac042/Desktop/dirac042/content/ko/posts/"

# Set GitHub Repo
myrepo="dirac042"

# Check for required commands
for cmd in git rsync python3 hugo; do
  if ! command -v $cmd &>/dev/null; then
    echo "$cmd is not installed or not in PATH."
    exit 1
  fi
done

# Step 1: Check if Git is initialized, and initialize if necessary
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

# Step 2: Sync posts from Obsidian to Hugo content folder using rsync
echo "Syncing posts from Obsidian..."
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

# Step 3: Process Markdown files with Python script to handle image links
echo "Processing image links in Markdown files..."
if [ ! -f "images.py" ]; then
  echo "Python script images.py not found."
  exit 1
fi

if ! python3 images.py; then
  echo "Failed to process image links."
  exit 1
fi

# Step 4: Build the Hugo site
echo "Building the Hugo site..."
if ! hugo; then
  echo "Hugo build failed."
  exit 1
fi

# Step 5: Add changes to Git

echo "Starting Git Commit and Branch process..."
# ask Commit message
read -rp "Commit message: " commit_msg

# generate temporary branch name
timestamp=$(date +'%Y%m%d-%H%M%S')
branch_name="test-${timestamp}"

# create and switch to new branch
git checkout -b "$branch_name"

# Add and Commit

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

read -rp "Merge '$branch_name' into 'master' and push? (y/N): " confirm_merge
if [[ "$confirm_merge" =~ ^[Yy]$ ]]; then
  git checkout master
  git merge "$branch_name"
  git push origin master
  echo "✅ Merged and pushed to master."
else
  echo "❗️ Merge skipped. You're still on branch '$branch_name'."
fi
