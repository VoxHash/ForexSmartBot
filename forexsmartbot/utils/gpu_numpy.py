"""GPU-accelerated NumPy operations using CuPy."""

import numpy as np
from typing import Union, Optional
import warnings

from .gpu_utils import CUPY_AVAILABLE, get_gpu_manager, is_gpu_enabled

if CUPY_AVAILABLE:
    import cupy as cp


class GPUArray:
    """Wrapper for GPU-accelerated array operations."""
    
    def __init__(self, data, use_gpu: Optional[bool] = None):
        """
        Initialize GPU array.
        
        Args:
            data: NumPy array or CuPy array
            use_gpu: Whether to use GPU (None = auto-detect)
        """
        self._use_gpu = use_gpu if use_gpu is not None else is_gpu_enabled()
        self._gpu_manager = get_gpu_manager()
        
        if self._use_gpu and CUPY_AVAILABLE:
            if isinstance(data, np.ndarray):
                self._array = cp.asarray(data)
            elif isinstance(data, cp.ndarray):
                self._array = data
            else:
                self._array = cp.asarray(np.array(data))
        else:
            if isinstance(data, cp.ndarray):
                self._array = cp.asnumpy(data)
            else:
                self._array = np.asarray(data)
    
    @property
    def array(self):
        """Get the underlying array (CuPy or NumPy)."""
        return self._array
    
    def to_numpy(self) -> np.ndarray:
        """Convert to NumPy array (CPU)."""
        if CUPY_AVAILABLE and isinstance(self._array, cp.ndarray):
            return cp.asnumpy(self._array)
        return np.asarray(self._array)
    
    def to_cupy(self):
        """Convert to CuPy array (GPU)."""
        if not CUPY_AVAILABLE:
            raise RuntimeError("CuPy not available")
        if isinstance(self._array, cp.ndarray):
            return self._array
        return cp.asarray(self._array)
    
    def __getitem__(self, key):
        """Array indexing."""
        return GPUArray(self._array[key], use_gpu=self._use_gpu)
    
    def __setitem__(self, key, value):
        """Array assignment."""
        if isinstance(value, GPUArray):
            self._array[key] = value.array
        else:
            self._array[key] = value
    
    def __len__(self):
        """Array length."""
        return len(self._array)
    
    def __array__(self):
        """NumPy array interface."""
        return self.to_numpy()
    
    @property
    def shape(self):
        """Array shape."""
        return self._array.shape
    
    @property
    def dtype(self):
        """Array dtype."""
        return self._array.dtype
    
    def copy(self):
        """Create a copy."""
        return GPUArray(self._array.copy(), use_gpu=self._use_gpu)
    
    def reshape(self, *args, **kwargs):
        """Reshape array."""
        return GPUArray(self._array.reshape(*args, **kwargs), use_gpu=self._use_gpu)
    
    def mean(self, axis=None, **kwargs):
        """Calculate mean."""
        result = self._array.mean(axis=axis, **kwargs)
        if isinstance(result, (cp.ndarray, cp.generic)):
            return GPUArray(result, use_gpu=self._use_gpu)
        return result
    
    def std(self, axis=None, **kwargs):
        """Calculate standard deviation."""
        result = self._array.std(axis=axis, **kwargs)
        if isinstance(result, (cp.ndarray, cp.generic)):
            return GPUArray(result, use_gpu=self._use_gpu)
        return result
    
    def sum(self, axis=None, **kwargs):
        """Calculate sum."""
        result = self._array.sum(axis=axis, **kwargs)
        if isinstance(result, (cp.ndarray, cp.generic)):
            return GPUArray(result, use_gpu=self._use_gpu)
        return result
    
    def max(self, axis=None, **kwargs):
        """Calculate maximum."""
        result = self._array.max(axis=axis, **kwargs)
        if isinstance(result, (cp.ndarray, cp.generic)):
            return GPUArray(result, use_gpu=self._use_gpu)
        return result
    
    def min(self, axis=None, **kwargs):
        """Calculate minimum."""
        result = self._array.min(axis=axis, **kwargs)
        if isinstance(result, (cp.ndarray, cp.generic)):
            return GPUArray(result, use_gpu=self._use_gpu)
        return result


def gpu_array(data, use_gpu: Optional[bool] = None) -> GPUArray:
    """Create a GPU-accelerated array."""
    return GPUArray(data, use_gpu=use_gpu)


def gpu_zeros(shape, dtype=np.float32, use_gpu: Optional[bool] = None):
    """Create GPU-accelerated zeros array."""
    use_gpu = use_gpu if use_gpu is not None else is_gpu_enabled()
    if use_gpu and CUPY_AVAILABLE:
        return GPUArray(cp.zeros(shape, dtype=dtype), use_gpu=True)
    return GPUArray(np.zeros(shape, dtype=dtype), use_gpu=False)


def gpu_ones(shape, dtype=np.float32, use_gpu: Optional[bool] = None):
    """Create GPU-accelerated ones array."""
    use_gpu = use_gpu if use_gpu is not None else is_gpu_enabled()
    if use_gpu and CUPY_AVAILABLE:
        return GPUArray(cp.ones(shape, dtype=dtype), use_gpu=True)
    return GPUArray(np.ones(shape, dtype=dtype), use_gpu=False)


def gpu_arange(start, stop=None, step=1, dtype=None, use_gpu: Optional[bool] = None):
    """Create GPU-accelerated arange array."""
    use_gpu = use_gpu if use_gpu is not None else is_gpu_enabled()
    if use_gpu and CUPY_AVAILABLE:
        return GPUArray(cp.arange(start, stop, step, dtype=dtype), use_gpu=True)
    return GPUArray(np.arange(start, stop, step, dtype=dtype), use_gpu=False)


def gpu_rolling_mean(data, window, use_gpu: Optional[bool] = None):
    """GPU-accelerated rolling mean."""
    use_gpu = use_gpu if use_gpu is not None else is_gpu_enabled()
    gpu_data = gpu_array(data, use_gpu=use_gpu)
    
    if use_gpu and CUPY_AVAILABLE and isinstance(gpu_data.array, cp.ndarray):
        # CuPy doesn't have rolling, so we'll use convolution
        kernel = cp.ones(window) / window
        result = cp.convolve(gpu_data.array, kernel, mode='same')
        return GPUArray(result, use_gpu=True)
    else:
        # Fallback to NumPy
        return GPUArray(np.convolve(gpu_data.to_numpy(), np.ones(window)/window, mode='same'), use_gpu=False)


def gpu_rolling_std(data, window, use_gpu: Optional[bool] = None):
    """GPU-accelerated rolling standard deviation."""
    use_gpu = use_gpu if use_gpu is not None else is_gpu_enabled()
    gpu_data = gpu_array(data, use_gpu=use_gpu)
    
    if use_gpu and CUPY_AVAILABLE and isinstance(gpu_data.array, cp.ndarray):
        # Use convolution for rolling std
        mean = gpu_rolling_mean(data, window, use_gpu=True)
        squared_diff = (gpu_data.array - mean.array) ** 2
        kernel = cp.ones(window) / window
        variance = cp.convolve(squared_diff, kernel, mode='same')
        std = cp.sqrt(variance)
        return GPUArray(std, use_gpu=True)
    else:
        # Fallback to NumPy
        arr = gpu_data.to_numpy()
        return GPUArray(np.array([np.std(arr[i:i+window]) if i+window <= len(arr) else np.nan 
                                  for i in range(len(arr))]), use_gpu=False)

