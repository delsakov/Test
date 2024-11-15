#!/bin/bash

# Define variables for repository paths
OLD_REPO_PATH="/path/to/OLD"
NEW_REPO_PATH="/path/to/NEW"
NEW2_REPO_PATH="/path/to/NEW2"
PATCHES_DIR="/path/to/patches"
CSV_OUTPUT_FILE="missing_files_report.csv"

# Clone OLD repository to NEW2
git clone "$OLD_REPO_PATH" "$NEW2_REPO_PATH"
cd "$NEW2_REPO_PATH"

# Use git filter-repo to remove unwanted branches and features
# Keep only branches like release/* and main
git filter-repo --force --refs 'release/*' 'main'

# Add NEW repository as a remote and fetch changes
git remote add new-repo "$NEW_REPO_PATH"
git fetch new-repo

# Create a temporary branch from NEW starting from a specific date
TEMP_BRANCH="temp-branch"
git checkout -b "$TEMP_BRANCH" new-repo/main
# Replace YYYY-MM-DD with the actual date you want to start cherry-picking from
START_DATE="YYYY-MM-DD"
git log --since="$START_DATE" --pretty=format:"%H" > commit_list.txt

# Export patches from NEW after a specific date
mkdir -p "$PATCHES_DIR"
while read -r COMMIT_HASH; do
    git format-patch -1 "$COMMIT_HASH" -o "$PATCHES_DIR"
done < commit_list.txt

# Apply patches in NEW2
cd "$NEW2_REPO_PATH"
git checkout main
for PATCH in "$PATCHES_DIR"/*.patch; do
    git am "$PATCH" || {
        echo "Patch failed. Please resolve conflicts and continue."
        exit 1
    }
done

# Push the NEW2 repository
git remote add origin /path/to/NEW2
git push -u origin --all
git push origin --tags

# Clean up
rm commit_list.txt
echo "Missing files have been restored, patches applied, and NEW2 repository created and updated successfully."
