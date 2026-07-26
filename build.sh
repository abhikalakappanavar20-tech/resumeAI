#!/bin/bash
set -e

echo "Building ResumeIQ for Vercel..."

# Install lean Python dependencies
pip install --no-compile --no-cache-dir -r requirements-vercel.txt

echo "Build complete."
