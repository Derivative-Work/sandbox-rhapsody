# Source before running faster-whisper on the GPU: ctranslate2 needs the pip-installed CUDA 12 cuBLAS and cuDNN.
SP=$(git rev-parse --show-toplevel)/.venv/lib/python3.12/site-packages/nvidia
export LD_LIBRARY_PATH="$SP/cublas/lib:$SP/cudnn/lib${LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}"
