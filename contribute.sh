#!/bin/bash

set -e

# Usage:
# ./contribute.sh <contribution_number> "<contributor_name>" <30_download_urls> <30_upload_urls> <contribution_upload_url>

if [ $# -ne 63 ]; then
    echo "Error: Incorrect number of arguments. Expected 63 arguments."
    echo "Usage: $0 <contribution_number> <contributor_name> <30_download_urls> <30_upload_urls> <contribution_upload_url>"
    exit 1
fi

CONTRIBUTION_NUMBER=$1
CONTRIBUTOR_NAME=$2
shift 2

# Create directories
INPUT_DIR="./input"
OUTPUT_DIR="./output"
mkdir -p "$INPUT_DIR" "$OUTPUT_DIR"

PH2_FILES=(
    "inclusion_26_1"
    "inclusion_26_2"
    "inclusion_26_3"
    "inclusion_26_4"
    "inclusion_26_8"
    "non-inclusion_26_1"
    "non-inclusion_26_2"
    "non-inclusion_26_3"
    "non-inclusion_26_4"
    "non-inclusion_26_8"
    "combined_26_1_1"
    "combined_26_1_2"
    "combined_26_1_4"
    "combined_26_1_8"
    "combined_26_2_1"
    "combined_26_2_2"
    "combined_26_2_4"
    "combined_26_2_8"
    "combined_26_3_1"
    "combined_26_3_2"
    "combined_26_3_4"
    "combined_26_3_8"
    "combined_26_4_1"
    "combined_26_4_2"
    "combined_26_4_4"
    "combined_26_4_8"
    "combined_26_8_1"
    "combined_26_8_2"
    "combined_26_8_4"
    "combined_26_8_8"
)

echo "Downloading files..."
for i in {1..30}; do
    url="$1"
    shift
    
    # Extract filename from URL
    filename=$(echo "$url" | sed -E 's/.*\/([^/?]+)\?.*/\1/')
    
    echo "Downloading $filename from $url"
    if ! curl -f -S -o "$INPUT_DIR/$filename" "$url"; then
        echo "Error downloading $filename. Exiting."
        exit 1
    fi
    echo "Successfully downloaded $filename"
done

# Function to install git
install_git() {
    OS_TYPE=$(uname -s | tr '[:upper:]' '[:lower:]')
    
    if [ "$OS_TYPE" = "darwin" ]; then
        if ! command -v brew &> /dev/null; then
            echo "Homebrew not found. Installing Homebrew..."
            /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
        fi
        echo "Installing git using Homebrew..."
        brew install git
    elif [ "$OS_TYPE" = "linux" ]; then
        if [ -f /etc/debian_version ]; then
            echo "Installing git using apt..."
            sudo apt update
            sudo apt install -y git
        elif [ -f /etc/redhat-release ]; then
            echo "Installing git using yum..."
            sudo yum install -y git
        else
            echo "Unsupported Linux distribution. Please install git manually."
            exit 1
        fi
    else
        echo "Unsupported OS: $OS_TYPE"
        exit 1
    fi
}

# Function to install go
install_go() {
    OS_TYPE=$(uname -s | tr '[:upper:]' '[:lower:]')
    
    if [ "$OS_TYPE" = "darwin" ]; then
        if ! command -v brew &> /dev/null; then
            echo "Homebrew not found. Installing Homebrew..."
            /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
        fi
        echo "Installing go using Homebrew..."
        brew install go
    elif [ "$OS_TYPE" = "linux" ]; then
        if [ -f /etc/debian_version ]; then
            echo "Installing go using apt..."
            sudo apt update
            sudo apt install -y golang
        elif [ -f /etc/redhat-release ]; then
            echo "Installing go using yum..."
            sudo yum install -y golang
        else
            echo "Unsupported Linux distribution. Please install go manually."
            exit 1
        fi
    else
        echo "Unsupported OS: $OS_TYPE"
        exit 1
    fi
}

# Check if git is installed
if ! command -v git &> /dev/null; then
    echo "git not found. Installing git..."
    install_git
fi

# Check if go is installed
if ! command -v go &> /dev/null; then
    echo "go not found. Installing go..."
    install_go
fi

# Clone and build semaphore-mtb-setup
TEMP_DIR=$(mktemp -d)
git clone https://github.com/worldcoin/semaphore-mtb-setup "$TEMP_DIR/semaphore-mtb-setup"
cd "$TEMP_DIR/semaphore-mtb-setup" && go build -v
cp semaphore-mtb-setup "$OLDPWD"
cd "$OLDPWD"
rm -rf "$TEMP_DIR"

CONTRIB_FILE="$OUTPUT_DIR/${CONTRIBUTOR_NAME}_CONTRIBUTION_${CONTRIBUTION_NUMBER}.txt"

# Create or overwrite the contribution file
> "$CONTRIB_FILE" || { echo "Failed to create/clear $CONTRIB_FILE. Check permissions."; exit 1; }

echo "Contribution file prepared: $CONTRIB_FILE"

# Execute the binary to ensure it's working
if ! ./semaphore-mtb-setup; then
    echo "Error: Failed to run semaphore-mtb-setup. Exiting."
    exit 1
fi

for ph2_file in "$INPUT_DIR"/*.ph2; do
    base_name=$(basename "$ph2_file")
    file_base=$(basename "$ph2_file" .ph2)
    for ph2_file_name in "${PH2_FILES[@]}"; do
        if [[ $file_base == ${ph2_file_name}* ]]; then
            output_file="$OUTPUT_DIR/${ph2_file_name}_${CONTRIBUTOR_NAME}_contribution_${CONTRIBUTION_NUMBER}.ph2"
            break
        fi
    done
    
    echo "Contributing to $ph2_file"
    if ! contribution_hash=$(./semaphore-mtb-setup p2c "$ph2_file" "$output_file"); then
        echo "Error: Failed to process $ph2_file. Exiting."
        exit 1
    fi
    
    echo "$base_name $contribution_hash" >> "$CONTRIB_FILE"
    echo "Contribution hash for $base_name: $contribution_hash"
done

echo "All contributions completed. Hashes stored in $CONTRIB_FILE"

echo "Uploading new .ph2 files..."
for ph2_file_name in "${PH2_FILES[@]}"; do
    output_file="$OUTPUT_DIR/${ph2_file_name}_${CONTRIBUTOR_NAME}_contribution_${CONTRIBUTION_NUMBER}.ph2"
    if [ -f "$output_file" ]; then
        url="$1"
        shift
        expected_filename="${ph2_file_name}_${CONTRIBUTOR_NAME}_contribution_${CONTRIBUTION_NUMBER}.ph2"
        if [[ "$url" == *"$expected_filename"* ]]; then
            echo "Uploading $(basename "$output_file")..."
            echo "URL: $url"
            if ! curl -f -S -X PUT -T "$output_file" "$url"; then
                echo "Error uploading $(basename "$output_file"). Exiting."
                exit 1
            fi
        else
            echo "Error: URL doesn't match expected filename for $ph2_file_name. Skipping."
        fi
    else
        echo "Warning: Expected file $output_file not found. Skipping."
        shift
    fi
done

echo "Uploading contribution file..."
contrib_url="$1"
echo "Contribution URL: $contrib_url"
if ! curl -f -S -X PUT -T "$CONTRIB_FILE" "$contrib_url"; then
    echo "Error uploading contribution file. Exiting."
    exit 1
fi

echo "All files uploaded successfully."
echo "Input files are stored in $INPUT_DIR"
echo "Output files and contribution file are stored in $OUTPUT_DIR"