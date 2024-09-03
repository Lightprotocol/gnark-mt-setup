#!/bin/bash

# Create virtual environment
python3 -m venv venv

# Activate virtual environment
source venv/bin/activate

# Install boto3
pip install boto3

# Activate virtual environment
source venv/bin/activate

# Print success message
echo "Virtual environment created and boto3 installed. Activate it with 'source venv/bin/activate'"