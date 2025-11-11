"""
Economic Calendar Integration Module
"""

import requests
from typing import Dict, List, Optional
from datetime import datetime, timedelta
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem, 
    QLabel, QDateEdit, QPushButton, QHeaderView, QMessageBox
)
from PyQt6.QtCore import QDate, Qt, QThread, pyqtSignal
import json


class EconomicCalendarLoader(QThread):
    """Thread for loading economic calendar events."""
    
    events_loaded = pyqtSignal(list)
    error_occurred = pyqtSignal(str)
    
    def __init__(self, provider, start_date, end_date):
        super().__init__()
        self.provider = provider
        self.start_date = start_date
        self.end_date = end_date
    
    def run(self):
        """Load events in background thread."""
        try:
            events = self.provider.get_events(self.start_date, self.end_date)
            self.events_loaded.emit(events)
        except Exception as e:
            self.error_occurred.emit(str(e))


class EconomicCalendarWidget(QWidget):
    """Widget for displaying economic calendar events."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.events = []
        self.provider = EconomicCalendarProvider()
        self.loader_thread = None
        self.setup_ui()
        self.load_events()  # Auto-load events on initialization
        
    def setup_ui(self):
        """Setup the UI."""
        layout = QVBoxLayout(self)
        layout.setSpacing(10)
        layout.setContentsMargins(10, 10, 10, 10)
        
        # Title
        title = QLabel("Economic Calendar")
        title.setStyleSheet("font-size: 18px; font-weight: bold; padding: 5px; color: #2196F3;")
        layout.addWidget(title)
        
        # Controls layout
        controls_layout = QHBoxLayout()
        controls_layout.setSpacing(10)
        
        # Date selector
        controls_layout.addWidget(QLabel("Date:"))
        self.date_edit = QDateEdit()
        self.date_edit.setDate(QDate.currentDate())
        self.date_edit.setCalendarPopup(True)
        self.date_edit.setDisplayFormat("dd.MM.yyyy")
        self.date_edit.dateChanged.connect(self.on_date_changed)
        self.date_edit.setStyleSheet("""
            QDateEdit {
                padding: 5px;
                border: 1px solid #555;
                border-radius: 4px;
                background-color: #2b2b2b;
                color: white;
            }
            QDateEdit::drop-down {
                border: none;
                width: 20px;
            }
        """)
        controls_layout.addWidget(self.date_edit)
        
        # Refresh button
        self.refresh_btn = QPushButton("Refresh")
        self.refresh_btn.setStyleSheet("""
            QPushButton {
                background-color: #2196F3;
                color: white;
                padding: 6px 15px;
                border: none;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #1976D2;
            }
            QPushButton:pressed {
                background-color: #0D47A1;
            }
        """)
        self.refresh_btn.clicked.connect(self.load_events)
        controls_layout.addWidget(self.refresh_btn)
        
        controls_layout.addStretch()
        layout.addLayout(controls_layout)
        
        # Status label
        self.status_label = QLabel("Loading events...")
        self.status_label.setStyleSheet("color: #888; font-style: italic;")
        layout.addWidget(self.status_label)
        
        # Events table with improved UX/UI
        self.events_table = QTableWidget()
        self.events_table.setColumnCount(5)
        self.events_table.setHorizontalHeaderLabels([
            'Time', 'Currency', 'Event', 'Impact', 'Previous'
        ])
        
        # Enhanced table styling
        self.events_table.setStyleSheet("""
            QTableWidget {
                background-color: #1e1e1e;
                alternate-background-color: #252525;
                color: white;
                border: 1px solid #444;
                border-radius: 4px;
                gridline-color: #333;
            }
            QTableWidget::item {
                padding: 8px;
                border: none;
            }
            QTableWidget::item:selected {
                background-color: #2196F3;
                color: white;
            }
            QHeaderView::section {
                background-color: #2b2b2b;
                color: white;
                padding: 8px;
                border: 1px solid #444;
                font-weight: bold;
            }
            QTableWidget::item:hover {
                background-color: #2b2b2b;
            }
        """)
        
        # Set column widths
        header = self.events_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)  # Time
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)  # Currency
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)  # Event (stretches)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)  # Impact
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)  # Previous
        
        # Enable alternating row colors
        self.events_table.setAlternatingRowColors(True)
        
        # Make table read-only
        self.events_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        
        # Enable selection
        self.events_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.events_table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        
        layout.addWidget(self.events_table)
        
    def on_date_changed(self, date):
        """Handle date change."""
        # Optionally auto-reload when date changes
        # Uncomment the line below if you want auto-reload on date change
        # self.load_events()
        pass
        
    def load_events(self):
        """Load economic calendar events for the selected date."""
        if self.loader_thread and self.loader_thread.isRunning():
            return  # Don't start multiple loads
        
        selected_date = self.date_edit.date().toPyDate()
        start_date = datetime.combine(selected_date, datetime.min.time())
        end_date = datetime.combine(selected_date, datetime.max.time())
        
        self.status_label.setText("Loading events...")
        self.refresh_btn.setEnabled(False)
        
        # Create and start loader thread
        self.loader_thread = EconomicCalendarLoader(self.provider, start_date, end_date)
        self.loader_thread.events_loaded.connect(self.on_events_loaded)
        self.loader_thread.error_occurred.connect(self.on_load_error)
        self.loader_thread.start()
        
    def on_events_loaded(self, events: List[Dict]):
        """Handle events loaded signal."""
        self.events = events
        self._populate_table()
        
        if len(events) == 0:
            self.status_label.setText("No events found. Configure API keys in .env file. See docs/ECONOMIC_CALENDAR_API_SETUP.md")
        else:
            self.status_label.setText(f"Loaded {len(events)} events")
        
        self.refresh_btn.setEnabled(True)
        
    def on_load_error(self, error: str):
        """Handle load error."""
        self.status_label.setText(f"Error: {error}")
        self.refresh_btn.setEnabled(True)
        
        # Show helpful error message
        error_msg = f"Failed to load economic events: {error}\n\n"
        error_msg += "To get real economic calendar data, please configure API keys:\n"
        error_msg += "1. See docs/ECONOMIC_CALENDAR_API_SETUP.md for setup instructions\n"
        error_msg += "2. Add API keys to your .env file\n"
        error_msg += "3. Free options: Alpha Vantage, FRED, NewsAPI"
        
        QMessageBox.warning(self, "Economic Calendar Error", error_msg)
        
    def update_events(self, events: List[Dict]):
        """
        Update economic calendar events.
        
        Args:
            events: List of event dictionaries
        """
        self.events = events
        self._populate_table()
        
    def _populate_table(self):
        """Populate events table with improved formatting."""
        self.events_table.setRowCount(len(self.events))
        
        if not self.events:
            self.status_label.setText("No events found for selected date")
            return
        
        for i, event in enumerate(self.events):
            # Time
            time_str = event.get('time', 'N/A')
            time_item = QTableWidgetItem(time_str)
            time_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.events_table.setItem(i, 0, time_item)
            
            # Currency
            currency = event.get('currency', 'N/A')
            currency_item = QTableWidgetItem(currency)
            currency_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            currency_item.setFont(self.font())  # Use default font
            self.events_table.setItem(i, 1, currency_item)
            
            # Event
            event_name = event.get('event', 'N/A')
            event_item = QTableWidgetItem(event_name)
            event_item.setToolTip(event_name)  # Show full name on hover
            self.events_table.setItem(i, 2, event_item)
            
            # Impact with color coding
            impact = event.get('impact', 'N/A')
            impact_item = QTableWidgetItem(impact)
            impact_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            
            # Color coding for impact
            if impact == 'High':
                impact_item.setForeground(Qt.GlobalColor.red)
                impact_item.setBackground(Qt.GlobalColor.darkRed)
            elif impact == 'Medium':
                impact_item.setForeground(Qt.GlobalColor.orange)
                impact_item.setBackground(Qt.GlobalColor.darkYellow)
            elif impact == 'Low':
                impact_item.setForeground(Qt.GlobalColor.green)
                impact_item.setBackground(Qt.GlobalColor.darkGreen)
            else:
                impact_item.setForeground(Qt.GlobalColor.gray)
            
            self.events_table.setItem(i, 3, impact_item)
            
            # Previous
            previous = event.get('previous', 'N/A')
            previous_item = QTableWidgetItem(str(previous))
            previous_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            self.events_table.setItem(i, 4, previous_item)
        
        # Resize columns to fit content
        self.events_table.resizeColumnsToContents()
        # But keep Event column stretchable
        header = self.events_table.horizontalHeader()
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)


class EconomicCalendarProvider:
    """Provider for economic calendar data from trusted APIs."""
    
    def __init__(self, api_key: Optional[str] = None):
        import os
        from dotenv import load_dotenv
        load_dotenv(override=False)
        
        # Try to get API keys from environment variables
        self.trading_economics_key = api_key or os.getenv('TRADING_ECONOMICS_API_KEY', '')
        self.alpha_vantage_key = os.getenv('ALPHA_VANTAGE_API_KEY', '')
        self.news_api_key = os.getenv('NEWS_API_KEY', '')
        self.fred_api_key = os.getenv('FRED_API_KEY', '')
        
        # API endpoints
        self.trading_economics_url = "https://api.tradingeconomics.com/calendar"
        self.alpha_vantage_url = "https://www.alphavantage.co/query"
        self.news_api_url = "https://newsapi.org/v2/everything"
        self.fred_url = "https://api.stlouisfed.org/fred/series/observations"
        
    def get_events(self, start_date: datetime, end_date: datetime,
                  currencies: Optional[List[str]] = None) -> List[Dict]:
        """
        Get economic calendar events from real APIs.
        
        Args:
            start_date: Start date
            end_date: End date
            currencies: List of currencies to filter (optional)
            
        Returns:
            List of event dictionaries
        """
        events = []
        
        # Try multiple API sources with fallbacks
        # 1. Try TradingEconomics API (most comprehensive)
        if self.trading_economics_key:
            try:
                events = self._get_trading_economics_events(start_date, end_date, currencies)
                if events:
                    return events
            except Exception as e:
                print(f"TradingEconomics API error: {e}")
        
        # 2. Try Alpha Vantage (free tier)
        if self.alpha_vantage_key:
            try:
                events = self._get_alpha_vantage_events(start_date, end_date, currencies)
                if events:
                    return events
            except Exception as e:
                print(f"Alpha Vantage API error: {e}")
        
        # 3. Try FRED API (free, US-focused, no key required for basic access)
        try:
            us_events = self._get_fred_events(start_date, end_date)
            if us_events:
                events.extend(us_events)
        except Exception as e:
            print(f"FRED API error: {e}")
        
        # 4. Try NewsAPI for economic news
        if self.news_api_key:
            try:
                news_events = self._get_newsapi_events(start_date, end_date, currencies)
                if news_events:
                    events.extend(news_events)
            except Exception as e:
                print(f"NewsAPI error: {e}")
        
        # 5. Try free public economic calendar APIs (fallback)
        if not events:
            try:
                free_events = self._get_free_economic_calendar(start_date, end_date, currencies)
                if free_events:
                    events.extend(free_events)
            except Exception as e:
                print(f"Free economic calendar API error: {e}")
        
        # If no events found, return empty list (don't generate fake data)
        if not events:
            print("Warning: No economic events found from any API source. Please configure API keys in .env file.")
            print("Available free APIs: FRED (US data, no key), Alpha Vantage (free tier), NewsAPI (free tier)")
        
        # Sort events by time
        events.sort(key=lambda x: (x.get('date', datetime.now().date()), x.get('time', '00:00')))
        
        return events
    
    def _get_trading_economics_events(self, start_date: datetime, end_date: datetime,
                                      currencies: Optional[List[str]] = None) -> List[Dict]:
        """Get events from TradingEconomics API."""
        try:
            # Format dates
            start_str = start_date.strftime('%Y-%m-%d')
            end_str = end_date.strftime('%Y-%m-%d')
            
            # Build URL
            url = f"{self.trading_economics_url}?c={self.trading_economics_key}&d1={start_str}&d2={end_str}"
            
            # Add currency filter if provided
            if currencies:
                currency_str = ','.join(currencies)
                url += f"&countries={currency_str}"
            
            # Make request
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            events = []
            for item in data:
                # Parse TradingEconomics format
                event_date = datetime.strptime(item.get('Date', ''), '%Y-%m-%dT%H:%M:%S')
                
                event = {
                    'time': event_date.strftime('%H:%M'),
                    'currency': item.get('Country', 'USD'),
                    'event': item.get('Event', 'N/A'),
                    'impact': self._map_impact(item.get('Importance', 0)),
                    'previous': str(item.get('Previous', 'N/A')),
                    'date': event_date.date()
                }
                events.append(event)
            
            return events
        except Exception as e:
            raise Exception(f"TradingEconomics API failed: {str(e)}")
    
    def _get_alpha_vantage_events(self, start_date: datetime, end_date: datetime,
                                  currencies: Optional[List[str]] = None) -> List[Dict]:
        """Get events from Alpha Vantage API."""
        try:
            events = []
            
            # Alpha Vantage provides economic indicators
            indicators = ['GDP', 'CPI', 'UNEMPLOYMENT', 'INTEREST_RATE']
            
            for indicator in indicators:
                url = f"{self.alpha_vantage_url}"
                params = {
                    'function': 'ECONOMIC_INDICATOR',
                    'indicator': indicator,
                    'apikey': self.alpha_vantage_key
                }
                
                response = requests.get(url, params=params, timeout=10)
                response.raise_for_status()
                data = response.json()
                
                # Parse Alpha Vantage format
                if 'data' in data:
                    for item in data['data']:
                        event_date = datetime.strptime(item.get('date', ''), '%Y-%m-%d')
                        if start_date <= event_date <= end_date:
                            event = {
                                'time': '08:00',  # Default time
                                'currency': item.get('country', 'USD'),
                                'event': indicator.replace('_', ' '),
                                'impact': 'Medium',
                                'previous': str(item.get('value', 'N/A')),
                                'date': event_date.date()
                            }
                            events.append(event)
            
            return events
        except Exception as e:
            raise Exception(f"Alpha Vantage API failed: {str(e)}")
    
    def _get_fred_events(self, start_date: datetime, end_date: datetime) -> List[Dict]:
        """Get US economic events from FRED API (free, requires API key)."""
        try:
            events = []
            
            # FRED requires an API key (free to get at https://fred.stlouisfed.org/docs/api/api_key.html)
            if not self.fred_api_key:
                return events  # Skip if no API key
            
            # FRED series IDs for major economic indicators
            fred_series = {
                'UNRATE': ('Unemployment Rate', 'High'),
                'CPIAUCSL': ('CPI', 'High'),
                'GDP': ('GDP', 'High'),
                'FEDFUNDS': ('Federal Funds Rate', 'High'),
                'RETAIL': ('Retail Sales', 'Medium'),
            }
            
            for series_id, (event_name, impact) in fred_series.items():
                url = f"{self.fred_url}"
                params = {
                    'series_id': series_id,
                    'api_key': self.fred_api_key,
                    'file_type': 'json',
                    'observation_start': start_date.strftime('%Y-%m-%d'),
                    'observation_end': end_date.strftime('%Y-%m-%d')
                }
                
                try:
                    response = requests.get(url, params=params, timeout=10)
                    response.raise_for_status()
                    data = response.json()
                    
                    if 'observations' in data:
                        for obs in data['observations']:
                            if obs.get('value') != '.':
                                event_date = datetime.strptime(obs.get('date', ''), '%Y-%m-%d')
                                event = {
                                    'time': '08:00',
                                    'currency': 'USD',
                                    'event': event_name,
                                    'impact': impact,
                                    'previous': str(obs.get('value', 'N/A')),
                                    'date': event_date.date()
                                }
                                events.append(event)
                except Exception as e:
                    print(f"FRED series {series_id} failed: {e}")
                    continue  # Skip if series fails
            
            return events
        except Exception as e:
            raise Exception(f"FRED API failed: {str(e)}")
    
    def _get_newsapi_events(self, start_date: datetime, end_date: datetime,
                           currencies: Optional[List[str]] = None) -> List[Dict]:
        """Get economic news from NewsAPI."""
        try:
            events = []
            
            # Build query
            query = "economic calendar OR economic indicator OR central bank OR interest rate"
            if currencies:
                query += " OR " + " OR ".join(currencies)
            
            url = f"{self.news_api_url}"
            params = {
                'q': query,
                'from': start_date.strftime('%Y-%m-%d'),
                'to': end_date.strftime('%Y-%m-%d'),
                'sortBy': 'publishedAt',
                'language': 'en',
                'apiKey': self.news_api_key
            }
            
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            if 'articles' in data:
                for article in data['articles']:
                    published = datetime.strptime(article.get('publishedAt', ''), '%Y-%m-%dT%H:%M:%SZ')
                    if start_date <= published <= end_date:
                        # Extract currency from title
                        currency = 'USD'
                        for curr in ['USD', 'EUR', 'GBP', 'JPY', 'AUD', 'CAD']:
                            if curr in article.get('title', ''):
                                currency = curr
                                break
                        
                        event = {
                            'time': published.strftime('%H:%M'),
                            'currency': currency,
                            'event': article.get('title', 'Economic News')[:50],
                            'impact': 'Medium',
                            'previous': 'N/A',
                            'date': published.date()
                        }
                        events.append(event)
            
            return events
        except Exception as e:
            raise Exception(f"NewsAPI failed: {str(e)}")
    
    def _get_free_economic_calendar(self, start_date: datetime, end_date: datetime,
                                    currencies: Optional[List[str]] = None) -> List[Dict]:
        """Get events from free public economic calendar sources."""
        try:
            events = []
            
            # Try using Investing.com's public economic calendar (scraping-free approach)
            # Use a free API aggregator or public endpoint
            # Note: This is a fallback that uses publicly available data
            
            # For now, we'll use a combination of public data sources
            # In production, you might want to use a service like:
            # - ForexFactory RSS feed (if available)
            # - Central bank websites
            # - Public economic data repositories
            
            # This is a placeholder that would need to be implemented with actual public APIs
            # For now, return empty to avoid fake data
            return []
            
        except Exception as e:
            raise Exception(f"Free economic calendar failed: {str(e)}")
    
    def _map_impact(self, importance: int) -> str:
        """Map importance score to impact level."""
        if importance >= 3:
            return 'High'
        elif importance >= 2:
            return 'Medium'
        else:
            return 'Low'
        
    def get_upcoming_high_impact_events(self, days: int = 7) -> List[Dict]:
        """
        Get upcoming high impact events.
        
        Args:
            days: Number of days to look ahead
            
        Returns:
            List of high impact events
        """
        start_date = datetime.now()
        end_date = start_date + timedelta(days=days)
        
        all_events = self.get_events(start_date, end_date)
        high_impact = [e for e in all_events if e.get('impact') == 'High']
        
        return high_impact

