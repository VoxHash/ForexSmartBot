"""Utility modules for ForexSmartBot."""

from .gpu_utils import (
    GPUManager,
    get_gpu_manager,
    set_gpu_enabled,
    is_gpu_enabled,
    GPUManager as GPUManager,
    CUPY_AVAILABLE,
    CUDA_AVAILABLE,
    TORCH_AVAILABLE,
    TF_GPU_AVAILABLE
)

from .gpu_numpy import (
    GPUArray,
    gpu_array,
    gpu_zeros,
    gpu_ones,
    gpu_arange,
    gpu_rolling_mean,
    gpu_rolling_std
)

__all__ = [
    'GPUManager',
    'get_gpu_manager',
    'set_gpu_enabled',
    'is_gpu_enabled',
    'CUPY_AVAILABLE',
    'CUDA_AVAILABLE',
    'TORCH_AVAILABLE',
    'TF_GPU_AVAILABLE',
    'GPUArray',
    'gpu_array',
    'gpu_zeros',
    'gpu_ones',
    'gpu_arange',
    'gpu_rolling_mean',
    'gpu_rolling_std',
]

