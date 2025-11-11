"""
Marketplace Dialog
Provides UI for strategy marketplace.
"""

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QListWidget, QListWidgetItem, QTextEdit, QTableWidget,
    QTableWidgetItem, QHeaderView, QLineEdit, QComboBox,
    QMessageBox, QGroupBox, QFormLayout, QSpinBox, QWidget
)
from PyQt6.QtCore import Qt
from typing import Optional
from datetime import datetime
import uuid


class MarketplaceDialog(QDialog):
    """Dialog for strategy marketplace."""
    
    def __init__(self, show_my_strategies: bool = False, parent=None, language_manager=None):
        super().__init__(parent)
        self.show_my_strategies = show_my_strategies
        self.language_manager = language_manager
        self.marketplace = None
        title = "My Strategies" if show_my_strategies else "Strategy Marketplace"
        self.setWindowTitle(title)
        self.setModal(False)  # Allow multiple windows
        self.resize(1000, 700)
        self.setup_ui()
        self.load_strategies()
    
    def tr(self, key, default=None):
        """Get translated text."""
        if self.language_manager:
            return self.language_manager.tr(key, default)
        return default or key
    
    def setup_ui(self):
        """Setup UI."""
        layout = QVBoxLayout(self)
        layout.setSpacing(10)
        layout.setContentsMargins(15, 15, 15, 15)
        
        # Title
        title_text = "My Strategies" if self.show_my_strategies else "Strategy Marketplace"
        title_label = QLabel(title_text)
        title_label.setStyleSheet("font-size: 18px; font-weight: bold; padding: 10px; color: #2196F3;")
        layout.addWidget(title_label)
        
        # Controls
        controls_layout = QHBoxLayout()
        
        if not self.show_my_strategies:
            # Search box
            search_label = QLabel("Search:")
            self.search_edit = QLineEdit()
            self.search_edit.setPlaceholderText("Search strategies...")
            self.search_edit.setStyleSheet("""
                QLineEdit {
                    padding: 6px;
                    border: 1px solid #555;
                    border-radius: 4px;
                    background-color: #2b2b2b;
                    color: white;
                }
            """)
            self.search_edit.textChanged.connect(self.filter_strategies)
            controls_layout.addWidget(search_label)
            controls_layout.addWidget(self.search_edit)
            
            # Publish button
            publish_btn = QPushButton("Publish Strategy")
            publish_btn.setStyleSheet("""
                QPushButton {
                    background-color: #4CAF50;
                    color: white;
                    padding: 6px 15px;
                    border: none;
                    border-radius: 4px;
                    font-weight: bold;
                }
                QPushButton:hover {
                    background-color: #45a049;
                }
            """)
            publish_btn.clicked.connect(self.show_publish_dialog)
            controls_layout.addWidget(publish_btn)
        
        controls_layout.addStretch()
        layout.addLayout(controls_layout)
        
        # Strategies table
        self.strategies_table = QTableWidget()
        self.strategies_table.setColumnCount(6)
        headers = ["Strategy", "Author", "Rating", "Downloads", "Category", "Actions"]
        self.strategies_table.setHorizontalHeaderLabels(headers)
        self.strategies_table.setStyleSheet("""
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
        
        header = self.strategies_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)  # Strategy name
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)  # Author
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)  # Rating
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)  # Downloads
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)  # Category
        header.setSectionResizeMode(5, QHeaderView.ResizeMode.Fixed)  # Actions
        self.strategies_table.setColumnWidth(5, 150 if self.show_my_strategies else 110)
        
        self.strategies_table.setAlternatingRowColors(True)
        self.strategies_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.strategies_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        
        layout.addWidget(self.strategies_table)
        
        # Buttons
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        if not self.show_my_strategies:
            refresh_btn = QPushButton("Refresh")
            refresh_btn.setStyleSheet("""
                QPushButton {
                    background-color: #FF9800;
                    color: white;
                    padding: 6px 15px;
                    border: none;
                    border-radius: 4px;
                    font-weight: bold;
                }
                QPushButton:hover {
                    background-color: #F57C00;
                }
            """)
            refresh_btn.clicked.connect(self.load_strategies)
            button_layout.addWidget(refresh_btn)
        
        close_btn = QPushButton("Close")
        close_btn.setStyleSheet("""
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
        """)
        close_btn.clicked.connect(self.close)
        button_layout.addWidget(close_btn)
        layout.addLayout(button_layout)
    
    def load_strategies(self):
        """Load strategies from marketplace and available strategies."""
        try:
            from ..marketplace.marketplace import StrategyMarketplace, StrategyListing
            from ..strategies import STRATEGIES
            
            self.marketplace = StrategyMarketplace()
            
            # Get marketplace strategies
            if self.show_my_strategies:
                marketplace_strategies = self.marketplace.get_recent_strategies(limit=50)
            else:
                marketplace_strategies = self.marketplace.get_popular_strategies(limit=50)
            
            # If marketplace is empty, populate with available strategies
            if not marketplace_strategies and not self.show_my_strategies:
                marketplace_strategies = self._create_default_listings(STRATEGIES)
            
            # Populate table
            self.strategies_table.setRowCount(len(marketplace_strategies))
            
            for i, strategy in enumerate(marketplace_strategies):
                if hasattr(strategy, 'name'):
                    name = strategy.name
                    author = strategy.author
                    rating = f"{strategy.rating:.1f} ⭐" if strategy.rating > 0 else "No ratings"
                    downloads = str(strategy.download_count)
                    category = strategy.category
                    strategy_id = strategy.strategy_id
                else:
                    name = strategy.get('name', 'Unknown')
                    author = strategy.get('author', 'Unknown')
                    rating = f"{strategy.get('rating', 0):.1f} ⭐"
                    downloads = str(strategy.get('download_count', 0))
                    category = strategy.get('category', 'General')
                    strategy_id = strategy.get('strategy_id', '')
                
                self.strategies_table.setItem(i, 0, QTableWidgetItem(name))
                self.strategies_table.setItem(i, 1, QTableWidgetItem(author))
                self.strategies_table.setItem(i, 2, QTableWidgetItem(rating))
                self.strategies_table.setItem(i, 3, QTableWidgetItem(downloads))
                self.strategies_table.setItem(i, 4, QTableWidgetItem(category))
                
                # Actions button
                actions_widget = QWidget()
                actions_widget.setMinimumWidth(150 if self.show_my_strategies else 110)
                actions_layout = QHBoxLayout(actions_widget)
                actions_layout.setContentsMargins(2, 2, 2, 2)
                actions_layout.setSpacing(5)
                
                download_btn = QPushButton("Download")
                download_btn.setMinimumWidth(90)
                download_btn.setMinimumHeight(28)
                download_btn.setMaximumWidth(90)
                download_btn.setStyleSheet("""
                    QPushButton {
                        background-color: #2196F3;
                        color: white;
                        padding: 5px 12px;
                        border: none;
                        border-radius: 3px;
                        font-size: 11px;
                        font-weight: bold;
                    }
                    QPushButton:hover {
                        background-color: #1976D2;
                    }
                """)
                download_btn.clicked.connect(lambda checked, sid=strategy_id: self.download_strategy(sid))
                actions_layout.addWidget(download_btn)
                
                if self.show_my_strategies:
                    remove_btn = QPushButton("Remove")
                    remove_btn.setMinimumWidth(75)
                    remove_btn.setMinimumHeight(28)
                    remove_btn.setMaximumWidth(75)
                    remove_btn.setStyleSheet("""
                        QPushButton {
                            background-color: #f44336;
                            color: white;
                            padding: 5px 12px;
                            border: none;
                            border-radius: 3px;
                            font-size: 11px;
                            font-weight: bold;
                        }
                        QPushButton:hover {
                            background-color: #da190b;
                        }
                    """)
                    remove_btn.clicked.connect(lambda checked, sid=strategy_id: self.remove_strategy(sid))
                    actions_layout.addWidget(remove_btn)
                
                actions_layout.addStretch()
                self.strategies_table.setCellWidget(i, 5, actions_widget)
            
            if not marketplace_strategies:
                self.strategies_table.setRowCount(1)
                self.strategies_table.setItem(0, 0, QTableWidgetItem("No strategies available"))
                self.strategies_table.setItem(0, 1, QTableWidgetItem(""))
                self.strategies_table.setItem(0, 2, QTableWidgetItem(""))
                self.strategies_table.setItem(0, 3, QTableWidgetItem(""))
                self.strategies_table.setItem(0, 4, QTableWidgetItem(""))
                self.strategies_table.setItem(0, 5, QTableWidgetItem(""))
                
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to load strategies: {e}")
    
    def _create_default_listings(self, available_strategies):
        """Create default listings from available strategies."""
        from ..marketplace.marketplace import StrategyListing
        
        listings = []
        for strategy_name in available_strategies.keys():
            listing = StrategyListing(
                strategy_id=str(uuid.uuid4()),
                name=strategy_name,
                description=f"Built-in {strategy_name} strategy",
                author="ForexSmartBot",
                version="1.0.0",
                category="Built-in",
                tags=["built-in", "default"],
                created_at=datetime.now(),
                updated_at=datetime.now(),
                download_count=0,
                rating=0.0,
                rating_count=0
            )
            listings.append(listing)
            # Add to marketplace
            self.marketplace.add_listing(listing)
        
        return listings
    
    def filter_strategies(self):
        """Filter strategies based on search text."""
        search_text = self.search_edit.text().lower()
        
        for i in range(self.strategies_table.rowCount()):
            strategy_name = self.strategies_table.item(i, 0)
            if strategy_name:
                if search_text in strategy_name.text().lower():
                    self.strategies_table.setRowHidden(i, False)
                else:
                    self.strategies_table.setRowHidden(i, True)
    
    def show_publish_dialog(self):
        """Show dialog to publish a strategy."""
        dialog = QDialog(self)
        dialog.setWindowTitle("Publish Strategy")
        dialog.setModal(True)
        dialog.resize(500, 400)
        
        layout = QVBoxLayout(dialog)
        
        form_group = QGroupBox("Strategy Information")
        form_layout = QFormLayout(form_group)
        
        name_edit = QLineEdit()
        name_edit.setPlaceholderText("Strategy name")
        form_layout.addRow("Name:", name_edit)
        
        desc_edit = QTextEdit()
        desc_edit.setPlaceholderText("Strategy description")
        desc_edit.setMaximumHeight(80)
        form_layout.addRow("Description:", desc_edit)
        
        author_edit = QLineEdit()
        author_edit.setPlaceholderText("Your name")
        form_layout.addRow("Author:", author_edit)
        
        category_combo = QComboBox()
        category_combo.addItems(["Trend Following", "Mean Reversion", "Breakout", "Scalping", "ML/AI", "Other"])
        form_layout.addRow("Category:", category_combo)
        
        version_edit = QLineEdit()
        version_edit.setText("1.0.0")
        form_layout.addRow("Version:", version_edit)
        
        layout.addWidget(form_group)
        
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        publish_btn = QPushButton("Publish")
        publish_btn.clicked.connect(lambda: self.publish_strategy(
            dialog, name_edit.text(), desc_edit.toPlainText(),
            author_edit.text(), category_combo.currentText(), version_edit.text()
        ))
        button_layout.addWidget(publish_btn)
        
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(dialog.close)
        button_layout.addWidget(cancel_btn)
        
        layout.addLayout(button_layout)
        dialog.exec()
    
    def publish_strategy(self, dialog, name, description, author, category, version):
        """Publish a strategy to marketplace."""
        try:
            if not name or not description or not author:
                QMessageBox.warning(dialog, "Validation", "Please fill in all required fields")
                return
            
            from ..marketplace.marketplace import StrategyListing
            
            listing = StrategyListing(
                strategy_id=str(uuid.uuid4()),
                name=name,
                description=description,
                author=author,
                version=version,
                category=category,
                tags=[],
                created_at=datetime.now(),
                updated_at=datetime.now()
            )
            
            self.marketplace.add_listing(listing)
            QMessageBox.information(dialog, "Success", "Strategy published successfully!")
            dialog.close()
            self.load_strategies()
            
        except Exception as e:
            QMessageBox.critical(dialog, "Error", f"Failed to publish strategy: {e}")
    
    def download_strategy(self, strategy_id):
        """Download a strategy."""
        try:
            listing = self.marketplace.get_listing(strategy_id)
            if listing:
                self.marketplace.increment_download(strategy_id)
                QMessageBox.information(self, "Success", f"Strategy '{listing.name}' downloaded successfully!")
                self.load_strategies()
            else:
                QMessageBox.warning(self, "Error", "Strategy not found")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to download strategy: {e}")
    
    def remove_strategy(self, strategy_id):
        """Remove a strategy from marketplace."""
        try:
            listing = self.marketplace.get_listing(strategy_id)
            if listing:
                reply = QMessageBox.question(
                    self, "Confirm", 
                    f"Are you sure you want to remove '{listing.name}'?",
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
                )
                if reply == QMessageBox.StandardButton.Yes:
                    self.marketplace.remove_listing(strategy_id)
                    QMessageBox.information(self, "Success", "Strategy removed successfully!")
                    self.load_strategies()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to remove strategy: {e}")

