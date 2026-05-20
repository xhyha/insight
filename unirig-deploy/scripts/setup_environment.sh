#!/bin/bash
# UniRig Environment Setup Script
# Phase 4.1: GPU Environment Setup (M1.1)
# Target: Ubuntu 22.04 + CUDA 11.8 + Python 3.11

set -e

echo "========================================"
echo "UniRig Environment Setup"
echo "Phase 4.1: M1.1 GPU Environment Setup"
echo "========================================"

# Check if running as root
if [ "$EUID" -eq 0 ]; then
    echo "Warning: Running as root is not recommended"
fi

# Step 1: System Update
echo "[1/8] Updating system packages..."
sudo apt update && sudo apt upgrade -y

# Step 2: Install CUDA 11.8
echo "[2/8] Installing CUDA 11.8..."
# Download CUDA 11.8 installer
wget https://developer.download.nvidia.com/compute/cuda/11.8.0/local_installers/cuda_11.8.0_520.61.05_linux.run
chmod +x cuda_11.8.0_520.61.05_linux.run
sudo ./cuda_11.8.0_520.61.05_linux.run --silent --toolkit --override
rm cuda_11.8.0_520.61.05_linux.run

# Add CUDA to PATH
echo 'export PATH=/usr/local/cuda-11.8/bin:$PATH' >> ~/.bashrc
echo 'export LD_LIBRARY_PATH=/usr/local/cuda-11.8/lib64:$LD_LIBRARY_PATH' >> ~/.bashrc

# Step 3: Install Miniconda
echo "[3/8] Installing Miniconda..."
wget https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh
chmod +x Miniconda3-latest-Linux-x86_64.sh
bash Miniconda3-latest-Linux-x86_64.sh -b -p /opt/miniconda
rm Miniconda3-latest-Linux-x86_64.sh
export PATH=/opt/miniconda/bin:$PATH

# Step 4: Create Python 3.11 Environment
echo "[4/8] Creating Python 3.11 environment..."
conda create -n unirig python=3.11 -y
conda activate unirig

# Step 5: Install PyTorch with CUDA 11.8
echo "[5/8] Installing PyTorch with CUDA 11.8..."
pip install torch torchvision --index-url https://download.pytorch.org/whl/cu118

# Step 6: Install Core Dependencies
echo "[6/8] Installing core dependencies..."
pip install numpy pandas open3d trimesh scikit-learn

# Step 7: Install UniRig Special Dependencies
echo "[7/8] Installing UniRig special dependencies..."
# These may require manual compilation
pip install spconv torch-scatter torch-cluster -f https://data.pyg.org/whl/torch-2.0.0+cu118.html

# Try to install flash_attn, may fail if no CUDA compiler
pip install flash-attn || echo "Warning: flash-attn installation may require CUDA 12+"

# Step 8: Verify Installation
echo "[8/8] Verifying installation..."
python -c "import torch; print(f'PyTorch version: {torch.__version__}'); print(f'CUDA available: {torch.cuda.is_available()}'); print(f'CUDA version: {torch.version.cuda}')"
python -c "import numpy; import pandas; import trimesh; print('Core dependencies OK')"

echo ""
echo "========================================"
echo "Environment setup completed!"
echo "========================================"
echo ""
echo "To activate the environment:"
echo "  conda activate unirig"
echo ""
echo "Next step: M1.2 - Deploy UniRig pre-trained model"