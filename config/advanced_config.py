import json
import os
from typing import Dict, Any

class AdvancedConfig:
    def __init__(self, config_path: str = None):
        """Load advanced configuration settings"""
        if config_path is None:
            config_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'config', 'advanced_config.json')
        
        self.config_path = config_path
        self._config = self._load_config()
        
    def _load_config(self) -> Dict[str, Any]:
        """Load and validate configuration file (supports // comments)"""
        try:
            with open(self.config_path, 'r') as f:
                # Read the file and strip // comments
                content = f.read()
                # Remove single-line comments (// comment)
                import re
                # Remove // comments but preserve URLs with //
                content = re.sub(r'(?<!:)//[^\n]*', '', content)
                config = json.loads(content)
            return config
        except Exception as e:
            print(f"Error loading advanced config: {e}")
            return {}
            
    def get(self, section: str, key: str, default: Any = None) -> Any:
        """Get a configuration value with fallback to default"""
        try:
            return self._config.get(section, {}).get(key, default)
        except Exception:
            return default
            
    def update(self, section: str, key: str, value: Any) -> None:
        """Update a configuration value"""
        try:
            if section not in self._config:
                self._config[section] = {}
            self._config[section][key] = value
            self._save_config()
        except Exception as e:
            print(f"Error updating config: {e}")
            
    def _save_config(self) -> None:
        """Save configuration to file"""
        try:
            with open(self.config_path, 'w') as f:
                json.dump(self._config, f, indent=4)
        except Exception as e:
            print(f"Error saving config: {e}")
