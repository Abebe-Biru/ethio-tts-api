#!/bin/bash
# Script to install CPU-only PyTorch

# Ensure we're using Python 3.10
export PYTHON_VERSION=3.10

# Upgrade pip first
python -m pip install --upgrade pip

# Install setuptools and wheel explicitly
python -m pip install setuptools wheel

# Install CPU-only PyTorch first
python -m pip install torch==2.9.1+cpu torchvision==0.14.1+cpu -f https://download.pytorch.org/whl/cpu/torch_stable.html

# Then install the rest of the dependencies using uv
uv sync --frozen