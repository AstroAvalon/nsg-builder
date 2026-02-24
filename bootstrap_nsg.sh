#!/bin/bash

# Configuration
# TODO: Update this URL to your actual Azure DevOps repository URL
REPO_URL="https://dev.azure.com/myorg/myproject/_git/nsg-tools"
FILES_TO_SYNC=("nsg_merger.py" "validator.py" "azure_helper.py" "base_rules.xlsx" "requirements.txt")
TEMP_DIR=".nsg_tools_temp"

# Function to update .gitignore
update_gitignore() {
    echo "Updating .gitignore..."
    if [ ! -f .gitignore ]; then
        touch .gitignore
    fi

    for file in "${FILES_TO_SYNC[@]}"; do
        if ! grep -q "^$file$" .gitignore; then
            echo "$file" >> .gitignore
            echo "Added $file to .gitignore"
        fi
    done
}

# Function to download tools
download_tools() {
    echo "Downloading NSG tools from $REPO_URL..."

    # Clean up any existing temp directory
    rm -rf "$TEMP_DIR"

    # Clone the repository
    # Using --depth 1 for shallow clone to save bandwidth/time
    git clone --depth 1 "$REPO_URL" "$TEMP_DIR"

    if [ $? -ne 0 ]; then
        echo "Error: Failed to clone repository."
        exit 1
    fi

    # Copy files to root
    for file in "${FILES_TO_SYNC[@]}"; do
        if [ -f "$TEMP_DIR/$file" ]; then
            cp "$TEMP_DIR/$file" .
            echo "Copied $file"
        else
            echo "Warning: $file not found in repository."
        fi
    done

    # Cleanup temp directory
    rm -rf "$TEMP_DIR"

    # Update gitignore
    update_gitignore

    echo "NSG tools downloaded successfully."
}

# Function to clean up tools
cleanup_tools() {
    echo "Cleaning up NSG tools..."
    for file in "${FILES_TO_SYNC[@]}"; do
        if [ -f "$file" ]; then
            rm "$file"
            echo "Removed $file"
        fi
    done
    echo "Cleanup complete."
}

# Main execution
if [ "$1" == "--clean" ]; then
    cleanup_tools
else
    download_tools
fi
