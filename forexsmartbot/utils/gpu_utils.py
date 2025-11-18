"""GPU utilities for CUDA support and device management."""

import os
from typing import Optional, Dict, Any
import warnings
import sys

# Initialize flags
CUPY_AVAILABLE = False
CUDA_AVAILABLE = False
TORCH_AVAILABLE = False
TF_AVAILABLE = False
TF_GPU_AVAILABLE = False
CUDA_DEVICE_COUNT = 0
TF_GPU_COUNT = 0

# Initialize module-level variables
cp = None
torch = None
tf = None

# Try to import CUDA libraries with defensive error handling
try:
    import cupy as cp
    CUPY_AVAILABLE = True
except Exception as e:
    CUPY_AVAILABLE = False
    cp = None
    # Silently fail - GPU is optional

# Try to import PyTorch with very defensive error handling
# Note: On Windows, PyTorch may fail to load DLLs (e.g., c10.dll) due to missing
# Visual C++ Redistributables or CUDA issues. We catch all exceptions to allow
# the app to run without GPU support.
try:
    import importlib
    torch = importlib.import_module('torch')
    TORCH_AVAILABLE = True
    try:
        if torch.cuda.is_available():
            CUDA_AVAILABLE = True
            CUDA_DEVICE_COUNT = torch.cuda.device_count()
        else:
            CUDA_AVAILABLE = False
            CUDA_DEVICE_COUNT = 0
    except (OSError, RuntimeError, Exception):
        # CUDA check failed (DLL loading issues, etc.)
        CUDA_AVAILABLE = False
        CUDA_DEVICE_COUNT = 0
except (ImportError, OSError, RuntimeError, AttributeError, Exception) as e:
    # PyTorch import failed (DLL errors, missing dependencies, etc.)
    # This includes WinError 1114 (DLL initialization failed)
    TORCH_AVAILABLE = False
    CUDA_AVAILABLE = False
    CUDA_DEVICE_COUNT = 0
    torch = None
    # Silently fail - GPU is optional

# Try to import TensorFlow with defensive error handling
try:
    import tensorflow as tf
    TF_AVAILABLE = True
    try:
        gpus = tf.config.list_physical_devices('GPU')
        if gpus:
            TF_GPU_AVAILABLE = True
            TF_GPU_COUNT = len(gpus)
        else:
            TF_GPU_AVAILABLE = False
            TF_GPU_COUNT = 0
    except (OSError, RuntimeError, Exception):
        # TensorFlow GPU check failed
        TF_GPU_AVAILABLE = False
        TF_GPU_COUNT = 0
except (ImportError, OSError, RuntimeError, AttributeError, Exception):
    # TensorFlow import failed (DLL errors, missing dependencies, etc.)
    TF_AVAILABLE = False
    TF_GPU_AVAILABLE = False
    TF_GPU_COUNT = 0
    tf = None
    # Silently fail - GPU is optional


class GPUManager:
    """Manager for GPU resources and operations."""
    
    def __init__(self, use_gpu: bool = True, device_id: int = 0):
        """
        Initialize GPU manager.
        
        Args:
            use_gpu: Whether to use GPU if available
            device_id: GPU device ID to use (0 for first GPU)
        """
        self.use_gpu = use_gpu and self.is_gpu_available()
        self.device_id = device_id
        self.device = None
        
        if self.use_gpu:
            self._initialize_device()
    
    def _initialize_device(self):
        """Initialize GPU device."""
        try:
            if TORCH_AVAILABLE and CUDA_AVAILABLE and torch is not None:
                if self.device_id < CUDA_DEVICE_COUNT:
                    self.device = torch.device(f'cuda:{self.device_id}')
                else:
                    import warnings
                    warnings.warn(f"GPU {self.device_id} not available, using CPU")
                    self.device = torch.device('cpu') if torch is not None else None
                    self.use_gpu = False
            elif CUPY_AVAILABLE and cp is not None:
                try:
                    # Test CuPy
                    _ = cp.array([1, 2, 3])
                    self.device = f'cuda:{self.device_id}'
                except Exception as e:
                    import warnings
                    warnings.warn(f"CuPy initialization failed: {e}, using CPU")
                    self.device = None
                    self.use_gpu = False
            else:
                self.use_gpu = False
        except Exception as e:
            import warnings
            warnings.warn(f"GPU device initialization failed: {e}, using CPU")
            self.use_gpu = False
            self.device = None
    
    @staticmethod
    def is_gpu_available() -> bool:
        """Check if GPU is available."""
        return CUDA_AVAILABLE or CUPY_AVAILABLE or TF_GPU_AVAILABLE
    
    @staticmethod
    def get_gpu_info() -> Dict[str, Any]:
        """Get information about available GPUs."""
        info = {
            'cuda_available': CUDA_AVAILABLE,
            'cupy_available': CUPY_AVAILABLE,
            'tensorflow_gpu_available': TF_GPU_AVAILABLE,
            'gpu_count': max(CUDA_DEVICE_COUNT, TF_GPU_COUNT, (1 if CUPY_AVAILABLE else 0))
        }
        
        if TORCH_AVAILABLE and CUDA_AVAILABLE:
            info['pytorch_gpus'] = []
            for i in range(CUDA_DEVICE_COUNT):
                info['pytorch_gpus'].append({
                    'id': i,
                    'name': torch.cuda.get_device_name(i),
                    'memory_total': torch.cuda.get_device_properties(i).total_memory / 1e9,  # GB
                    'memory_allocated': torch.cuda.memory_allocated(i) / 1e9,  # GB
                })
        
        if TF_AVAILABLE and TF_GPU_AVAILABLE and tf is not None:
            try:
                info['tensorflow_gpus'] = []
                for i, gpu in enumerate(tf.config.list_physical_devices('GPU')):
                    info['tensorflow_gpus'].append({
                        'id': i,
                        'name': gpu.name,
                    })
            except Exception:
                info['tensorflow_gpus'] = []
        
        if CUPY_AVAILABLE and cp is not None:
            try:
                info['cupy_device'] = cp.cuda.Device().id
                info['cupy_memory'] = cp.cuda.Device().mem_info
            except Exception:
                pass
        
        return info
    
    def get_device(self):
        """Get the current device (PyTorch)."""
        if self.use_gpu and TORCH_AVAILABLE and self.device and torch is not None:
            try:
                return self.device
            except Exception:
                pass
        if TORCH_AVAILABLE and torch is not None:
            try:
                return torch.device('cpu')
            except Exception:
                pass
        return None
    
    def to_device(self, tensor, device=None):
        """Move tensor to device."""
        if not TORCH_AVAILABLE or torch is None:
            return tensor
        
        try:
            if device is None:
                device = self.get_device()
            
            if device and hasattr(tensor, 'to'):
                return tensor.to(device)
        except Exception:
            pass
        return tensor
    
    def numpy_to_cupy(self, array):
        """Convert NumPy array to CuPy array (GPU)."""
        if not self.use_gpu or not CUPY_AVAILABLE:
            return array
        
        try:
            return cp.asarray(array)
        except Exception as e:
            warnings.warn(f"Failed to convert to CuPy: {e}")
            return array
    
    def cupy_to_numpy(self, array):
        """Convert CuPy array to NumPy array (CPU)."""
        if CUPY_AVAILABLE and isinstance(array, cp.ndarray):
            return cp.asnumpy(array)
        return array
    
    def synchronize(self):
        """Synchronize GPU operations."""
        if self.use_gpu:
            try:
                if TORCH_AVAILABLE and CUDA_AVAILABLE and torch is not None:
                    torch.cuda.synchronize()
                elif CUPY_AVAILABLE and cp is not None:
                    cp.cuda.Stream.null.synchronize()
            except Exception:
                pass


# Global GPU manager instance
_gpu_manager: Optional[GPUManager] = None


def get_gpu_manager(use_gpu: bool = True, device_id: int = 0) -> GPUManager:
    """Get or create global GPU manager."""
    global _gpu_manager
    if _gpu_manager is None:
        _gpu_manager = GPUManager(use_gpu=use_gpu, device_id=device_id)
    return _gpu_manager


def set_gpu_enabled(enabled: bool):
    """Enable or disable GPU usage globally."""
    global _gpu_manager
    if _gpu_manager is None:
        _gpu_manager = GPUManager(use_gpu=enabled)
    else:
        _gpu_manager.use_gpu = enabled and _gpu_manager.is_gpu_available()


def is_gpu_enabled() -> bool:
    """Check if GPU is enabled."""
    if _gpu_manager is None:
        return False
    return _gpu_manager.use_gpu

