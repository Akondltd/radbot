import logging
import json
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QLineEdit, QDoubleSpinBox,
    QSpinBox, QGroupBox, QFormLayout, QCheckBox
)

logger = logging.getLogger(__name__)

# Defines the parameter structure for each strategy to dynamically build UI forms.
STRATEGY_PARAMS = {
    "RSI": {
        "rsi_period": {"type": "int", "default": 14, "label": "RSI Period"},
        "buy_threshold": {"type": "float", "default": 30.0, "label": "Buy Threshold"},
        "sell_threshold": {"type": "float", "default": 70.0, "label": "Sell Threshold"},
    },
    "MACD": {
        "fast_period": {"type": "int", "default": 12, "label": "Fast Period"},
        "slow_period": {"type": "int", "default": 26, "label": "Slow Period"},
        "signal_period": {"type": "int", "default": 9, "label": "Signal Period"},
    },
    "Bollinger Bands": {
        "period": {"type": "int", "default": 20, "label": "Period"},
        "std_dev_multiplier": {"type": "float", "default": 2.0, "label": "Std. Dev. Multiplier"},
    },
    "Moving Average Crossover": {
        "short_period": {"type": "int", "default": 20, "label": "Short Period"},
        "long_period": {"type": "int", "default": 50, "label": "Long Period"},
    },
    "Ping Pong": {
        "buy_price": {"type": "float", "default": 0.0, "label": "Buy Price"},
        "sell_price": {"type": "float", "default": 0.0, "label": "Sell Price"},
    },
    "AI Strategy": {
        "smoothing_period": {"type": "int", "default": 5, "label": "Smoothing Period"},
        "weights": {
            "type": "nested",
            "label": "Indicator Weights",
            "params": {
                "rsi": {"type": "float", "default": 1.0, "label": "RSI Weight"},
                "macd": {"type": "float", "default": 1.0, "label": "MACD Weight"},
                "bb": {"type": "float", "default": 1.0, "label": "Bollinger Bands Weight"},
                "mac": {"type": "float", "default": 1.0, "label": "MA Crossover Weight"},
            }
        },
    }
}

class StrategyFormManager:
    """Dynamically creates and manages UI forms for strategy parameters."""
    def __init__(self, parent_layout):
        self.parent_layout = parent_layout
        self.widgets = {}

    def clear_form(self):
        """Removes all widgets from the parent layout."""
        while self.parent_layout.count():
            child = self.parent_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
        self.widgets = {}

    def create_form_widgets(self, strategy_name, settings_json):
        """Creates and populates form widgets based on strategy and current settings."""
        self.clear_form()
        params_config = STRATEGY_PARAMS.get(strategy_name, {})
        if not params_config:
            logger.warning(f"No parameter configuration found for strategy: {strategy_name}")
            self.parent_layout.addWidget(QLabel(f"No editable parameters for {strategy_name}."))
            return

        try:
            current_settings = json.loads(settings_json) if settings_json and settings_json.strip() else {}
        except json.JSONDecodeError:
            logger.error(f"Invalid JSON in indicator_settings_json for {strategy_name}: {settings_json}")
            current_settings = {}

        self.widgets = self._create_widgets_recursive(params_config, current_settings, self.parent_layout)

    def _create_widgets_recursive(self, config, current_values, layout):
        widgets_map = {}
        form_layout = QFormLayout()

        for key, spec in config.items():
            value = current_values.get(key, spec.get('default'))
            label_text = spec.get('label', key.replace('_', ' ').title())

            if spec['type'] == 'nested':
                group_box = QGroupBox(label_text)
                nested_layout = QVBoxLayout()
                group_box.setLayout(nested_layout)
                widgets_map[key] = self._create_widgets_recursive(spec['params'], value, nested_layout)
                layout.addWidget(group_box)
            else:
                widget = self._create_input_widget(spec, value)
                form_layout.addRow(QLabel(label_text), widget)
                widgets_map[key] = widget
        
        if form_layout.rowCount() > 0:
            container = QWidget()
            container.setLayout(form_layout)
            layout.addWidget(container)
        
        return widgets_map

    def _create_input_widget(self, spec, value):
        widget_type = spec['type']
        default_value = spec.get('default')
        current_value = value if value is not None else default_value

        if widget_type == 'int':
            widget = QSpinBox()
            widget.setRange(-10000, 10000)
            widget.setValue(int(current_value))
        elif widget_type == 'float':
            widget = QDoubleSpinBox()
            widget.setRange(-1000000.0, 1000000.0)
            widget.setDecimals(8)
            widget.setValue(float(current_value))
        else:
            widget = QLineEdit()
            widget.setText(str(current_value))
        return widget

    def get_form_data(self, strategy_name):
        """Extracts the current values from the form widgets into a dictionary."""
        params_config = STRATEGY_PARAMS.get(strategy_name, {})
        return self._get_data_recursive(params_config, self.widgets)

    def _get_data_recursive(self, config, widgets):
        data = {}
        for key, spec in config.items():
            widget = widgets.get(key)
            if not widget:
                continue

            if spec['type'] == 'nested':
                data[key] = self._get_data_recursive(spec['params'], widget)
            elif isinstance(widget, (QSpinBox, QDoubleSpinBox)):
                data[key] = widget.value()
            elif isinstance(widget, QLineEdit):
                try:
                    if spec['type'] == 'int':
                        data[key] = int(widget.text())
                    elif spec['type'] == 'float':
                        data[key] = float(widget.text())
                    else:
                        data[key] = widget.text()
                except (ValueError, TypeError):
                    data[key] = widget.text()
        return data