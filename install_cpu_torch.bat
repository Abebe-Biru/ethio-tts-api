@echo off
REM Script to install CPU-only PyTorch on Windows

REM Check Python version and distutils availability
echo Checking Python environment...
python -c "import sys; print('Python version:', sys.version)"
python -c "import distutils; print('distutils is available')" || echo distutils is NOT available

REM Upgrade pip first
echo Upgrading pip...
python -m pip install --upgrade pip

REM Install setuptools and wheel explicitly
echo Installing setuptools and wheel...
python -m pip install setuptools wheel

REM Check again if distutils is available after installing setuptools
python -c "import distutils; print('distutils is now available')" || echo distutils is still NOT available

REM Install CPU-only PyTorch first
echo Installing CPU-only PyTorch...
python -m pip install torch==2.9.1+cpu torchvision==0.14.1+cpu -f https://download.pytorch.org/whl/cpu/torch_stable.html

REM Then install the rest of the dependencies using uv
echo Installing remaining dependencies with uv...
uv sync --frozen