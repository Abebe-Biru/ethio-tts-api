@echo off
REM Script to install CPU-only PyTorch on Windows

REM Install uv if not already installed
pip install uv

REM Install CPU-only PyTorch first
pip install torch==2.9.1+cpu torchvision==0.14.1+cpu -f https://download.pytorch.org/whl/cpu/torch_stable.html

REM Then install the rest of the dependencies using uv
uv sync --frozen