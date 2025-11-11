"""Example: Using the strategy builder."""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from forexsmartbot.builder import StrategyBuilder, StrategyTemplate, CodeGenerator
from forexsmartbot.builder.strategy_builder import ComponentType


def main():
    """Example: Build a custom strategy."""
    print("Strategy Builder Example")
    print("=" * 50)
    
    # Example 1: Create strategy from template
    print("\n1. Using Pre-built Template")
    print("-" * 50)
    
    template = StrategyTemplate.get_template("SMA Crossover")
    structure = template.get_strategy_structure()
    print(f"Template structure: {len(structure['components'])} components")
    
    # Example 2: Build custom strategy
    print("\n2. Building Custom Strategy")
    print("-" * 50)
    
    builder = StrategyBuilder()
    
    # Add indicators
    sma_fast_id = builder.add_component(
        ComponentType.INDICATOR,
        "SMA Fast",
        {"period": 20}
    )
    
    sma_slow_id = builder.add_component(
        ComponentType.INDICATOR,
        "SMA Slow",
        {"period": 50}
    )
    
    rsi_id = builder.add_component(
        ComponentType.INDICATOR,
        "RSI",
        {"period": 14}
    )
    
    # Add filter
    filter_id = builder.add_component(
        ComponentType.FILTER,
        "RSI Filter",
        {"oversold": 30, "overbought": 70}
    )
    
    # Add signal
    signal_id = builder.add_component(
        ComponentType.SIGNAL,
        "Crossover Signal",
        {"type": "crossover"}
    )
    
    # Connect components
    builder.connect_components(sma_fast_id, signal_id)
    builder.connect_components(sma_slow_id, signal_id)
    builder.connect_components(rsi_id, filter_id)
    builder.connect_components(filter_id, signal_id)
    
    # Validate strategy
    is_valid, errors = builder.validate_strategy()
    print(f"Strategy valid: {is_valid}")
    if errors:
        print(f"Errors: {errors}")
    
    # Generate code
    print("\n3. Generating Python Code")
    print("-" * 50)
    
    code_generator = CodeGenerator(builder)
    code = code_generator.generate_code()
    print("Generated code (first 20 lines):")
    print("\n".join(code.split("\n")[:20]))
    print("...")
    
    print("\nStrategy building complete!")


if __name__ == "__main__":
    main()

