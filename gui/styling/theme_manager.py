"""
Theme Manager for RADbot
Centralized theme management system for easy theme switching
"""
import os
from typing import Dict
from utils.path_utils import get_absolute_path

class ThemeManager:
    """Manages application themes and provides theme switching capabilities"""
    
    # Theme color definitions
    THEMES = {
        'dark': {
            'name': 'Dark Theme',
            'file': 'dark_theme.qss',
            'colors': {
                'background_primary': '#0f172a',
                'background_secondary': '#0a0e27',
                'border': '#1e293b',
                'text_primary': '#ffffff',
                'text_secondary': '#94a3b8',
                'accent_blue': '#0D6EFD',
                'accent_cyan': '#00D4FF',
                'success': '#4CAF50',
                'error': '#F44336',
                'warning': '#FF9800'
            }
        },
        'light': {
            'name': 'Light Theme',
            'file': 'light_theme.qss',  # To be created
            'colors': {
                'background_primary': '#ffffff',
                'background_secondary': '#f8fafc',
                'border': '#e2e8f0',
                'text_primary': '#0f172a',
                'text_secondary': '#64748b',
                'accent_blue': '#0D6EFD',
                'accent_cyan': '#00D4FF',
                'success': '#4CAF50',
                'error': '#F44336',
                'warning': '#FF9800'
            }
        }
    }
    
    def __init__(self):
        self.current_theme = 'dark'
        self.theme_path = get_absolute_path('gui/styling')
    
    def get_theme_stylesheet(self, theme_name: str = None) -> str:
        """
        Load and return the QSS stylesheet for the specified theme
        
        Args:
            theme_name: Name of the theme ('dark' or 'light'). Uses current if None.
            
        Returns:
            str: The QSS stylesheet content
        """
        if theme_name is None:
            theme_name = self.current_theme
            
        if theme_name not in self.THEMES:
            theme_name = 'dark'  # Fallback to dark
            
        theme_file = self.THEMES[theme_name]['file']
        theme_file_path = os.path.join(self.theme_path, theme_file)
        
        try:
            with open(theme_file_path, 'r', encoding='utf-8') as f:
                return f.read()
        except FileNotFoundError:
            print(f"Warning: Theme file not found: {theme_file_path}")
            return ""
        except Exception as e:
            print(f"Error loading theme: {e}")
            return ""
    
    def get_theme_color(self, color_key: str, theme_name: str = None) -> str:
        """
        Get a specific color from the theme palette
        
        Args:
            color_key: Key for the color (e.g., 'background_primary')
            theme_name: Name of the theme. Uses current if None.
            
        Returns:
            str: Hex color code
        """
        if theme_name is None:
            theme_name = self.current_theme
            
        if theme_name not in self.THEMES:
            theme_name = 'dark'
            
        return self.THEMES[theme_name]['colors'].get(color_key, '#000000')
    
    def set_theme(self, theme_name: str) -> bool:
        """
        Set the current active theme
        
        Args:
            theme_name: Name of the theme to activate
            
        Returns:
            bool: True if successful, False otherwise
        """
        if theme_name in self.THEMES:
            self.current_theme = theme_name
            return True
        return False
    
    def get_available_themes(self) -> Dict[str, str]:
        """Get list of available themes"""
        return {key: val['name'] for key, val in self.THEMES.items()}
    
    def get_current_theme(self) -> str:
        """Get the name of the current theme"""
        return self.current_theme

# Global theme manager instance
_theme_manager = None

def get_theme_manager() -> ThemeManager:
    """Get or create the global theme manager instance"""
    global _theme_manager
    if _theme_manager is None:
        _theme_manager = ThemeManager()
    return _theme_manager
