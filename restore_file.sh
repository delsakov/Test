#!/bin/bash

OLD_REPO_PATH="/path/to/OLD/repository"
NEW_REPO_PATH="/path/to/NEW/repository"

# Function to list release branches
list_release_branches() {
    git -C "$NEW_REPO_PATH" branch -r --list 'origin/release/*' | sed 's/^[[:space:]]*origin\///'
}

# Function to list missing files for a branch
list_missing_files() {
    local branch="$1"
    comm -23 <(git -C "$OLD_REPO_PATH" ls-tree -r --name-only "$branch" | sort) \
              <(git -C "$NEW_REPO_PATH" ls-tree -r --name-only "$branch" | sort)
}

# Function to copy missing files
copy_missing_files() {
    local branch="$1"
    local file="$2"
    local old_file_path=$(git -C "$OLD_REPO_PATH" ls-tree -r --full-name "$branch" -- "$file" | awk '{print $4}')
    if [ -n "$old_file_path" ]; then
        mkdir -p "$(dirname "$NEW_REPO_PATH/$file")"
        cp "$OLD_REPO_PATH/$old_file_path" "$NEW_REPO_PATH/$file"
        git -C "$NEW_REPO_PATH" add "$file"
    fi
}

# Main script
for branch in $(list_release_branches); do
    echo "Processing branch: $branch"
    git -C "$NEW_REPO_PATH" checkout "$branch"
    
    missing_files=$(list_missing_files "$branch")
    if [ -n "$missing_files" ]; then
        echo "Restoring missing files for $branch"
        while IFS= read -r file; do
            copy_missing_files "$branch" "$file"
        done <<< "$missing_files"
        
        git -C "$NEW_REPO_PATH" commit -m "Restored missing files from $branch"
    else
        echo "No missing files for $branch"
    fi
done

# Verify restored files
for branch in $(list_release_branches); do
    echo "Verifying branch: $branch"
    git -C "$NEW_REPO_PATH" checkout "$branch"
    
    missing_files=$(list_missing_files "$branch")
    if [ -n "$missing_files" ]; then
        while IFS= read -r file; do
            if git -C "$NEW_REPO_PATH" ls-files --error-unmatch "$file" &>/dev/null; then
                echo "  $file: Restored"
            else
                echo "  $file: Failed to restore"
            fi
        done <<< "$missing_files"
    else
        echo "  All files present"
    fi
done

echo "Process completed. Please review the changes and push if satisfied."
echo "To push all branches, run: git -C \"$NEW_REPO_PATH\" push --all"
