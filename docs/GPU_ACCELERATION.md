# GPU Acceleration Guide

ForexSmartBot now supports GPU acceleration for machine learning models, NumPy operations, and backtesting. This guide explains how to set up and use GPU acceleration.

## Requirements

### CUDA Toolkit
GPU acceleration requires NVIDIA CUDA toolkit:
- **CUDA 11.x**: For older GPUs (GTX 10 series, RTX 20 series)
- **CUDA 12.x**: For newer GPUs (RTX 30/40 series, A series)

Download from: https://developer.nvidia.com/cuda-downloads

### Python Packages

Install GPU-accelerated packages based on your CUDA version:

```bash
# For CUDA 12.x
pip install cupy-cuda12x

# For CUDA 11.x
pip install cupy-cuda11x
```

**Note**: PyTorch and TensorFlow GPU support is included in their standard packages if CUDA is installed.

## GPU Detection

The system automatically detects available GPUs:

```python
from forexsmartbot.utils.gpu_utils import get_gpu_manager, GPUManager

# Get GPU information
gpu_manager = get_gpu_manager()
info = GPUManager.get_gpu_info()
print(info)
```

## Using GPU Acceleration

### 1. ML Models with CUDA

#### Transformer Strategy (PyTorch)
```python
from forexsmartbot.strategies import TransformerStrategy

# GPU is enabled by default
strategy = TransformerStrategy(use_gpu=True)
```

#### LSTM Strategy (TensorFlow)
```python
from forexsmartbot.strategies import LSTMStrategy

# GPU is enabled by default
strategy = LSTMStrategy(use_gpu=True)
```

### 2. GPU-Accelerated NumPy Operations

```python
from forexsmartbot.utils.gpu_numpy import gpu_array, gpu_rolling_mean

# Create GPU array
data = np.array([1, 2, 3, 4, 5])
gpu_data = gpu_array(data, use_gpu=True)

# GPU-accelerated rolling mean
rolling = gpu_rolling_mean(data, window=3, use_gpu=True)
result = rolling.to_numpy()  # Convert back to NumPy
```

### 3. GPU-Accelerated Backtesting

```python
from forexsmartbot.services.gpu_backtest import GPUBacktestService
from forexsmartbot.adapters.data import MultiProvider

# Initialize GPU backtest service
data_provider = MultiProvider()
gpu_backtest = GPUBacktestService(data_provider, use_gpu=True)

# Run backtest
results = gpu_backtest.run_backtest(
    strategy=strategy,
    symbol="EURUSD",
    start_date="2023-01-01",
    end_date="2023-12-31",
    initial_balance=10000.0
)
```

### 4. Parallel Backtesting

Run multiple strategies in parallel:

```python
strategies = [strategy1, strategy2, strategy3]
results = gpu_backtest.run_parallel_backtests(
    strategies=strategies,
    symbol="EURUSD",
    start_date="2023-01-01",
    end_date="2023-12-31"
)
```

## Performance Benefits

### ML Model Training
- **LSTM**: 5-10x faster on GPU
- **Transformer**: 10-20x faster on GPU
- **Ensemble ML**: 3-5x faster on GPU

### NumPy Operations
- **Large arrays (>10K elements)**: 10-50x faster
- **Rolling calculations**: 5-20x faster
- **Matrix operations**: 20-100x faster

### Backtesting
- **Single strategy**: 2-5x faster
- **Multiple strategies**: 5-10x faster (parallel execution)
- **Large datasets**: 10-50x faster

## GPU Memory Management

The system automatically manages GPU memory:

```python
# Enable/disable GPU globally
from forexsmartbot.utils.gpu_utils import set_gpu_enabled

set_gpu_enabled(True)  # Enable GPU
set_gpu_enabled(False)  # Disable GPU (use CPU)
```

## Troubleshooting

### GPU Not Detected
1. Verify CUDA is installed: `nvcc --version`
2. Check GPU is recognized: `nvidia-smi`
3. Verify PyTorch/TensorFlow GPU support:
   ```python
   import torch
   print(torch.cuda.is_available())  # Should be True
   
   import tensorflow as tf
   print(tf.config.list_physical_devices('GPU'))  # Should list GPUs
   ```

### Out of Memory Errors
- Reduce batch size in ML models
- Process data in smaller chunks
- Disable GPU for less critical operations

### Performance Issues
- Ensure data is large enough to benefit from GPU (typically >1000 elements)
- Use GPU for computationally intensive operations only
- CPU may be faster for small datasets due to overhead

## Best Practices

1. **Use GPU for**:
   - ML model training and inference
   - Large-scale backtesting
   - Complex indicator calculations
   - Parallel strategy evaluation

2. **Use CPU for**:
   - Small datasets (<1000 elements)
   - Simple operations
   - Real-time trading (low latency needed)

3. **Hybrid Approach**:
   - Use GPU for backtesting and optimization
   - Use CPU for live trading (lower latency)

## Example: Complete GPU Workflow

```python
from forexsmartbot.utils.gpu_utils import get_gpu_manager
from forexsmartbot.strategies import LSTMStrategy
from forexsmartbot.services.gpu_backtest import GPUBacktestService
from forexsmartbot.adapters.data import MultiProvider

# Check GPU availability
gpu_manager = get_gpu_manager()
if gpu_manager.is_gpu_available():
    print("GPU acceleration enabled!")
    
    # Create GPU-accelerated strategy
    strategy = LSTMStrategy(use_gpu=True)
    
    # Run GPU backtest
    data_provider = MultiProvider()
    backtest = GPUBacktestService(data_provider, use_gpu=True)
    
    results = backtest.run_backtest(
        strategy=strategy,
        symbol="EURUSD",
        start_date="2023-01-01",
        end_date="2023-12-31"
    )
    
    print(f"Backtest completed with GPU acceleration!")
    print(f"Total return: {results['total_return']:.2%}")
else:
    print("GPU not available, using CPU")
```

## Additional Resources

- [CuPy Documentation](https://docs.cupy.dev/)
- [PyTorch CUDA Guide](https://pytorch.org/docs/stable/notes/cuda.html)
- [TensorFlow GPU Guide](https://www.tensorflow.org/guide/gpu)
- [NVIDIA CUDA Toolkit](https://developer.nvidia.com/cuda-toolkit)

