#!/bin/bash

# Build script for AWS Lambda deployment package

set -e

echo "Building Lambda deployment package..."

# Create build directory
rm -rf build/
mkdir -p build/

# Install dependencies
pip install -r requirements.txt -t build/

# Copy Lambda function
cp lambda_function.py build/

# Create deployment package
cd build/
zip -r ../function.zip .
cd ..

echo "Lambda deployment package created: function.zip"
echo "Upload this file to AWS Lambda or use it with the AWS CLI"