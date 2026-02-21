from PySide6.QtWidgets import QWidget, QMessageBox
from PySide6.QtCore import Signal, Qt
from .indicators_ui import Ui_IndicatorsTabMain
from .wallet_helpers import WalletErrorHelper
import json
import logging

logger = logging.getLogger(__name__)

class IndicatorsTabMain(QWidget):
    """Tab for configuring trading indicators and AI strategy parameters."""
    settings_changed = Signal(dict)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.ui = Ui_IndicatorsTabMain()
        self.ui.setupUi(self)
        self.ui.retranslateUi(self)
        
        # Initialize settings with default values
        self.default_settings = {
            # AI Strategy settings (special group)
            "AI_STRATEGY": {
                "RSI": {
                    "period": 14,
                    "buy_threshold": 30,
                    "sell_threshold": 70
                },
                "MACD": {
                    "low_threshold": 12,
                    "high_threshold": 26,
                    "period": 19
                },
                "MA_CROSS": {
                    "short_period": 9,
                    "long_period": 21
                },
                "BB": {
                    "period": 20,
                    "std_dev_multiplier": 2
                }
            },
            # Individual indicator settings
            "RSI": {
                "period": 14,
                "buy_threshold": 30,
                "sell_threshold": 70
            },
            "MACD": {
                "fast_period": 12,
                "slow_period": 26,
                "signal_period": 9
            },
            "MA_CROSS": {
                "short_period": 9,
                "long_period": 21
            },
            "BB": {
                "period": 20,
                "std_dev_multiplier": 2
            },
            "ML_ENABLED": False  # ML checkbox state
        }
        
        # Initialize current settings with default values
        self.current_settings = self.default_settings.copy()
        
        # Connect signals
        self.connect_signals()
        
        # Initialize UI with default values FIRST
        try:
            self.update_ui_from_settings()
        except Exception as e:
            logger.error(f"Failed to initialize UI with default settings: {e}")
            # This should never happen since we're using default settings
            raise Exception("Failed to initialize UI with default settings!")
        
        # Try to load settings from file
        try:
            self.load_default_settings()
            # Update UI after loading settings
            self.update_ui_from_settings()
        except Exception as e:
            logger.error(f"Failed to load settings from file: {e}")
            # If loading fails, use default settings
            self.save_default_settings(self.default_settings)
            logger.info("Using default settings instead")
            # Update UI with default settings again
            self.update_ui_from_settings()

    def connect_signals(self):
        """Connect UI signals to appropriate slots."""
        # AI Strategy fields are now read-only (no longer uses default settings)
        # Signals removed since fields are disabled
        
        # Disable AI Strategy input fields (AI uses ML, not configurable defaults)
        #self.ui.IndicatorsTabMainAIStrategyGroupBoxRSILowTextInput.setEnabled(False)
        #self.ui.IndicatorsTabMainAIStrategyGroupBoxRSIHighTextInput.setEnabled(False)
        #self.ui.IndicatorsTabMainAIStrategyGroupBoxRSIPeriodTextInput.setEnabled(False)
        #self.ui.IndicatorsTabMainAIStrategyGroupBoxMACDLowTextInput.setEnabled(False)
        #self.ui.IndicatorsTabMainAIStrategyGroupBoxMACDHighTextInput.setEnabled(False)
        #self.ui.IndicatorsTabMainAIStrategyGroupBoxMACDPeriodTextInput.setEnabled(False)
        #self.ui.IndicatorsTabMainAIStrategyGroupBoxMACrossShortTextInput.setEnabled(False)
        #self.ui.IndicatorsTabMainAIStrategyGroupBoxMACrossLongTextInput.setEnabled(False)
        #self.ui.IndicatorsTabMainAIStrategyGroupBoxBBPeriodTextInput.setEnabled(False)
        #self.ui.IndicatorsTabMainAIStrategyGroupBoxBBStdDevMultiplierTextInput.setEnabled(False)
        
        # Clear the text from disabled fields (clean slate for adding AI Strategy explanation)
        #self.ui.IndicatorsTabMainAIStrategyGroupBoxRSILowTextInput.clear()
        #self.ui.IndicatorsTabMainAIStrategyGroupBoxRSIHighTextInput.clear()
        #self.ui.IndicatorsTabMainAIStrategyGroupBoxRSIPeriodTextInput.clear()
        #self.ui.IndicatorsTabMainAIStrategyGroupBoxMACDLowTextInput.clear()
        #self.ui.IndicatorsTabMainAIStrategyGroupBoxMACDHighTextInput.clear()
        #self.ui.IndicatorsTabMainAIStrategyGroupBoxMACDPeriodTextInput.clear()
        #self.ui.IndicatorsTabMainAIStrategyGroupBoxMACrossShortTextInput.clear()
        #self.ui.IndicatorsTabMainAIStrategyGroupBoxMACrossLongTextInput.clear()
        #self.ui.IndicatorsTabMainAIStrategyGroupBoxBBPeriodTextInput.clear()
        #self.ui.IndicatorsTabMainAIStrategyGroupBoxBBStdDevMultiplierTextInput.clear()
        
        # Disable and check ML checkbox (AI Strategy always uses ML)
        #self.ui.IndicatorsTabMainAIStrategyGroupBoxEnableMLCheckBox.setEnabled(False)
        #self.ui.IndicatorsTabMainAIStrategyGroupBoxEnableMLCheckBox.setChecked(True)

    def load_default_settings(self):
        """Load and initialize default indicator settings."""
        try:
            with open('config/indicator_defaults.json', 'r') as f:
                loaded_settings = json.load(f)
                
                # Initialize with our default structure
                settings = self.default_settings.copy()
                
                # Update settings from loaded file where they match
                for key in loaded_settings:
                    if key == "RSI":
                        settings["RSI"] = {
                            "period": loaded_settings["RSI"].get("period", 14),
                            "buy_threshold": loaded_settings["RSI"].get("buy_threshold", 30),
                            "sell_threshold": loaded_settings["RSI"].get("sell_threshold", 70)
                        }
                        settings["AI_STRATEGY"]["RSI"] = {
                            "period": loaded_settings["RSI"].get("period", 14),
                            "buy_threshold": loaded_settings["RSI"].get("buy_threshold", 30),
                            "sell_threshold": loaded_settings["RSI"].get("sell_threshold", 70)
                        }
                    elif key == "MACD":
                        settings["MACD"] = {
                            "fast_period": loaded_settings["MACD"].get("fast_period", 12),
                            "slow_period": loaded_settings["MACD"].get("slow_period", 26),
                            "signal_period": loaded_settings["MACD"].get("signal_period", 9)
                        }
                        settings["AI_STRATEGY"]["MACD"] = {
                            "low_threshold": loaded_settings["MACD"].get("low_threshold", 12),
                            "high_threshold": loaded_settings["MACD"].get("high_threshold", 26),
                            "period": loaded_settings["MACD"].get("period", loaded_settings["MACD"].get("fast_period", 12))
                        }
                    elif key == "MA_CROSS":
                        settings["MA_CROSS"] = {
                            "short_period": loaded_settings["MA_CROSS"].get("short_period", 9),
                            "long_period": loaded_settings["MA_CROSS"].get("long_period", 21)
                        }
                        settings["AI_STRATEGY"]["MA_CROSS"] = {
                            "short_period": loaded_settings["MA_CROSS"].get("short_period", 9),
                            "long_period": loaded_settings["MA_CROSS"].get("long_period", 21)
                        }
                    elif key == "BB":
                        settings["BB"] = {
                            "period": loaded_settings["BB"].get("period", 20),
                            "std_dev_multiplier": loaded_settings["BB"].get("std_dev_multiplier", 2)
                        }
                        settings["AI_STRATEGY"]["BB"] = {
                            "period": loaded_settings["BB"].get("period", 20),
                            "std_dev_multiplier": loaded_settings["BB"].get("std_dev_multiplier", 2)
                        }
                
                # Validate required keys
                required_keys = ['RSI', 'MACD', 'MA_CROSS', 'BB']
                if all(key in settings for key in required_keys):
                    self.default_settings = settings
                    self.current_settings = settings.copy()
                    logger.info("Successfully loaded and updated settings")
                else:
                    logger.error("Loaded settings are missing required keys")
                    raise ValueError("Settings file is missing required keys")
        except Exception as e:
            logger.error(f"Failed to load default indicator settings: {e}")
            # If loading fails, use the default settings we initialized in __init__
            self.save_default_settings(self.default_settings)
            logger.info("Using default settings instead")

    def update_ui_from_settings(self):
        """Update UI elements with current settings."""
        try:
            # First ensure we have the basic structure
            if "AI_STRATEGY" not in self.current_settings:
                logger.warning("AI_STRATEGY not found in settings, using default")
                self.current_settings["AI_STRATEGY"] = {
                    "RSI": {
                        "period": 14,
                        "buy_threshold": 30,
                        "sell_threshold": 70
                    },
                    "MACD": {
                        "low_threshold": 12,
                        "high_threshold": 26,
                        "period": 12
                    },
                    "MA_CROSS": {
                        "short_period": 9,
                        "long_period": 21
                    },
                    "BB": {
                        "period": 20,
                        "std_dev_multiplier": 2
                    }
                }
            
            # AI Strategy Group - Fields are now DISABLED and cleared
            # AI Strategy uses ML and doesn't use these configurable defaults
            # Space reserved for adding AI Strategy explanation text
            # Fields remain empty (cleared in connect_signals)
            
            # ML Enable Checkbox - Always enabled for AI Strategy (disabled checkbox, always checked)
            #self.ui.IndicatorsTabMainAIStrategyGroupBoxEnableMLCheckBox.setChecked(True)
            
            # Individual Indicator Groups
            # RSI
            if "RSI" in self.current_settings:
                rsi_settings = self.current_settings["RSI"]
                self.ui.IndicatorsTabMainRSIGroupBoxLowValueTextInput.setText(str(rsi_settings.get("buy_threshold", 30)))
                self.ui.IndicatorsTabMainRSIGroupBoxHighValueTextInput.setText(str(rsi_settings.get("sell_threshold", 70)))
                self.ui.IndicatorsTabMainRSIGroupBoxPeriodTextInput.setText(str(rsi_settings.get("period", 14)))
            
            # MA Cross
            if "MA_CROSS" in self.current_settings:
                macross_settings = self.current_settings["MA_CROSS"]
                self.ui.IndicatorsTabMainMACrossGroupBoxShortTimeTextInput.setText(str(macross_settings.get("short_period", 9)))
                self.ui.IndicatorsTabMainMACrossGroupBoxLongTimeTextInput.setText(str(macross_settings.get("long_period", 21)))
            
            # Bollinger Bands
            if "BB" in self.current_settings:
                bb_settings = self.current_settings["BB"]
                self.ui.IndicatorsTabMainBBGroupBoxBBPeriodTextInput.setText(str(int(bb_settings.get("period", 20))))
                self.ui.IndicatorsTabMainBBGroupBoxBBStdDevMultiplierTextInput.setText(str(int(bb_settings.get("std_dev_multiplier", 2))))
            
            # MACD
            if "MACD" in self.current_settings:
                macd_settings = self.current_settings["MACD"]
                self.ui.IndicatorsTabMainMACDGroupBoxMACDLowTextInput.setText(str(macd_settings.get("fast_period", 12)))
                self.ui.IndicatorsTabMainMACDGroupBoxMACDHighTextInput.setText(str(macd_settings.get("slow_period", 26)))
                self.ui.IndicatorsTabMainMACDGroupBoxMACDPeriodTextInput.setText(str(macd_settings.get("signal_period", 9)))
            
        except Exception as e:
            logger.error(f"Error updating UI: {e}")
            logger.error(f"Current settings: {self.current_settings}")
            WalletErrorHelper.show_message(self, f"Error updating UI: {str(e)}")

    def on_settings_changed(self):
        """Handle changes to indicator settings."""
        try:
            # First ensure we have the basic structure
            if "AI_STRATEGY" not in self.current_settings:
                self.current_settings["AI_STRATEGY"] = {
                    "RSI": {"period": 14, "buy_threshold": 30, "sell_threshold": 70},
                    "MACD": {"low_threshold": 12, "high_threshold": 26, "period": 9},
                    "MA_CROSS": {"short_period": 9, "long_period": 21},
                    "BB": {"period": 20, "std_dev_multiplier": 2}
                }
            
            # AI Strategy fields are now disabled/read-only (AI uses ML, not configurable defaults)
            # Settings are not read from these fields anymore
            # ML is always enabled for AI Strategy
            self.current_settings["ML_ENABLED"] = True
            
            # Individual Indicator Groups
            # RSI
            if "RSI" not in self.current_settings:
                self.current_settings["RSI"] = {
                    "period": 14,
                    "buy_threshold": 30,
                    "sell_threshold": 70
                }
            else:
                # Ensure all RSI values exist with defaults
                self.current_settings["RSI"] = {
                    "period": self.current_settings["RSI"].get("period", 14),
                    "buy_threshold": self.current_settings["RSI"].get("buy_threshold", 30),
                    "sell_threshold": self.current_settings["RSI"].get("sell_threshold", 70)
                }
            if self.ui.IndicatorsTabMainRSIGroupBoxLowValueTextInput.text().isdigit():
                self.current_settings["RSI"]["buy_threshold"] = int(self.ui.IndicatorsTabMainRSIGroupBoxLowValueTextInput.text())
            if self.ui.IndicatorsTabMainRSIGroupBoxHighValueTextInput.text().isdigit():
                self.current_settings["RSI"]["sell_threshold"] = int(self.ui.IndicatorsTabMainRSIGroupBoxHighValueTextInput.text())
            if self.ui.IndicatorsTabMainRSIGroupBoxPeriodTextInput.text().isdigit():
                self.current_settings["RSI"]["period"] = int(self.ui.IndicatorsTabMainRSIGroupBoxPeriodTextInput.text())
            
            # MA Cross
            if "MA_CROSS" not in self.current_settings:
                self.current_settings["MA_CROSS"] = {
                    "short_period": 9,
                    "long_period": 21
                }
            else:
                # Ensure all MA_CROSS values exist with defaults
                self.current_settings["MA_CROSS"] = {
                    "short_period": self.current_settings["MA_CROSS"].get("short_period", 9),
                    "long_period": self.current_settings["MA_CROSS"].get("long_period", 21)
                }
            if self.ui.IndicatorsTabMainMACrossGroupBoxShortTimeTextInput.text().isdigit():
                self.current_settings["MA_CROSS"]["short_period"] = int(self.ui.IndicatorsTabMainMACrossGroupBoxShortTimeTextInput.text())
            if self.ui.IndicatorsTabMainMACrossGroupBoxLongTimeTextInput.text().isdigit():
                self.current_settings["MA_CROSS"]["long_period"] = int(self.ui.IndicatorsTabMainMACrossGroupBoxLongTimeTextInput.text())
            
            # Bollinger Bands
            if "BB" not in self.current_settings:
                self.current_settings["BB"] = {
                    "period": 20,
                    "std_dev_multiplier": 2
                }
            else:
                # Ensure all BB values exist with defaults
                self.current_settings["BB"] = {
                    "period": self.current_settings["BB"].get("period", 20),
                    "std_dev_multiplier": self.current_settings["BB"].get("std_dev_multiplier", 2)
                }
            if self.ui.IndicatorsTabMainBBGroupBoxBBPeriodTextInput.text().isdigit():
                self.current_settings["BB"]["period"] = int(self.ui.IndicatorsTabMainBBGroupBoxBBPeriodTextInput.text())
            if self.ui.IndicatorsTabMainBBGroupBoxBBStdDevMultiplierTextInput.text().replace('.', '', 1).isdigit():
                self.current_settings["BB"]["std_dev_multiplier"] = float(self.ui.IndicatorsTabMainBBGroupBoxBBStdDevMultiplierTextInput.text())
            
            # MACD
            if "MACD" not in self.current_settings:
                self.current_settings["MACD"] = {"fast_period": 12, "slow_period": 26, "signal_period": 9}
            if self.ui.IndicatorsTabMainMACDGroupBoxMACDLowTextInput.text().isdigit():
                self.current_settings["MACD"]["fast_period"] = int(self.ui.IndicatorsTabMainMACDGroupBoxMACDLowTextInput.text())
            if self.ui.IndicatorsTabMainMACDGroupBoxMACDHighTextInput.text().isdigit():
                self.current_settings["MACD"]["slow_period"] = int(self.ui.IndicatorsTabMainMACDGroupBoxMACDHighTextInput.text())
            if self.ui.IndicatorsTabMainMACDGroupBoxMACDPeriodTextInput.text().isdigit():
                self.current_settings["MACD"]["signal_period"] = int(self.ui.IndicatorsTabMainMACDGroupBoxMACDPeriodTextInput.text())
            
            # Emit settings changed signal
            self.settings_changed.emit(self.current_settings)
            
        except Exception as e:
            logger.error(f"Failed to update settings: {e}")
            logger.error(f"Current settings: {self.current_settings}")
            WalletErrorHelper.show_message(self, f"Error updating settings: {str(e)}")
            # Reset to default settings on error
            self.current_settings = self.default_settings.copy()
            self.update_ui_from_settings()

    def validate_settings(self) -> bool:
        """Validate that all settings are valid numbers."""
        try:
            # RSI Settings
            float(self.current_settings["rsi"]["low"])
            float(self.current_settings["rsi"]["high"])
            int(self.current_settings["rsi"]["period"])
            
            # MACD Settings
            float(self.current_settings["macd"]["low"])
            float(self.current_settings["macd"]["high"])
            int(self.current_settings["macd"]["period"])
            
            # Moving Average Cross Settings
            int(self.current_settings["ma_cross"]["short_period"])
            int(self.current_settings["ma_cross"]["long_period"])
            
            # Bollinger Bands Settings
            int(self.current_settings["bb"]["period"])
            float(self.current_settings["bb"]["std_dev_multiplier"])
            
            return True
            
        except ValueError:
            WalletErrorHelper.show_message(self, "Please enter valid numbers for all settings")
            return False
            
    def reset_to_defaults(self):
        """Reset all settings to their default values."""
        self.current_settings = self.default_settings.copy()
        self.update_ui_from_settings()
        self.settings_changed.emit(self.current_settings)

    def save_default_settings(self, settings: dict):
        """Save default indicator settings to indicator_defaults.json."""
        try:
            with open('config/indicator_defaults.json', 'w') as f:
                json.dump(settings, f, indent=4)
            WalletErrorHelper.show_message(self, "Default indicator settings saved successfully")
        except Exception as e:
            logger.error(f"Failed to save default settings: {e}")
            WalletErrorHelper.show_message(self, f"Failed to save default settings: {str(e)}")

    def save_settings(self, file_path: str):
        """Save current settings to a file (for individual trade)."""
        try:
            with open(file_path, 'w') as f:
                json.dump(self.current_settings, f, indent=4)
            WalletErrorHelper.show_message(self, f"Trade settings saved to {file_path}")
        except Exception as e:
            logger.error(f"Failed to save trade settings: {e}")
            WalletErrorHelper.show_message(self, f"Failed to save trade settings: {str(e)}")

    def load_trade_settings(self, file_path: str):
        """Load settings from a file (for individual trade)."""
        try:
            with open(file_path, 'r') as f:
                new_settings = json.load(f)
                self.current_settings = new_settings
                self.update_ui_from_settings()
                self.settings_changed.emit(self.current_settings)
            WalletErrorHelper.show_message(self, f"Trade settings loaded from {file_path}")
        except Exception as e:
            logger.error(f"Failed to load trade settings: {e}")
            WalletErrorHelper.show_message(self, f"Failed to load trade settings: {str(e)}")

    def apply_to_defaults(self):
        """Apply current settings to default settings."""
        try:
            self.save_default_settings(self.current_settings)
            self.default_settings = self.current_settings.copy()
            WalletErrorHelper.show_message(self, "Settings applied to default settings")
        except Exception as e:
            logger.error(f"Failed to apply to defaults: {e}")
            WalletErrorHelper.show_message(self, f"Failed to apply to defaults: {str(e)}")

    def load_default_settings(self):
        """Load settings from indicator_defaults.json."""
        try:
            with open('config/indicator_defaults.json', 'r') as f:
                new_settings = json.load(f)
                
                # Validate the loaded settings structure
                required_keys = ['AI_STRATEGY', 'RSI', 'MACD', 'MA_CROSS', 'BB', 'ML_ENABLED']
                if not all(key in new_settings for key in required_keys):
                    logger.error("Settings file is missing required keys")
                    raise ValueError("Settings file is missing required keys")
                    
                # Validate AI_STRATEGY structure
                ai_strategy_keys = ['RSI', 'MACD', 'MA_CROSS', 'BB']
                if not all(key in new_settings['AI_STRATEGY'] for key in ai_strategy_keys):
                    logger.error("AI_STRATEGY is missing required indicators")
                    raise ValueError("AI_STRATEGY is missing required indicators")
                    
                self.default_settings = new_settings
                self.current_settings = new_settings.copy()
                self.update_ui_from_settings()
                self.settings_changed.emit(self.current_settings)
        except Exception as e:
            logger.error(f"Failed to load default settings: {e}")
            # If loading fails, use our default settings
            default_settings = {
                "AI_STRATEGY": {
                    "RSI": {"period": 14, "buy_threshold": 30, "sell_threshold": 70},
                    "MACD": {"low_threshold": -0.5, "high_threshold": 0.5, "period": 12},
                    "MA_CROSS": {"short_period": 9, "long_period": 21},
                    "BB": {"period": 20, "std_dev_multiplier": 2}
                },
                "RSI": {"period": 14, "buy_threshold": 30, "sell_threshold": 70},
                "MACD": {"fast_period": 12, "slow_period": 26, "signal_period": 9},
                "MA_CROSS": {"short_period": 9, "long_period": 21},
                "BB": {"period": 20, "std_dev_multiplier": 2},
                "ML_ENABLED": False
            }
            self.default_settings = default_settings
            self.current_settings = default_settings.copy()
            self.update_ui_from_settings()
            self.settings_changed.emit(self.current_settings)
            logger.info("Using default settings instead")