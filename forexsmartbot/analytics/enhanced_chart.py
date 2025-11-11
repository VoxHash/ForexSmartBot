"""
Enhanced Chart with Pattern Recognition Integration
Extends TradingView chart with pattern recognition capabilities.
"""

import pandas as pd
from typing import Dict, List, Optional
from .chart_patterns import ChartPatternRecognizer
from ..ui.tradingview_chart import TradingViewChart


class EnhancedTradingViewChart(TradingViewChart):
    """Enhanced TradingView chart with pattern recognition."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.pattern_recognizer = ChartPatternRecognizer()
        self.detected_patterns = []
        self.show_patterns = True
        
    def detect_and_display_patterns(self, data: pd.DataFrame):
        """
        Detect patterns and display on chart.
        
        Args:
            data: Price data DataFrame
        """
        if data is None or len(data) < 20:
            return
            
        # Detect patterns
        self.detected_patterns = self.pattern_recognizer.detect_patterns(data)
        
        # Update chart with pattern annotations
        if self.show_patterns:
            self._annotate_patterns()
            
    def _annotate_patterns(self):
        """Annotate detected patterns on the chart."""
        if not self.detected_patterns or self.data is None:
            return
            
        # This would be called during chart update
        # Patterns would be drawn on the chart axes
        pass
        
    def toggle_pattern_display(self, show: bool):
        """Toggle pattern display on/off."""
        self.show_patterns = show
        if show and self.data is not None:
            self.detect_and_display_patterns(self.data)
            self.update_chart()
            
    def get_pattern_summary(self) -> List[Dict]:
        """Get summary of detected patterns."""
        return self.detected_patterns

