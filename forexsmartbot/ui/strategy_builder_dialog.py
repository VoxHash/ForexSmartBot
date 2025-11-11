"""
Strategy Builder Dialog
Enhanced visual strategy builder interface with template loading, code generation, and testing.
"""

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QTextEdit, QMessageBox, QTreeWidget, QTreeWidgetItem,
    QGroupBox, QFormLayout, QSpinBox, QDoubleSpinBox, QLineEdit,
    QTabWidget, QWidget, QSplitter, QListWidget, QListWidgetItem
)
from PyQt6.QtCore import Qt
from typing import Optional, Dict, Any
import json


class StrategyBuilderDialog(QDialog):
    """Enhanced dialog for visual strategy builder."""
    
    def __init__(self, parent=None, language_manager=None):
        super().__init__(parent)
        self.language_manager = language_manager
        self.builder = None
        self.setWindowTitle("Strategy Builder")
        self.setModal(False)  # Allow multiple windows
        self.resize(1200, 800)
        self.setup_ui()
    
    def tr(self, key, default=None):
        """Get translated text."""
        if self.language_manager:
            return self.language_manager.tr(key, default)
        return default or key
    
    def setup_ui(self):
        """Setup UI."""
        layout = QVBoxLayout(self)
        
        # Title
        title = QLabel("Visual Strategy Builder")
        title.setStyleSheet("font-size: 18px; font-weight: bold; padding: 10px;")
        layout.addWidget(title)
        
        # Main splitter
        splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # Left panel: Components and Templates
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        
        # Templates section
        templates_group = QGroupBox("Strategy Templates")
        templates_layout = QVBoxLayout(templates_group)
        
        self.templates_list = QListWidget()
        self.templates_list.addItems(["SMA Crossover", "RSI Reversion", "Breakout ATR"])
        self.templates_list.itemDoubleClicked.connect(self.load_template)
        templates_layout.addWidget(self.templates_list)
        
        load_template_btn = QPushButton("Load Template")
        load_template_btn.clicked.connect(self.load_selected_template)
        templates_layout.addWidget(load_template_btn)
        
        left_layout.addWidget(templates_group)
        
        # Components section
        components_group = QGroupBox("Available Components")
        components_layout = QVBoxLayout(components_group)
        
        self.components_tree = QTreeWidget()
        self.components_tree.setHeaderLabel("Component Type")
        self.components_tree.setRootIsDecorated(True)
        
        # Add component categories
        indicators_item = QTreeWidgetItem(self.components_tree, ["Indicators"])
        indicators_item.addChild(QTreeWidgetItem(["SMA (Simple Moving Average)"]))
        indicators_item.addChild(QTreeWidgetItem(["RSI (Relative Strength Index)"]))
        indicators_item.addChild(QTreeWidgetItem(["ATR (Average True Range)"]))
        indicators_item.addChild(QTreeWidgetItem(["MACD"]))
        indicators_item.addChild(QTreeWidgetItem(["Bollinger Bands"]))
        
        signals_item = QTreeWidgetItem(self.components_tree, ["Signals"])
        signals_item.addChild(QTreeWidgetItem(["Crossover Signal"]))
        signals_item.addChild(QTreeWidgetItem(["Mean Reversion Signal"]))
        signals_item.addChild(QTreeWidgetItem(["Breakout Signal"]))
        signals_item.addChild(QTreeWidgetItem(["Momentum Signal"]))
        
        filters_item = QTreeWidgetItem(self.components_tree, ["Filters"])
        filters_item.addChild(QTreeWidgetItem(["RSI Filter"]))
        filters_item.addChild(QTreeWidgetItem(["Volatility Filter"]))
        filters_item.addChild(QTreeWidgetItem(["Trend Filter"]))
        
        risk_item = QTreeWidgetItem(self.components_tree, ["Risk Management"])
        risk_item.addChild(QTreeWidgetItem(["ATR-based SL/TP"]))
        risk_item.addChild(QTreeWidgetItem(["Fixed SL/TP"]))
        risk_item.addChild(QTreeWidgetItem(["Trailing Stop"]))
        
        self.components_tree.expandAll()
        components_layout.addWidget(self.components_tree)
        
        add_component_btn = QPushButton("Add Component")
        add_component_btn.clicked.connect(self.add_selected_component)
        components_layout.addWidget(add_component_btn)
        
        left_layout.addWidget(components_group)
        left_layout.addStretch()
        
        splitter.addWidget(left_panel)
        
        # Center panel: Strategy Structure
        center_panel = QWidget()
        center_layout = QVBoxLayout(center_panel)
        
        structure_group = QGroupBox("Strategy Structure")
        structure_layout = QVBoxLayout(structure_group)
        
        self.strategy_tree = QTreeWidget()
        self.strategy_tree.setHeaderLabels(["Component", "Type", "Parameters"])
        self.strategy_tree.setRootIsDecorated(True)
        structure_layout.addWidget(self.strategy_tree)
        
        # Parameter editor
        params_group = QGroupBox("Component Parameters")
        params_layout = QVBoxLayout(params_group)
        
        self.params_widget = QWidget()
        self.params_layout = QFormLayout(self.params_widget)
        params_layout.addWidget(self.params_widget)
        
        center_layout.addWidget(structure_group)
        center_layout.addWidget(params_group)
        
        splitter.addWidget(center_panel)
        
        # Right panel: Code and Actions
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        
        # Tabs for code preview and validation
        tabs = QTabWidget()
        
        # Code preview tab
        code_tab = QWidget()
        code_layout = QVBoxLayout(code_tab)
        
        code_label = QLabel("Generated Code Preview:")
        code_layout.addWidget(code_label)
        
        self.code_preview = QTextEdit()
        self.code_preview.setReadOnly(True)
        self.code_preview.setFontFamily("Courier")
        code_layout.addWidget(self.code_preview)
        
        tabs.addTab(code_tab, "Code Preview")
        
        # Validation tab
        validation_tab = QWidget()
        validation_layout = QVBoxLayout(validation_tab)
        
        validation_label = QLabel("Strategy Validation:")
        validation_layout.addWidget(validation_label)
        
        self.validation_text = QTextEdit()
        self.validation_text.setReadOnly(True)
        validation_layout.addWidget(self.validation_text)
        
        tabs.addTab(validation_tab, "Validation")
        
        right_layout.addWidget(tabs)
        
        # Action buttons
        actions_group = QGroupBox("Actions")
        actions_layout = QVBoxLayout(actions_group)
        
        generate_code_btn = QPushButton("Generate Code")
        generate_code_btn.clicked.connect(self.generate_code)
        actions_layout.addWidget(generate_code_btn)
        
        validate_btn = QPushButton("Validate Strategy")
        validate_btn.clicked.connect(self.validate_strategy)
        actions_layout.addWidget(validate_btn)
        
        save_btn = QPushButton("Save Strategy")
        save_btn.clicked.connect(self.save_strategy)
        actions_layout.addWidget(save_btn)
        
        load_btn = QPushButton("Load Strategy")
        load_btn.clicked.connect(self.load_strategy)
        actions_layout.addWidget(load_btn)
        
        test_btn = QPushButton("Test Strategy")
        test_btn.clicked.connect(self.test_strategy)
        actions_layout.addWidget(test_btn)
        
        clear_btn = QPushButton("Clear All")
        clear_btn.clicked.connect(self.clear_strategy)
        actions_layout.addWidget(clear_btn)
        
        right_layout.addWidget(actions_group)
        
        splitter.addWidget(right_panel)
        
        # Set splitter sizes
        splitter.setSizes([250, 500, 450])
        layout.addWidget(splitter)
        
        # Bottom buttons
        button_layout = QHBoxLayout()
        
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.close)
        button_layout.addWidget(close_btn)
        
        button_layout.addStretch()
        layout.addLayout(button_layout)
        
        # Connect tree selection
        self.strategy_tree.itemSelectionChanged.connect(self.on_component_selected)
    
    def load_selected_template(self):
        """Load the selected template."""
        current_item = self.templates_list.currentItem()
        if current_item:
            self.load_template(current_item)
    
    def load_template(self, item):
        """Load a strategy template."""
        try:
            from ..builder.strategy_template import StrategyTemplate
            
            template_name = item.text() if hasattr(item, 'text') else str(item)
            
            # Map display names to template names
            template_map = {
                "SMA Crossover": "SMA Crossover",
                "RSI Reversion": "RSI Mean Reversion",
                "Breakout ATR": "Breakout"
            }
            
            actual_name = template_map.get(template_name, template_name)
            self.builder = StrategyTemplate.get_template(actual_name)
            
            # Update UI
            self.update_strategy_tree()
            self.validate_strategy()
            
            QMessageBox.information(self, "Template Loaded", 
                                  f"Template '{template_name}' loaded successfully!")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to load template: {e}")
    
    def add_selected_component(self):
        """Add selected component to strategy."""
        current_item = self.components_tree.currentItem()
        if not current_item or current_item.parent() is None:
            QMessageBox.warning(self, "Warning", "Please select a component to add.")
            return
        
        if self.builder is None:
            from ..builder.strategy_builder import StrategyBuilder, ComponentType
            self.builder = StrategyBuilder()
        
        component_name = current_item.text(0)
        component_type = self._get_component_type(current_item)
        
        if component_type:
            params = self._get_default_params(component_name, component_type)
            comp_id = self.builder.add_component(component_type, component_name, params)
            self.update_strategy_tree()
            QMessageBox.information(self, "Component Added", f"Added {component_name}")
    
    def _get_component_type(self, item):
        """Get component type from tree item."""
        from ..builder.strategy_builder import ComponentType
        
        parent = item.parent()
        if parent:
            parent_text = parent.text(0)
            if "Indicator" in parent_text:
                return ComponentType.INDICATOR
            elif "Signal" in parent_text:
                return ComponentType.SIGNAL
            elif "Filter" in parent_text:
                return ComponentType.FILTER
            elif "Risk" in parent_text:
                return ComponentType.RISK_MANAGEMENT
        return None
    
    def _get_default_params(self, name, component_type):
        """Get default parameters for a component."""
        from ..builder.strategy_builder import ComponentType
        
        params = {}
        if component_type == ComponentType.INDICATOR:
            if "SMA" in name:
                params = {"period": 20}
            elif "RSI" in name:
                params = {"period": 14}
            elif "ATR" in name:
                params = {"period": 14}
        elif component_type == ComponentType.SIGNAL:
            if "Crossover" in name:
                params = {"type": "crossover"}
            elif "Mean Reversion" in name:
                params = {"type": "mean_reversion"}
            elif "Breakout" in name:
                params = {"lookback_period": 20, "atr_multiplier": 1.5}
        elif component_type == ComponentType.FILTER:
            if "RSI" in name:
                params = {"oversold": 30, "overbought": 70}
        elif component_type == ComponentType.RISK_MANAGEMENT:
            if "ATR" in name:
                params = {"sl_multiplier": 2.0, "tp_multiplier": 3.0}
            else:
                params = {"stop_loss": 0.02, "take_profit": 0.03}
        
        return params
    
    def update_strategy_tree(self):
        """Update the strategy structure tree."""
        self.strategy_tree.clear()
        
        if self.builder is None:
            return
        
        structure = self.builder.get_strategy_structure()
        
        for comp_id, comp_data in structure['components'].items():
            item = QTreeWidgetItem(self.strategy_tree, [
                comp_data['name'],
                comp_data['type'],
                str(comp_data['parameters'])
            ])
            item.setData(0, Qt.ItemDataRole.UserRole, comp_id)
            
            # Add connections
            if comp_data.get('connections'):
                for conn_id in comp_data['connections']:
                    if conn_id in structure['components']:
                        conn_name = structure['components'][conn_id]['name']
                        conn_item = QTreeWidgetItem(item, [f"→ {conn_name}", "", ""])
    
    def on_component_selected(self):
        """Handle component selection in tree."""
        current_item = self.strategy_tree.currentItem()
        if not current_item or self.builder is None:
            return
        
        comp_id = current_item.data(0, Qt.ItemDataRole.UserRole)
        if not comp_id:
            return
        
        # Clear parameter form
        while self.params_layout.count():
            child = self.params_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
        
        # Get component
        component = self.builder.components.get(comp_id)
        if not component:
            return
        
        # Create parameter editors
        self.param_widgets = {}
        for param_name, param_value in component.parameters.items():
            if isinstance(param_value, int):
                widget = QSpinBox()
                widget.setRange(1, 1000)
                widget.setValue(param_value)
                widget.valueChanged.connect(lambda v, p=param_name: self.update_param(comp_id, p, v))
            elif isinstance(param_value, float):
                widget = QDoubleSpinBox()
                widget.setRange(0.01, 100.0)
                widget.setDecimals(4)
                widget.setValue(param_value)
                widget.valueChanged.connect(lambda v, p=param_name: self.update_param(comp_id, p, v))
            else:
                widget = QLineEdit(str(param_value))
                widget.textChanged.connect(lambda t, p=param_name: self.update_param(comp_id, p, t))
            
            self.params_layout.addRow(param_name + ":", widget)
            self.param_widgets[param_name] = widget
    
    def update_param(self, comp_id, param_name, value):
        """Update component parameter."""
        if self.builder:
            self.builder.update_component_params(comp_id, {param_name: value})
            self.update_strategy_tree()
    
    def generate_code(self):
        """Generate Python code from strategy."""
        if self.builder is None:
            QMessageBox.warning(self, "Warning", "No strategy loaded. Please load a template or add components.")
            return
        
        try:
            from ..builder.code_generator import CodeGenerator
            
            generator = CodeGenerator(self.builder)
            code = generator.generate_code()
            self.code_preview.setPlainText(code)
            
            QMessageBox.information(self, "Code Generated", "Strategy code generated successfully!")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to generate code: {e}")
    
    def validate_strategy(self):
        """Validate the strategy structure."""
        if self.builder is None:
            self.validation_text.setPlainText("No strategy loaded.")
            return
        
        is_valid, errors = self.builder.validate_strategy()
        
        if is_valid:
            self.validation_text.setPlainText("✓ Strategy is valid!\n\nComponents:\n" + 
                                            "\n".join([f"- {comp.name} ({comp.component_type.value})" 
                                                      for comp in self.builder.components.values()]))
        else:
            self.validation_text.setPlainText("✗ Strategy has errors:\n\n" + "\n".join(errors))
    
    def save_strategy(self):
        """Save strategy to file."""
        if self.builder is None:
            QMessageBox.warning(self, "Warning", "No strategy to save.")
            return
        
        try:
            structure = self.builder.get_strategy_structure()
            code = json.dumps(structure, indent=2)
            
            # For now, just show in message box
            # In production, would use file dialog
            QMessageBox.information(self, "Strategy Saved", 
                                  f"Strategy structure:\n\n{code}")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save strategy: {e}")
    
    def load_strategy(self):
        """Load strategy from file."""
        QMessageBox.information(self, "Load Strategy", 
                              "Load strategy functionality - to be implemented with file dialog")
    
    def test_strategy(self):
        """Test strategy with paper trading."""
        if self.builder is None:
            QMessageBox.warning(self, "Warning", "No strategy to test.")
            return
        
        # Validate first
        is_valid, errors = self.builder.validate_strategy()
        if not is_valid:
            QMessageBox.warning(self, "Invalid Strategy", 
                              "Please fix errors before testing:\n" + "\n".join(errors))
            return
        
        QMessageBox.information(self, "Test Strategy", 
                              "Strategy testing with paper account - to be integrated")
    
    def clear_strategy(self):
        """Clear all components."""
        if self.builder:
            self.builder.clear()
            self.update_strategy_tree()
            self.code_preview.clear()
            self.validation_text.clear()
            QMessageBox.information(self, "Cleared", "Strategy cleared.")


class StrategyTemplatesDialog(QDialog):
    """Enhanced dialog for strategy templates."""
    
    def __init__(self, parent=None, language_manager=None):
        super().__init__(parent)
        self.language_manager = language_manager
        self.parent_window = parent
        self.loaded_builder = None
        self.setWindowTitle("Strategy Templates")
        self.setModal(True)
        self.resize(600, 500)
        self.setup_ui()
    
    def setup_ui(self):
        """Setup UI."""
        layout = QVBoxLayout(self)
        
        layout.addWidget(QLabel("Strategy Templates"))
        layout.addWidget(QLabel("Select a template to load into the Strategy Builder:"))
        
        from ..builder.strategy_template import StrategyTemplate
        
        templates = StrategyTemplate.list_templates()
        
        self.templates_list = QListWidget()
        for template in templates:
            item = QListWidgetItem(template)
            self.templates_list.addItem(item)
        
        layout.addWidget(self.templates_list)
        
        # Template description
        self.description_text = QTextEdit()
        self.description_text.setReadOnly(True)
        self.description_text.setMaximumHeight(150)
        layout.addWidget(QLabel("Template Description:"))
        layout.addWidget(self.description_text)
        
        # Update description on selection
        self.templates_list.currentItemChanged.connect(self.update_description)
        self.templates_list.itemSelectionChanged.connect(self.update_description)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        load_btn = QPushButton("Load Template")
        load_btn.clicked.connect(lambda: self.load_template(None))
        button_layout.addWidget(load_btn)
        
        button_layout.addStretch()
        
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.close)
        button_layout.addWidget(close_btn)
        
        layout.addLayout(button_layout)
        
        # Set initial selection and description
        if templates:
            self.templates_list.setCurrentRow(0)
            # Ensure item is selected
            first_item = self.templates_list.item(0)
            if first_item:
                first_item.setSelected(True)
            self.update_description()
    
    def update_description(self):
        """Update template description."""
        current_item = self.templates_list.currentItem()
        if not current_item:
            return
        
        template_name = current_item.text()
        descriptions = {
            "SMA Crossover": "Simple Moving Average Crossover strategy. Generates buy signals when fast SMA crosses above slow SMA, and sell signals when it crosses below.",
            "RSI Reversion": "RSI-based mean reversion strategy. Buys when RSI is oversold (<30) and sells when overbought (>70).",
            "Breakout ATR": "ATR-based breakout strategy. Enters trades when price breaks above/below recent high/low with ATR-based stop loss and take profit."
        }
        
        description = descriptions.get(template_name, "No description available.")
        self.description_text.setPlainText(description)
    
    def load_template(self, item=None):
        """Load template."""
        if item is None:
            item = self.templates_list.currentItem()
            # Fallback: try to get item by current row if currentItem() returns None
            if not item:
                current_row = self.templates_list.currentRow()
                if current_row >= 0:
                    item = self.templates_list.item(current_row)
        
        if not item:
            QMessageBox.warning(self, "Warning", "Please select a template.")
            return
        
        template_name = item.text()
        
        try:
            from ..builder.strategy_template import StrategyTemplate
            
            # Map display names
            template_map = {
                "SMA Crossover": "SMA Crossover",
                "RSI Reversion": "RSI Mean Reversion",
                "Breakout ATR": "Breakout"
            }
            
            actual_name = template_map.get(template_name, template_name)
            builder = StrategyTemplate.get_template(actual_name)
            
            # Store builder for parent to access
            self.loaded_builder = builder
            
            # Get structure info
            structure = builder.get_strategy_structure()
            components_count = len(structure['components'])
            
            QMessageBox.information(self, "Template", 
                                  f"Loading template: {template_name}\n\n"
                                  f"Components: {components_count}\n"
                                  f"Opening Strategy Builder...")
            self.accept()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to load template: {e}")
