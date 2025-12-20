#!/bin/bash
# Script to install CPU-only PyTorch

# Install uv if not already installed
pip install uv

# Install distutils for Python 3.10
pip install setuptools

# Install CPU-only PyTorch first
pip install torch==2.9.1+cpu torchvision==0.14.1+cpu -f https://download.pytorch.org/whl/cpu/torch_stable.html

# Then install the rest of the dependencies using uv
uv sync --frozen