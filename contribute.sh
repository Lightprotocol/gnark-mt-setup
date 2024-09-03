#!/bin/bash

set -e

# Usage:
# ./contribute.sh <contribution_number> "<contributor_name>" "url1" "url2" ...

# 18
if [ $# -lt 1 ]; then
    echo "Error: Incorrect number of arguments. Usage: $0 <contribution_number> <contributor_name> <url1> <url2> ..."
    exit 1
fi

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
REPO_ROOT="$( cd "$SCRIPT_DIR/.." && pwd )"
cd "$REPO_ROOT"


CONTRIBUTION_NUMBER=$1
CONTRIBUTOR_NAME=$2
shift 2

PH2_FILES=(
    "inclusion_26_1.ph2"
    "inclusion_26_2.ph2"
    "inclusion_26_3.ph2"
    "inclusion_26_4.ph2"
    "inclusion_26_8.ph2"
    "non-inclusion_26_1.ph2"
    "non-inclusion_26_2.ph2"
    "combined_26_1_1.ph2"
    "combined_26_1_2.ph2"
    "combined_26_2_1.ph2"
    "combined_26_2_2.ph2"
    "combined_26_3_1.ph2"
    "combined_26_3_2.ph2"
    "combined_26_4_1.ph2"
    "combined_26_4_2.ph2"
)

INPUT_DIR="$REPO_ROOT/ceremony/contribute/ph2-files"
OUTPUT_DIR="$REPO_ROOT/ceremony/contribute/outputs"
mkdir -p "$INPUT_DIR" "$OUTPUT_DIR"

echo "Downloading files..."
for i in "${!PH2_FILES[@]}"; do
    file="${PH2_FILES[$i]}"
    url="$1"
    shift
    output_file="$INPUT_DIR/${file%.ph2}_${CONTRIBUTOR_NAME}_contribution_${CONTRIBUTION_NUMBER}.ph2"
    echo "Downloading $file from $url"
    curl -f -S -o "$output_file" "$url"
    echo "Successfully downloaded $file"
done

cd "$REPO_ROOT"
if [ ! -d "semaphore-mtb-setup" ]; then
    if ! command -v go &> /dev/null; then
        echo "Go not found, downloading and installing Go..."
        curl -LO https://golang.org/dl/go1.17.6.linux-amd64.tar.gz
        tar -C /usr/local -xzf go1.17.6.linux-amd64.tar.gz
        export PATH=$PATH:/usr/local/go/bin
        echo "Go installed successfully."
    fi
    git clone https://github.com/worldcoin/semaphore-mtb-setup
    cd semaphore-mtb-setup
    if ! command -v git &> /dev/null; then
        echo "Git not found, installing Git..."
        if [ "$3" == "mac-arm" ] || [ "$3" == "mac-x86" ]; then
            brew install git
        else
            echo "Git installation not supported for this OS."
            exit 1
        fi
        echo "Git installed successfully."
    fi

    if [ "$3" == "linux" ]; then
        curl -LO https://golang.org/dl/go1.23.0.linux-amd64.tar.gz
        tar -C /usr/local -xzf go1.23.0.linux-amd64.tar.gz
    elif [ "$3" == "mac-arm" ]; then
        curl -LO https://golang.org/dl/go1.23.0.darwin-arm64.pkg
        sudo installer -pkg go1.23.0.darwin-arm64.pkg -target /
    elif [ "$3" == "mac-x86" ]; then
        curl -LO https://golang.org/dl/go1.23.0.darwin-amd64.pkg
        sudo installer -pkg go1.23.0.darwin-amd64.pkg -target /
    else
        echo "Unsupported OS type."
        exit 1
    fi

    export PATH=$PATH:/usr/local/go/bin
    go build -v
else
    cd semaphore-mtb-setup
fi
cd "$REPO_ROOT"
CONTRIB_FILE="$OUTPUT_DIR/${CONTRIBUTOR_NAME}_CONTRIBUTION_${CONTRIBUTION_NUMBER}.txt"
> "$CONTRIB_FILE"

for ph2_file in "$INPUT_DIR"/*_${CONTRIBUTOR_NAME}_contribution_${CONTRIBUTION_NUMBER}.ph2; do
    base_name=$(basename "$ph2_file" "_${CONTRIBUTOR_NAME}_contribution_${CONTRIBUTION_NUMBER}.ph2")
    new_contribution=$((CONTRIBUTION_NUMBER + 1))
    output_file="${base_name}_${CONTRIBUTOR_NAME}_contribution_${new_contribution}.ph2"
    
    echo "Contributing to $ph2_file"
    contribution_hash=$(./semaphore-mtb-setup/semaphore-mtb-setup p2c "$ph2_file" "$OUTPUT_DIR/$output_file")
    
    echo "$base_name $contribution_hash" >> "$CONTRIB_FILE"
    echo "Contribution hash for $base_name: $contribution_hash"
done

echo "All contributions completed. Hashes stored in $CONTRIB_FILE"
echo "Uploading new .ph2 files..."
for file in "${PH2_FILES[@]}"; do
    url="$1"
    shift
    ph2_file="$OUTPUT_DIR/${file%.ph2}_${CONTRIBUTOR_NAME}_contribution_$((CONTRIBUTION_NUMBER + 1)).ph2"
    echo "Uploading $(basename "$ph2_file")..."
    echo "URL: $url"
    curl -v -f -S -X PUT -T "$ph2_file" "$url"
    if [ $? -ne 0 ]; then
        echo "Error uploading $(basename "$ph2_file"). Exiting."
        exit 1
    fi
done

echo "Uploading contribution file..."
contrib_url="$1"
echo "Contribution URL: $contrib_url"
curl -v -f -S -X PUT -T "$CONTRIB_FILE" "$contrib_url"
if [ $? -ne 0 ]; then
    echo "Error uploading contribution file. Exiting."
    exit 1
fi

echo "All files uploaded successfully."