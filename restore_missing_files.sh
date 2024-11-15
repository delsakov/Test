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

# Fetch all branches from OLD repository
git fetch --all

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

# Script complete
echo "Missing files have been restored and pushed for specified branches."
