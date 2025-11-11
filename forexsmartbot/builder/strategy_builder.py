"""Visual strategy builder with drag-and-drop interface (framework)."""

from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field
from enum import Enum


class ComponentType(Enum):
    """Types of strategy components."""
    INDICATOR = "indicator"
    SIGNAL = "signal"
    FILTER = "filter"
    RISK_MANAGEMENT = "risk_management"
    EXIT_CONDITION = "exit_condition"


@dataclass
class StrategyComponent:
    """Represents a component in a strategy."""
    component_id: str
    component_type: ComponentType
    name: str
    parameters: Dict[str, Any] = field(default_factory=dict)
    connections: List[str] = field(default_factory=list)  # IDs of connected components


class StrategyBuilder:
    """Framework for building custom strategies visually."""
    
    def __init__(self):
        self.components: Dict[str, StrategyComponent] = {}
        self.component_counter = 0
        
    def add_component(self, component_type: ComponentType, name: str, 
                     parameters: Optional[Dict[str, Any]] = None) -> str:
        """Add a component to the strategy."""
        component_id = f"comp_{self.component_counter}"
        self.component_counter += 1
        
        component = StrategyComponent(
            component_id=component_id,
            component_type=component_type,
            name=name,
            parameters=parameters or {}
        )
        
        self.components[component_id] = component
        return component_id
        
    def connect_components(self, source_id: str, target_id: str) -> bool:
        """Connect two components."""
        if source_id not in self.components or target_id not in self.components:
            return False
            
        if target_id not in self.components[source_id].connections:
            self.components[source_id].connections.append(target_id)
        return True
        
    def remove_component(self, component_id: str) -> bool:
        """Remove a component from the strategy."""
        if component_id not in self.components:
            return False
            
        # Remove connections
        for comp in self.components.values():
            if component_id in comp.connections:
                comp.connections.remove(component_id)
                
        del self.components[component_id]
        return True
        
    def update_component_params(self, component_id: str, parameters: Dict[str, Any]) -> bool:
        """Update component parameters."""
        if component_id not in self.components:
            return False
            
        self.components[component_id].parameters.update(parameters)
        return True
        
    def get_strategy_structure(self) -> Dict[str, Any]:
        """Get the current strategy structure."""
        return {
            'components': {
                comp_id: {
                    'type': comp.component_type.value,
                    'name': comp.name,
                    'parameters': comp.parameters,
                    'connections': comp.connections
                }
                for comp_id, comp in self.components.items()
            }
        }
        
    def validate_strategy(self) -> tuple[bool, List[str]]:
        """Validate the strategy structure."""
        errors = []
        
        # Check for at least one signal component
        has_signal = any(
            comp.component_type == ComponentType.SIGNAL 
            for comp in self.components.values()
        )
        
        if not has_signal:
            errors.append("Strategy must have at least one signal component")
            
        # Check for valid connections
        for comp_id, comp in self.components.items():
            for conn_id in comp.connections:
                if conn_id not in self.components:
                    errors.append(f"Component {comp_id} references non-existent component {conn_id}")
                    
        return len(errors) == 0, errors
        
    def clear(self):
        """Clear all components."""
        self.components.clear()
        self.component_counter = 0

