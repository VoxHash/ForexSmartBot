"""Example: Real-time parameter adaptation."""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from forexsmartbot.strategies import get_strategy
from forexsmartbot.optimization import RealTimeParameterAdapter, AdaptiveParameter
from forexsmartbot.adapters.data import YFinanceProvider


def main():
    """Example: Real-time parameter adaptation."""
    print("=" * 70)
    print("Real-Time Parameter Adaptation Example")
    print("=" * 70)
    
    data_provider = YFinanceProvider()
    
    # Define base parameters
    base_params = {
        'fast_period': 20,
        'slow_period': 50
    }
    
    # Define adaptation configuration
    adaptation_config = {
        'fast_period': AdaptiveParameter(
            parameter_name='fast_period',
            base_value=20,
            regime_multipliers={
                'trending': 0.8,    # Faster in trending markets
                'ranging': 1.2,     # Slower in ranging markets
                'volatile': 0.9,    # Slightly faster in volatile markets
                'calm': 1.1         # Slightly slower in calm markets
            },
            min_value=10,
            max_value=30,
            adaptation_rate=0.1  # 10% adaptation per update
        ),
        'slow_period': AdaptiveParameter(
            parameter_name='slow_period',
            base_value=50,
            regime_multipliers={
                'trending': 0.9,
                'ranging': 1.1,
                'volatile': 1.0,
                'calm': 1.0
            },
            min_value=40,
            max_value=80,
            adaptation_rate=0.1
        )
    }
    
    # Strategy factory
    def strategy_factory(params):
        return get_strategy('SMA_Crossover', **params)
    
    # Create adapter
    adapter = RealTimeParameterAdapter(
        strategy_factory=strategy_factory,
        base_params=base_params,
        adaptation_config=adaptation_config,
        lookback_period=50
    )
    
    print("\nSimulating real-time parameter adaptation...")
    print()
    
    # Get data
    df = data_provider.get_data('EURUSD=X', '2023-01-01', '2023-12-31', '1h')
    
    if df.empty:
        print("No data available")
        return
    
    # Simulate real-time updates
    update_points = [100, 200, 300, 400, 500]
    
    for i, point in enumerate(update_points, 1):
        if point >= len(df):
            break
        
        print(f"Update {i}: Processing data point {point}")
        
        # Update strategy
        current_data = df.iloc[:point]
        strategy = adapter.update(current_data)
        
        # Get current parameters
        current_params = adapter.param_manager.get_current_parameters()
        regime = adapter.param_manager.current_regime
        
        print(f"  Current Regime: {regime.regime_type if regime else 'Unknown'}")
        print(f"  Volatility: {regime.volatility:.4f}" if regime else "  Volatility: N/A")
        print(f"  Trend Strength: {regime.trend_strength:.4f}" if regime else "  Trend Strength: N/A")
        print(f"  Adapted Parameters:")
        print(f"    fast_period: {current_params.get('fast_period', 0):.1f}")
        print(f"    slow_period: {current_params.get('slow_period', 0):.1f}")
        print()
    
    # Get adaptation statistics
    stats = adapter.get_adaptation_stats()
    
    print("Adaptation Statistics:")
    print("-" * 70)
    print(f"Total Updates: {stats.get('total_periods', 0)}")
    print(f"Regime Distribution:")
    for regime_type, percentage in stats.get('regime_distribution', {}).items():
        print(f"  {regime_type}: {percentage:.1%}")
    print(f"Average Volatility: {stats.get('avg_volatility', 0):.4f}")
    print(f"Average Trend Strength: {stats.get('avg_trend_strength', 0):.4f}")
    
    print("\n" + "=" * 70)
    print("Real-time parameter adaptation example complete!")
    print("=" * 70)


if __name__ == "__main__":
    main()

