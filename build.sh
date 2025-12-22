#!/usr/bin/env bash
# Render build script for TTS API

set -o errexit  # Exit on error

echo "=== Starting Render Build ==="

# Upgrade pip
echo "Upgrading pip..."
pip install --upgrade pip

# Install setuptools (provides distutils for Python 3.10)
echo "Installing setuptools..."
pip install setuptools>=65.0.0 wheel

# Install CPU-only PyTorch to save space (Render free tier has limited disk)
echo "Installing CPU-only PyTorch..."
pip install torch==2.5.1+cpu --index-url https://download.pytorch.org/whl/cpu

# Install transformers without dependencies to prevent PyTorch reinstall
echo "Installing transformers (no deps)..."
pip install --no-deps transformers>=4.57.0

# Install all other dependencies from pyproject.toml
echo "Installing application dependencies..."
pip install boltons>=25.0.0 \
    deepdiff>=8.6.1 \
    diskcache>=5.6.3 \
    fastapi>=0.119.0 \
    glom>=24.11.0 \
    httpx>=0.27.0 \
    prometheus-client>=0.19.0 \
    pyinstrument>=5.1.1 \
    pydantic-settings>=2.0.0 \
    pyrsistent>=0.20.0 \
    sentencepiece>=0.2.1 \
    soundfile>=0.13.1 \
    structlog>=25.4.0 \
    tenacity>=9.1.2 \
    tqdm>=4.66.0 \
    uroman>=0.3.0 \
    uvicorn[standard]>=0.37.0

# Install transformers dependencies
echo "Installing transformers dependencies..."
pip install huggingface-hub>=0.19.0 \
    tokenizers>=0.19.0 \
    safetensors>=0.4.0 \
    pyyaml>=5.1 \
    regex>=2022.1.18 \
    requests>=2.26.0 \
    filelock>=3.0 \
    numpy>=1.17

echo "=== Build Complete ==="
