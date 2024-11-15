#!/bin/bash

# Define variables for repository paths
OLD_REPO_PATH="/path/to/OLD"
NEW_REPO_PATH="/path/to/NEW"
CSV_OUTPUT_FILE="missing_files_report.csv"

# Define branches to restore files for
BRANCHES_TO_UPDATE=("release/*")

# Create or clear the CSV output file
echo "filepath,branch,filesize" > "$CSV_OUTPUT_FILE"

# Change to the OLD repository
cd "$OLD_REPO_PATH"

# Fetch all branches and tags from OLD repository
git fetch --all --tags

# Iterate through each branch in NEW repository
for BRANCH in "${BRANCHES_TO_UPDATE[@]}"
do
    # Switch to the corresponding branch in OLD
    git checkout "$BRANCH"

    # Create a temporary directory to store files to restore
    TEMP_DIR=$(mktemp -d)

    # Find missing files by comparing OLD and NEW repositories
    # Copy only the missing files from OLD repository to the temporary directory
    cd "$NEW_REPO_PATH"
    git checkout "$BRANCH"
    cd "$OLD_REPO_PATH"

    for FILE in $(find . -type f); do
        if [ ! -f "$NEW_REPO_PATH/$FILE" ]; then
            FILE_SIZE=$(stat -c%s "$FILE")
            echo "${FILE},${BRANCH},${FILE_SIZE}" >> "$CSV_OUTPUT_FILE"
            mkdir -p "$TEMP_DIR/$(dirname "$FILE")"
            cp "$FILE" "$TEMP_DIR/$FILE"
        fi
    done

    # Change to the NEW repository
    cd "$NEW_REPO_PATH"

    # Switch to the target branch in NEW repository
    git checkout "$BRANCH"

    # Copy files from the temporary directory to NEW repository
    cp -r "$TEMP_DIR"/* .

    # Stage and commit the changes
    git add .
    git commit -m "Restored missing files from OLD repository for branch $BRANCH"

    # Push the changes to the NEW repository
    git push origin "$BRANCH"

    # Clean up the temporary directory
    rm -rf "$TEMP_DIR"

    # Change back to the OLD repository
    cd "$OLD_REPO_PATH"

done

# Restore tags manually from OLD repository to NEW repository
cd "$OLD_REPO_PATH"

# Iterate over each tag in OLD repository
for TAG in $(git tag); do
    # Get the commit hash for the tag in the OLD repository
    TAG_COMMIT=$(git rev-list -n 1 "$TAG")

    # Change to the NEW repository
    cd "$NEW_REPO_PATH"

    # Find the best matching commit in the NEW repository for the tag
    # This could involve matching commit dates, messages, or using other heuristics
    # For simplicity, we'll try to use commit messages here
    COMMIT_MESSAGE=$(git log -n 1 --format=%s "$TAG_COMMIT")

    NEW_COMMIT=$(git log --all --grep="$COMMIT_MESSAGE" --format="%H" -n 1)

    if [ -n "$NEW_COMMIT" ]; then
        # Create the tag in the NEW repository at the best matching commit
        git tag -a "$TAG" -m "Recreated tag $TAG from OLD repository" "$NEW_COMMIT"
    else
        echo "Warning: No matching commit found for tag $TAG"
    fi

    # Change back to the OLD repository
    cd "$OLD_REPO_PATH"
done

# Push tags to NEW repository
cd "$NEW_REPO_PATH"
git push origin --tags

# Script complete
echo "Missing files have been restored and pushed for specified branches, and tags have been recreated and pushed."
