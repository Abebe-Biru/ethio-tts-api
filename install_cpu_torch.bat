@echo off
REM Script to install CPU-only PyTorch on Windows

REM Upgrade pip first
python3.10 -m pip install --upgrade pip

REM Install setuptools and wheel explicitly
python3.10 -m pip install setuptools wheel

REM Install CPU-only PyTorch first
python3.10 -m pip install torch==2.9.1+cpu torchvision==0.14.1+cpu -f https://download.pytorch.org/whl/cpu/torch_stable.html

REM Then install the rest of the dependencies using uv
uv sync --frozen