#!/bin/bash

# Define repository paths
OLD_REPO_PATH="/path/to/OLD"
NEW_REPO_PATH="/path/to/NEW"
NEW2_REPO_PATH="/path/to/NEW2"

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

# Cherry-pick commits from NEW repository after the specific date
while read -r COMMIT_HASH; do
    git cherry-pick "$COMMIT_HASH" || {
        echo "Conflict detected. Resolve the conflict, then continue."
        exit 1
    }
done < commit_list.txt

# Merge temp branch into main branch of NEW2
git checkout main
git merge "$TEMP_BRANCH"

# Push the NEW2 repository
git remote add origin /path/to/NEW2
git push -u origin --all
git push origin --tags

# Clean up
rm commit_list.txt
git branch -D "$TEMP_BRANCH"

echo "NEW2 repository created and updated successfully."
