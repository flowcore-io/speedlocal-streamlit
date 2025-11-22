"""
Central registry for all app modules.
"""

from typing import Dict
from modules.base_module import BaseModule
from modules.key_insights.module import KeyInsightsModule
from modules.energy_emissions.module import EnergyEmissionsModule
from modules.energy_emissions_v2.module import EnergyEmissionsModuleV2
from modules.energy_map.module import EnergyMapModule


from modules.development.module import DevelopmentModule

class ModuleRegistry:
    """Central registry for all app modules."""
    
    def __init__(self):
        """Initialize module registry."""
        self._modules: Dict[str, BaseModule] = {}
        self._register_default_modules()
    
    def _register_default_modules(self) -> None:
        """Register all default modules."""
        # Register Key Insights module first (order=0)
        self.register_module("key_insights", KeyInsightsModule())
        
        # # Register Energy/Emissions module (order=1)
        # self.register_module("energy_emissions", EnergyEmissionsModule())
        
        # Register Energy/Emissions module (order=1)
        self.register_module("energy_emissions_v2", EnergyEmissionsModuleV2())

        self.register_module("energy_map", EnergyMapModule())

        # Future modules can be added here:
        # self.register_module("land_use", LandUseModule())
        # self.register_module("economics", EconomicsModule())
        # self.register_module("daynite", DayNiteModule())

        # Register Development module (order=999 = always last)
        
        self.register_module("development", DevelopmentModule())

    def register_module(self, key: str, module: BaseModule) -> None:
        """
        Register a new module.
        
        Args:
            key: Unique identifier for the module
            module: Module instance
        """
        self._modules[key] = module
    
    def get_module(self, key: str) -> BaseModule:
        """
        Get a registered module.
        
        Args:
            key: Module identifier
            
        Returns:
            Module instance
            
        Raises:
            KeyError: If module not found
        """
        if key not in self._modules:
            raise KeyError(f"Module '{key}' not found in registry.")
        return self._modules[key]
    
    def get_all_modules(self) -> Dict[str, BaseModule]:
        """Get all registered modules sorted by order."""
        sorted_modules = sorted(
            self._modules.items(),
            key=lambda x: x[1].order
        )
        return dict(sorted_modules)
    
    def get_enabled_modules(self) -> Dict[str, BaseModule]:
        """Get only enabled modules sorted by order."""
        enabled = {
            key: module 
            for key, module in self._modules.items() 
            if module.enabled
        }
        sorted_modules = sorted(
            enabled.items(),
            key=lambda x: x[1].order
        )
        return dict(sorted_modules)
    
    def get_module_names(self) -> list:
        """Get list of module names for display."""
        return [module.name for module in self.get_enabled_modules().values()]
    
    def enable_module(self, key: str) -> None:
        """Enable a module."""
        if key in self._modules:
            self._modules[key].enabled = True
    
    def disable_module(self, key: str) -> None:
        """Disable a module."""
        if key in self._modules:
            self._modules[key].enabled = False
