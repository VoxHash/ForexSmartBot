"""Code generation from visual strategy builder."""

from typing import Dict, Any
from .strategy_builder import StrategyBuilder, ComponentType


class CodeGenerator:
    """Generate Python code from strategy builder structure."""
    
    def __init__(self, builder: StrategyBuilder):
        self.builder = builder
        
    def generate_code(self) -> str:
        """Generate Python code for the strategy."""
        structure = self.builder.get_strategy_structure()
        
        code_lines = [
            '"""Auto-generated strategy from visual builder."""',
            '',
            'import pandas as pd',
            'import numpy as np',
            'from typing import Dict, Any, Optional',
            'from ..core.interfaces import IStrategy',
            '',
            '',
            'class GeneratedStrategy(IStrategy):',
            '    """Auto-generated trading strategy."""',
            '    ',
            '    def __init__(self, **params):',
        ]
        
        # Add parameter initialization
        all_params = {}
        for comp_data in structure['components'].values():
            all_params.update(comp_data.get('parameters', {}))
            
        for param_name, param_value in all_params.items():
            if isinstance(param_value, (int, float, str)):
                code_lines.append(f"        self._{param_name} = params.get('{param_name}', {param_value})")
                
        code_lines.extend([
            '        self._name = "Generated Strategy"',
            '    ',
            '    @property',
            '    def name(self) -> str:',
            '        return self._name',
            '    ',
            '    @property',
            '    def params(self) -> Dict[str, Any]:',
            '        return {',
        ])
        
        for param_name in all_params.keys():
            code_lines.append(f"            '{param_name}': self._{param_name},")
            
        code_lines.extend([
            '        }',
            '    ',
            '    def set_params(self, **kwargs) -> None:',
        ])
        
        for param_name in all_params.keys():
            code_lines.append(f"        if '{param_name}' in kwargs:")
            code_lines.append(f"            self._{param_name} = kwargs['{param_name}']")
            
        code_lines.extend([
            '    ',
            '    def indicators(self, df: pd.DataFrame) -> pd.DataFrame:',
            '        """Calculate indicators."""',
            '        out = df.copy()',
        ])
        
        # Generate indicator code based on components
        for comp_id, comp_data in structure['components'].items():
            if comp_data['type'] == 'indicator':
                comp_name = comp_data['name']
                if 'SMA' in comp_name:
                    period = comp_data['parameters'].get('period', 20)
                    code_lines.append(f"        out['SMA_{period}'] = out['Close'].rolling({period}).mean()")
                elif 'RSI' in comp_name:
                    period = comp_data['parameters'].get('period', 14)
                    code_lines.append("        # RSI calculation")
                    code_lines.append(f"        delta = out['Close'].diff()")
                    code_lines.append(f"        gain = (delta.where(delta > 0, 0)).rolling(window={period}).mean()")
                    code_lines.append(f"        loss = (-delta.where(delta < 0, 0)).rolling(window={period}).mean()")
                    code_lines.append(f"        rs = gain / loss")
                    code_lines.append(f"        out['RSI'] = 100 - (100 / (1 + rs))")
                elif 'ATR' in comp_name:
                    period = comp_data['parameters'].get('period', 14)
                    code_lines.append(f"        # ATR calculation")
                    code_lines.append(f"        high_low = out['High'] - out['Low']")
                    code_lines.append(f"        high_close = abs(out['High'] - out['Close'].shift())")
                    code_lines.append(f"        low_close = abs(out['Low'] - out['Close'].shift())")
                    code_lines.append(f"        tr = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)")
                    code_lines.append(f"        out['ATR'] = tr.rolling({period}).mean()")
        
        code_lines.extend([
            '        return out',
            '    ',
            '    def signal(self, df: pd.DataFrame) -> int:',
            '        """Generate trading signal."""',
            '        if len(df) < 50:',
            '            return 0',
            '        ',
            '        # Signal logic based on components',
        ])
        
        # Generate signal logic
        for comp_id, comp_data in structure['components'].items():
            if comp_data['type'] == 'signal':
                comp_name = comp_data['name']
                if 'Crossover' in comp_name:
                    code_lines.append("        # Crossover signal")
                    code_lines.append("        if 'SMA_20' in df.columns and 'SMA_50' in df.columns:")
                    code_lines.append("            if df['SMA_20'].iloc[-1] > df['SMA_50'].iloc[-1] and df['SMA_20'].iloc[-2] <= df['SMA_50'].iloc[-2]:")
                    code_lines.append("                return 1")
                    code_lines.append("            elif df['SMA_20'].iloc[-1] < df['SMA_50'].iloc[-1] and df['SMA_20'].iloc[-2] >= df['SMA_50'].iloc[-2]:")
                    code_lines.append("                return -1")
                elif 'RSI' in comp_name:
                    code_lines.append("        # RSI signal")
                    code_lines.append("        if 'RSI' in df.columns:")
                    code_lines.append("            rsi = df['RSI'].iloc[-1]")
                    code_lines.append("            if rsi < 30:")
                    code_lines.append("                return 1")
                    code_lines.append("            elif rsi > 70:")
                    code_lines.append("                return -1")
                elif 'Breakout' in comp_name:
                    code_lines.append("        # Breakout signal")
                    code_lines.append("        lookback = 20")
                    code_lines.append("        if len(df) >= lookback:")
                    code_lines.append("            high = df['High'].rolling(lookback).max().iloc[-1]")
                    code_lines.append("            low = df['Low'].rolling(lookback).min().iloc[-1]")
                    code_lines.append("            current = df['Close'].iloc[-1]")
                    code_lines.append("            if current > high:")
                    code_lines.append("                return 1")
                    code_lines.append("            elif current < low:")
                    code_lines.append("                return -1")
        
        code_lines.extend([
            '        return 0',
            '    ',
            '    def volatility(self, df: pd.DataFrame) -> Optional[float]:',
            '        """Calculate volatility."""',
            '        if "ATR" in df.columns and len(df) > 0:',
            '            atr = float(df["ATR"].iloc[-1])',
            '            price = float(df["Close"].iloc[-1])',
            '            if not pd.isna(atr) and price > 0:',
            '                return atr / price',
            '        return None',
            '    ',
            '    def stop_loss(self, df: pd.DataFrame, entry_price: float, side: int) -> Optional[float]:',
            '        """Calculate stop loss."""',
            '        if "ATR" in df.columns and len(df) > 0:',
            '            atr = float(df["ATR"].iloc[-1])',
            '            if side > 0:',
            '                return entry_price - (2 * atr)',
            '            else:',
            '                return entry_price + (2 * atr)',
            '        return None',
            '    ',
            '    def take_profit(self, df: pd.DataFrame, entry_price: float, side: int) -> Optional[float]:',
            '        """Calculate take profit."""',
            '        if "ATR" in df.columns and len(df) > 0:',
            '            atr = float(df["ATR"].iloc[-1])',
            '            if side > 0:',
            '                return entry_price + (4 * atr)',
            '            else:',
            '                return entry_price - (4 * atr)',
            '        return None',
        ])
        
        return '\n'.join(code_lines)

