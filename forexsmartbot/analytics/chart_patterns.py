"""
Chart Pattern Recognition Module
Identifies common chart patterns in price data.
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Tuple
from datetime import datetime
from scipy.signal import find_peaks


class ChartPatternRecognizer:
    """Recognizes chart patterns in price data."""
    
    def __init__(self):
        self.patterns = []
        
    def detect_patterns(self, data: pd.DataFrame, 
                      lookback: int = 50) -> List[Dict]:
        """
        Detect chart patterns in price data.
        
        Args:
            data: DataFrame with OHLCV data
            lookback: Number of periods to analyze
            
        Returns:
            List of detected patterns
        """
        if data is None or len(data) < lookback:
            return []
            
        # Use recent data
        recent_data = data.tail(lookback).copy()
        
        patterns = []
        
        # Detect various patterns
        patterns.extend(self._detect_head_and_shoulders(recent_data))
        patterns.extend(self._detect_double_top(recent_data))
        patterns.extend(self._detect_double_bottom(recent_data))
        patterns.extend(self._detect_triangles(recent_data))
        patterns.extend(self._detect_flags_pennants(recent_data))
        patterns.extend(self._detect_wedges(recent_data))
        patterns.extend(self._detect_support_resistance(recent_data))
        
        return patterns
        
    def _detect_head_and_shoulders(self, data: pd.DataFrame) -> List[Dict]:
        """Detect head and shoulders pattern."""
        patterns = []
        
        if len(data) < 20:
            return patterns
            
        highs = data['High'].values
        peaks, _ = find_peaks(highs, distance=5, prominence=np.std(highs) * 0.5)
        
        if len(peaks) >= 3:
            # Check for head and shoulders pattern
            for i in range(len(peaks) - 2):
                left_shoulder = peaks[i]
                head = peaks[i + 1]
                right_shoulder = peaks[i + 2]
                
                # Head should be higher than shoulders
                if (highs[head] > highs[left_shoulder] and 
                    highs[head] > highs[right_shoulder]):
                    # Shoulders should be roughly equal
                    shoulder_diff = abs(highs[left_shoulder] - highs[right_shoulder]) / highs[head]
                    if shoulder_diff < 0.05:  # 5% tolerance
                        patterns.append({
                            'pattern': 'Head and Shoulders',
                            'type': 'bearish',
                            'confidence': 0.7,
                            'start_idx': left_shoulder,
                            'end_idx': right_shoulder,
                            'price_level': highs[head]
                        })
                        
        return patterns
        
    def _detect_double_top(self, data: pd.DataFrame) -> List[Dict]:
        """Detect double top pattern."""
        patterns = []
        
        if len(data) < 20:
            return patterns
            
        highs = data['High'].values
        peaks, _ = find_peaks(highs, distance=5, prominence=np.std(highs) * 0.5)
        
        if len(peaks) >= 2:
            for i in range(len(peaks) - 1):
                peak1 = peaks[i]
                peak2 = peaks[i + 1]
                
                # Check if peaks are similar height
                peak_diff = abs(highs[peak1] - highs[peak2]) / highs[peak1]
                if peak_diff < 0.02:  # 2% tolerance
                    # Check for valley between peaks
                    valley_idx = peak1 + np.argmin(highs[peak1:peak2])
                    valley_depth = (highs[peak1] - highs[valley_idx]) / highs[peak1]
                    
                    if valley_depth > 0.03:  # At least 3% drop
                        patterns.append({
                            'pattern': 'Double Top',
                            'type': 'bearish',
                            'confidence': 0.75,
                            'start_idx': peak1,
                            'end_idx': peak2,
                            'price_level': highs[peak1]
                        })
                        
        return patterns
        
    def _detect_double_bottom(self, data: pd.DataFrame) -> List[Dict]:
        """Detect double bottom pattern."""
        patterns = []
        
        if len(data) < 20:
            return patterns
            
        lows = data['Low'].values
        troughs, _ = find_peaks(-lows, distance=5, prominence=np.std(lows) * 0.5)
        
        if len(troughs) >= 2:
            for i in range(len(troughs) - 1):
                bottom1 = troughs[i]
                bottom2 = troughs[i + 1]
                
                # Check if bottoms are similar depth
                bottom_diff = abs(lows[bottom1] - lows[bottom2]) / lows[bottom1]
                if bottom_diff < 0.02:  # 2% tolerance
                    # Check for peak between bottoms
                    peak_idx = bottom1 + np.argmax(lows[bottom1:bottom2])
                    peak_height = (lows[peak_idx] - lows[bottom1]) / lows[bottom1]
                    
                    if peak_height > 0.03:  # At least 3% rise
                        patterns.append({
                            'pattern': 'Double Bottom',
                            'type': 'bullish',
                            'confidence': 0.75,
                            'start_idx': bottom1,
                            'end_idx': bottom2,
                            'price_level': lows[bottom1]
                        })
                        
        return patterns
        
    def _detect_triangles(self, data: pd.DataFrame) -> List[Dict]:
        """Detect triangle patterns (ascending, descending, symmetrical)."""
        patterns = []
        
        if len(data) < 30:
            return patterns
            
        # Use recent data for triangle detection
        recent = data.tail(30)
        highs = recent['High'].values
        lows = recent['Low'].values
        
        # Find trend lines
        high_trend = np.polyfit(range(len(highs)), highs, 1)[0]
        low_trend = np.polyfit(range(len(lows)), lows, 1)[0]
        
        # Ascending triangle: horizontal resistance, rising support
        if abs(high_trend) < 0.0001 and low_trend > 0.0001:
            patterns.append({
                'pattern': 'Ascending Triangle',
                'type': 'bullish',
                'confidence': 0.65,
                'start_idx': len(data) - 30,
                'end_idx': len(data) - 1,
                'price_level': np.mean(highs)
            })
        # Descending triangle: falling resistance, horizontal support
        elif high_trend < -0.0001 and abs(low_trend) < 0.0001:
            patterns.append({
                'pattern': 'Descending Triangle',
                'type': 'bearish',
                'confidence': 0.65,
                'start_idx': len(data) - 30,
                'end_idx': len(data) - 1,
                'price_level': np.mean(lows)
            })
        # Symmetrical triangle: converging trend lines
        elif high_trend < -0.0001 and low_trend > 0.0001:
            patterns.append({
                'pattern': 'Symmetrical Triangle',
                'type': 'neutral',
                'confidence': 0.6,
                'start_idx': len(data) - 30,
                'end_idx': len(data) - 1,
                'price_level': np.mean([np.mean(highs), np.mean(lows)])
            })
            
        return patterns
        
    def _detect_flags_pennants(self, data: pd.DataFrame) -> List[Dict]:
        """Detect flag and pennant patterns."""
        patterns = []
        
        if len(data) < 20:
            return patterns
            
        # Flags and pennants are continuation patterns after strong moves
        recent = data.tail(20)
        price_change = (recent['Close'].iloc[-1] - recent['Close'].iloc[0]) / recent['Close'].iloc[0]
        
        if abs(price_change) > 0.02:  # At least 2% move
            volatility = recent['High'].std() / recent['Close'].mean()
            
            if volatility < 0.01:  # Low volatility consolidation
                pattern_type = 'bullish' if price_change > 0 else 'bearish'
                patterns.append({
                    'pattern': 'Flag/Pennant',
                    'type': pattern_type,
                    'confidence': 0.7,
                    'start_idx': len(data) - 20,
                    'end_idx': len(data) - 1,
                    'price_level': recent['Close'].iloc[-1]
                })
                
        return patterns
        
    def _detect_wedges(self, data: pd.DataFrame) -> List[Dict]:
        """Detect rising and falling wedge patterns."""
        patterns = []
        
        if len(data) < 30:
            return patterns
            
        recent = data.tail(30)
        highs = recent['High'].values
        lows = recent['Low'].values
        
        # Calculate trend slopes
        high_trend = np.polyfit(range(len(highs)), highs, 1)[0]
        low_trend = np.polyfit(range(len(lows)), lows, 1)[0]
        
        # Rising wedge: both trend lines rising, but converging
        if high_trend > 0 and low_trend > 0 and high_trend < low_trend:
            patterns.append({
                'pattern': 'Rising Wedge',
                'type': 'bearish',
                'confidence': 0.65,
                'start_idx': len(data) - 30,
                'end_idx': len(data) - 1,
                'price_level': np.mean(highs)
            })
        # Falling wedge: both trend lines falling, but converging
        elif high_trend < 0 and low_trend < 0 and abs(high_trend) < abs(low_trend):
            patterns.append({
                'pattern': 'Falling Wedge',
                'type': 'bullish',
                'confidence': 0.65,
                'start_idx': len(data) - 30,
                'end_idx': len(data) - 1,
                'price_level': np.mean(lows)
            })
            
        return patterns
        
    def _detect_support_resistance(self, data: pd.DataFrame) -> List[Dict]:
        """Detect support and resistance levels."""
        patterns = []
        
        if len(data) < 20:
            return patterns
            
        # Find price levels that are touched multiple times
        highs = data['High'].values
        lows = data['Low'].values
        
        # Cluster similar price levels
        price_levels = np.concatenate([highs, lows])
        price_levels = np.sort(price_levels)
        
        # Find clusters (support/resistance levels)
        clusters = []
        current_cluster = [price_levels[0]]
        
        for price in price_levels[1:]:
            if abs(price - current_cluster[-1]) / current_cluster[-1] < 0.01:  # 1% tolerance
                current_cluster.append(price)
            else:
                if len(current_cluster) >= 3:  # At least 3 touches
                    clusters.append(np.mean(current_cluster))
                current_cluster = [price]
                
        if len(current_cluster) >= 3:
            clusters.append(np.mean(current_cluster))
            
        # Add as patterns
        for cluster in clusters:
            # Determine if support or resistance
            touches_above = np.sum(highs >= cluster * 0.99)
            touches_below = np.sum(lows <= cluster * 1.01)
            
            if touches_above > touches_below:
                patterns.append({
                    'pattern': 'Resistance Level',
                    'type': 'bearish',
                    'confidence': 0.8,
                    'start_idx': 0,
                    'end_idx': len(data) - 1,
                    'price_level': cluster
                })
            else:
                patterns.append({
                    'pattern': 'Support Level',
                    'type': 'bullish',
                    'confidence': 0.8,
                    'start_idx': 0,
                    'end_idx': len(data) - 1,
                    'price_level': cluster
                })
                
        return patterns

