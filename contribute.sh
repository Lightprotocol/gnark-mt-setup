#!/bin/bash

set -e

# Usage:
# ./contribute.sh <contribution_number> "<contributor_name>" <15_download_urls> <15_upload_urls> <contribution_upload_url>

if [ $# -ne 33 ]; then
    echo "Error: Incorrect number of arguments. Expected 33 arguments."
    echo "Usage: $0 <contribution_number> <contributor_name> <15_download_urls> <15_upload_urls> <contribution_upload_url>"
    exit 1
fi

CONTRIBUTION_NUMBER=$1
CONTRIBUTOR_NAME=$2
shift 2

# Create directories
INPUT_DIR="./input"
OUTPUT_DIR="./output"
mkdir -p "$INPUT_DIR" "$OUTPUT_DIR"

echo "Downloading files..."
for i in {1..15}; do
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
    output_file="$OUTPUT_DIR/${base_name%.ph2}_${CONTRIBUTOR_NAME}_contribution_$CONTRIBUTION_NUMBER.ph2"
    
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
for ph2_file in "$OUTPUT_DIR"/*.ph2; do
    url="$1"
    shift
    echo "Uploading $(basename "$ph2_file")..."
    echo "URL: $url"
    if ! curl -f -S -X PUT -T "$ph2_file" "$url"; then
        echo "Error uploading $(basename "$ph2_file"). Exiting."
        exit 1
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