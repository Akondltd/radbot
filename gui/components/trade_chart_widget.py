import pandas as pd
import logging
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QSizePolicy
from PySide6.QtCore import Signal, Qt
from PySide6.QtGui import QPalette, QColor, QPainter

# --- Matplotlib Imports ---
from matplotlib.figure import Figure
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
import mplfinance as mpf


class ThemedFigureCanvas(FigureCanvas):
    """FigureCanvas that pre-fills its background before matplotlib renders,
    guaranteeing no DPI-rounding gaps on any edge."""

    _bg_color = QColor('#0f172a')

    def paintEvent(self, event):
        # Paint the full widget background FIRST so that any pixel the
        # Agg buffer does not cover (typically a 1px strip on the right
        # or bottom caused by Windows DPI rounding) shows the correct
        # theme colour instead of stale artefacts.
        painter = QPainter(self)
        painter.fillRect(self.rect(), self._bg_color)
        painter.end()
        # Now let matplotlib draw the Agg buffer on top.
        super().paintEvent(event)

# --- Matplotlib Style ---
# Theme colors matching dark_theme.qss
mpf_style = {
    "marketcolors": {
        "candle": {"up": "#4CAF50", "down": "#F44336"},
        "edge": {"up": "#4CAF50", "down": "#F44336"},
        "vcedge": {"up": "#4CAF50", "down": "#F44336"},
        "wick": {"up": "#4CAF50", "down": "#F44336"},
        "ohlc": {"up": "#4CAF50", "down": "#F44336"},
        "volume": {"up": "#4CAF50", "down": "#F44336"},
        "alpha": 1.0,
        "vcdopcod": False,
    },
    "mavcolors": ("#0D6EFD", "#00D4FF", "#4CAF50"),
    "y_on_right": False,
    "facecolor": "#0f172a",  # Theme chart background
    "gridcolor": "#334155",
    "figcolor": "#0f172a",  # Theme chart background
}

# Setup logger
logger = logging.getLogger(__name__)

class TradeChartWidget(QWidget):
    """A widget for displaying trade data using Matplotlib"""
    
    # Signal emitted when timeframe changes
    timeframe_changed = Signal(str)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(0)
        
        # Ensure this widget itself paints the theme background so no
        # parent bleed-through appears in the button/stretch area.
        self.setAutoFillBackground(True)
        pal = self.palette()
        pal.setColor(QPalette.ColorRole.Window, QColor('#0f172a'))
        self.setPalette(pal)
        
        # Current timeframe and data
        self.current_timeframe = "10m"
        self.full_dataframe = None
        self.current_strategy = ""
        
        # --- Matplotlib Canvas Setup ---
        self.figure = Figure(figsize=(5, 4), dpi=100, facecolor='#0f172a')  # Theme background
        self.canvas = ThemedFigureCanvas(self.figure)
        # Disable WA_OpaquePaintEvent so our ThemedFigureCanvas.paintEvent
        # pre-fill is visible; the canvas handles its own background.
        self.canvas.setAttribute(Qt.WidgetAttribute.WA_OpaquePaintEvent, False)
        # Set size policy to allow canvas to expand and scale with window
        self.canvas.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.layout.addWidget(self.canvas)
        
        # --- Timeframe Buttons ---
        self.button_layout = QHBoxLayout()
        self.button_layout.setContentsMargins(5, 0, 0, 5)  # Small margin from bottom-left
        
        # Create timeframe buttons
        self.btn_10m = QPushButton("10m")
        self.btn_1h = QPushButton("1h") 
        self.btn_4h = QPushButton("4h")
        
        # Buttons styled by TradeChartWidget QPushButton in dark_theme.qss
        for btn in [self.btn_10m, self.btn_1h, self.btn_4h]:
            btn.setCheckable(True)
            self.button_layout.addWidget(btn)
        
        # Set default selection
        self.btn_10m.setChecked(True)
        
        # Add stretch to push buttons to left
        self.button_layout.addStretch()
        
        # Connect button signals
        self.btn_10m.clicked.connect(lambda: self._on_timeframe_clicked("10m"))
        self.btn_1h.clicked.connect(lambda: self._on_timeframe_clicked("1h"))
        self.btn_4h.clicked.connect(lambda: self._on_timeframe_clicked("4h"))
        
        # Add button layout to main layout
        self.layout.addLayout(self.button_layout)

    def _on_timeframe_clicked(self, timeframe: str):
        """Handle timeframe button clicks."""
        # Update button states
        self.btn_10m.setChecked(timeframe == "10m")
        self.btn_1h.setChecked(timeframe == "1h") 
        self.btn_4h.setChecked(timeframe == "4h")
        
        # Update current timeframe
        self.current_timeframe = timeframe
        
        # Refresh chart with new timeframe
        if self.full_dataframe is not None:
            self._update_chart_with_timeframe()
        
        # Emit signal for parent to handle data refresh if needed
        self.timeframe_changed.emit(timeframe)

    def _get_data_limit(self) -> int:
        """Get the number of raw 10m data points to fetch.
        
        For higher timeframes we need more raw candles so that after
        resampling (6:1 for 1h, 24:1 for 4h) we still have enough candles.
        """
        limits = {
            "10m": 144,   # 144 candles = 24 hours
            "1h": 1008,   # 1008 raw -> ~168 hourly candles (1 week)
            "4h": 4320    # 4320 raw -> ~180  4-hour candles (1 month)
        }
        return limits.get(self.current_timeframe, 144)

    def _get_candle_width(self) -> float:
        """Get optimal candle width based on timeframe."""
        widths = {
            "10m": 0.6,  # Thinner candles for more data points
            "1h": 0.8,   # Medium width
            "4h": 1.0    # Standard width for fewer data points
        }
        return widths.get(self.current_timeframe, 0.6)

    def clear_chart(self):
        """Clears all items from the chart and resets stored data."""
        self.full_dataframe = None
        self.figure.clear()
        self.canvas.draw()

    def set_data(self, df: pd.DataFrame, strategy_name: str):
        """Set chart data and render with current timeframe."""
        logger.debug(f"=== CHART WIDGET DEBUG ===")
        logger.debug(f"Strategy name: '{strategy_name}'")
        logger.debug(f"DataFrame shape: {df.shape}")
        logger.debug(f"DataFrame columns: {list(df.columns)}")
        
        # Check for Ping Pong specific columns
        if 'buy_level' in df.columns:
            logger.debug(f"*** BUY LEVEL FOUND *** Sample: {df['buy_level'].iloc[:3].tolist()}")
        else:
            logger.debug("*** NO BUY LEVEL COLUMN ***")
            
        if 'sell_level' in df.columns:
            logger.debug(f"*** SELL LEVEL FOUND *** Sample: {df['sell_level'].iloc[:3].tolist()}")
        else:
            logger.debug("*** NO SELL LEVEL COLUMN ***")

        # Check for signal columns
        if 'buy_signal' in df.columns:
            logger.debug(f"*** BUY SIGNAL FOUND *** Count: {df['buy_signal'].count()}")
        else:
            logger.debug("*** NO BUY SIGNAL COLUMN ***")
    
        if 'sell_signal' in df.columns:
            logger.debug(f"*** SELL SIGNAL FOUND *** Count: {df['sell_signal'].count()}")
        else:
            logger.debug("*** NO SELL SIGNAL COLUMN ***")
        
        # Store the full dataframe and strategy
        self.full_dataframe = df
        self.current_strategy = strategy_name
        
        # Render chart with current timeframe
        self._update_chart_with_timeframe()

    def _resample_ohlc(self, df: pd.DataFrame, timeframe: str) -> pd.DataFrame:
        """Resample 10-minute OHLC data into larger timeframe candles.
        
        Args:
            df: DataFrame with datetime index and Open/High/Low/Close columns
            timeframe: Target timeframe ('10m', '1h', '4h')
        Returns:
            Resampled DataFrame with proper OHLC aggregation
        """
        resample_map = {'1h': '1h', '4h': '4h'}
        rule = resample_map.get(timeframe)
        if not rule:
            return df  # 10m — no resampling needed
        
        ohlc_agg = {
            'Open': 'first',
            'High': 'max',
            'Low': 'min',
            'Close': 'last',
        }
        
        # Aggregate OHLC columns
        df_resampled = df.resample(rule).agg(ohlc_agg).dropna(subset=['Open'])
        
        # Carry forward non-OHLC columns (indicators, signals, levels) using last value
        extra_cols = [c for c in df.columns if c not in ohlc_agg and c != 'Volume']
        if extra_cols:
            df_extras = df[extra_cols].resample(rule).last()
            df_resampled = df_resampled.join(df_extras)
        
        logger.debug(f"Resampled {len(df)} candles -> {len(df_resampled)} {timeframe} candles")
        return df_resampled

    def _update_chart_with_timeframe(self):
        """Update chart with current timeframe."""
        if self.full_dataframe is None:
            return
            
        # Get data limit based on timeframe
        data_limit = self._get_data_limit()
        
        # Slice dataframe to limit (get most recent 10m data)
        df = self.full_dataframe.tail(data_limit).copy()
        
        logger.debug(f"Updating chart with timeframe {self.current_timeframe}: {len(df)} raw data points")
        
        self.figure.clear()
        if df.empty or not all(k in df for k in ['timestamp', 'open', 'high', 'low', 'close']):
            self.canvas.draw()
            return

        try:
            df_mpf = df.copy()
            df_mpf['datetime'] = pd.to_datetime(df_mpf['timestamp'], unit='s')
            df_mpf.set_index('datetime', inplace=True)
            df_mpf.rename(columns={'open': 'Open', 'high': 'High', 'low': 'Low', 'close': 'Close', 'volume': 'Volume'}, inplace=True)
            
            # Resample into larger candles if 1h or 4h selected
            df_mpf = self._resample_ohlc(df_mpf, self.current_timeframe)

            # --- Determine Panel Count --- 
            num_panels = 1 # Price panel only (volume removed - no pair-specific data available)
            indicator_panels = 0
            
            # Check what indicators we have and need separate panels for
            if self.current_strategy.lower() == 'ai_strategy':
                # AI strategy plots composite signal on main chart, no separate panels needed
                pass
            else:
                # Individual strategies may need separate panels for indicators
                if 'rsi' in df_mpf.columns: indicator_panels += 1
                if 'macd' in df_mpf.columns: indicator_panels += 1
                
            num_panels += indicator_panels

            # --- Axes Creation ---
            # Create the grid spec and all axes first.
            gs = self.figure.add_gridspec(num_panels, 1, height_ratios=[3] + [1] * indicator_panels, hspace=0)

            ax1 = self.figure.add_subplot(gs[0, 0])
            
            # Create indicator axes if needed
            indicator_axes = []
            for i in range(indicator_panels):
                ax_ind = self.figure.add_subplot(gs[1 + i, 0], sharex=ax1)
                indicator_axes.append(ax_ind)

            # --- Addplots List ---
            addplots = []

            # --- Plot Ping Pong Strategy Lines ---
            if 'ping pong' in self.current_strategy.lower():
                logger.debug("*** PING PONG STRATEGY DETECTED ***")
                
                if 'buy_level' in df_mpf.columns and 'sell_level' in df_mpf.columns:
                    logger.debug("*** PING PONG COLUMNS CREATED ***")
                    # Add horizontal lines for buy and sell levels
                    addplots.append(mpf.make_addplot(df_mpf['buy_level'], color='lime', ax=ax1, width=2, linestyle='--', alpha=0.8))
                    addplots.append(mpf.make_addplot(df_mpf['sell_level'], color='red', ax=ax1, width=2, linestyle='--', alpha=0.8))
                else:
                    logger.debug("*** PING PONG COLUMNS MISSING ***")

            # --- Plot Moving Average Lines (for both dedicated MA strategy and Manual indicator selection) ---
            if 'ma_fast' in df_mpf.columns and 'ma_slow' in df_mpf.columns:
                # Dual moving average crossover (no labels here - we'll add legend manually)
                addplots.append(mpf.make_addplot(df_mpf['ma_fast'], color='#00BFFF', ax=ax1, width=1.5, alpha=0.8))  # Deep sky blue
                addplots.append(mpf.make_addplot(df_mpf['ma_slow'], color='#FF6347', ax=ax1, width=1.5, alpha=0.8))  # Tomato red
            elif 'ma_single' in df_mpf.columns:
                # Single moving average
                addplots.append(mpf.make_addplot(df_mpf['ma_single'], color='orange', ax=ax1, width=2))

            # --- Plot Bollinger Bands (for both dedicated BB strategy and Manual indicator selection) ---
            if all(col in df_mpf.columns for col in ['bb_upper', 'bb_middle', 'bb_lower']):
                addplots.append(mpf.make_addplot(df_mpf['bb_upper'], color='purple', ax=ax1, width=1, alpha=0.7))
                addplots.append(mpf.make_addplot(df_mpf['bb_middle'], color='orange', ax=ax1, width=1.5, alpha=0.8))
                addplots.append(mpf.make_addplot(df_mpf['bb_lower'], color='purple', ax=ax1, width=1, alpha=0.7))

            # --- Plot AI Strategy Composite Signal ---
            if self.current_strategy.lower() == 'ai_strategy' and 'composite_signal_scaled' in df_mpf.columns:
                # The signal is scaled to the price range, so plot it on the main axis (ax1).
                addplots.append(mpf.make_addplot(df_mpf['composite_signal_scaled'], ax=ax1, color='fuchsia', width=2, alpha=0.8))
            else:
                # --- Plot Individual Indicator Signals on Separate Panels ---
                ax_idx = 0
                
                # Plot RSI on separate panel
                if 'rsi' in df_mpf.columns and ax_idx < len(indicator_axes):
                    addplots.append(mpf.make_addplot(df_mpf['rsi'], ax=indicator_axes[ax_idx], color='#0077FF', width=1.5))
                    
                    # Add RSI threshold lines if they exist
                    if 'rsi_buy_threshold' in df_mpf.columns:
                        addplots.append(mpf.make_addplot(df_mpf['rsi_buy_threshold'], ax=indicator_axes[ax_idx], color='lime', width=1, linestyle='--', alpha=0.7))
                    if 'rsi_sell_threshold' in df_mpf.columns:
                        addplots.append(mpf.make_addplot(df_mpf['rsi_sell_threshold'], ax=indicator_axes[ax_idx], color='red', width=1, linestyle='--', alpha=0.7))
                    
                    # Set RSI axis limits and labels
                    indicator_axes[ax_idx].set_ylim(0, 100)
                    indicator_axes[ax_idx].set_ylabel('RSI', color='white', fontsize=8)
                    ax_idx += 1
                
                # Plot MACD on separate panel
                if 'macd' in df_mpf.columns and 'macd_signal' in df_mpf.columns and ax_idx < len(indicator_axes):
                    addplots.append(mpf.make_addplot(df_mpf['macd'], ax=indicator_axes[ax_idx], color='#FF8800', width=1.5))
                    addplots.append(mpf.make_addplot(df_mpf['macd_signal'], ax=indicator_axes[ax_idx], color='#00DDFF', width=1))
                    
                    # Plot MACD histogram if it exists
                    if 'macd_histogram' in df_mpf.columns:
                        addplots.append(mpf.make_addplot(df_mpf['macd_histogram'], ax=indicator_axes[ax_idx], type='bar', color='gray', alpha=0.3))
                    
                    indicator_axes[ax_idx].set_ylabel('MACD', color='white', fontsize=8)
                    # Add zero line for MACD
                    indicator_axes[ax_idx].axhline(y=0, color='white', linestyle='-', alpha=0.3, linewidth=0.5)
                    ax_idx += 1

            # --- Plot Buy/Sell Signals ---
            if 'buy_signal' in df_mpf.columns:
                # Check if there are any non-NaN buy signals
                if df_mpf['buy_signal'].notna().any():
                    logger.debug(f"*** BUY SIGNALS DEBUG ***")
                    logger.debug(f"buy_signal column shape: {df_mpf['buy_signal'].shape}")
                    logger.debug(f"non-NaN count: {df_mpf['buy_signal'].notna().sum()}")
                    logger.debug(f"signal values: {df_mpf['buy_signal'].dropna().tolist()}")
                    addplots.append(mpf.make_addplot(df_mpf['buy_signal'], ax=ax1, type='scatter', markersize=50, marker='^', color='lime'))
            
            if 'sell_signal' in df_mpf.columns:
                # Check if there are any non-NaN sell signals
                if df_mpf['sell_signal'].notna().any():
                    logger.debug(f"*** SELL SIGNALS DEBUG ***")
                    logger.debug(f"sell_signal column shape: {df_mpf['sell_signal'].shape}")
                    logger.debug(f"non-NaN count: {df_mpf['sell_signal'].notna().sum()}")
                    logger.debug(f"signal values: {df_mpf['sell_signal'].dropna().tolist()}")
                    addplots.append(mpf.make_addplot(df_mpf['sell_signal'], ax=ax1, type='scatter', markersize=50, marker='v', color='red'))

            # --- Style All Axes ---
            all_axes = [ax1] + indicator_axes
            for ax in all_axes:
                ax.set_facecolor('#0f172a')  # Theme chart background 
                ax.tick_params(axis='y', colors='white', labelsize=8)
                ax.tick_params(axis='x', colors='white', labelsize=8)
                ax.spines['bottom'].set_color('white')
                ax.spines['top'].set_color('white') 
                ax.spines['left'].set_color('white')
                ax.spines['right'].set_color('white')
                if ax.get_ylabel():
                    ax.set_ylabel(ax.get_ylabel(), color='white', fontsize=8)

            # Hide x-axis labels on all but the last panel
            for ax in all_axes[:-1]:
                ax.tick_params(labelbottom=False)
            all_axes[-1].tick_params(labelbottom=True)

            ax1.set_ylabel('Price (XRD)', color='white', fontsize=9)

            # --- Plotting ---
            logger.debug(f"About to plot with {len(addplots)} addplots")
            # Adjust datetime format based on timeframe
            dt_fmt = '%H:%M' if self.current_timeframe == '10m' else '%d %b %H:%M'
            
            mpf.plot(df_mpf,
                     type='candle',
                     ax=ax1, 
                     volume=False,
                     addplot=addplots if addplots else None,
                     style=mpf_style,
                     datetime_format=dt_fmt,
                     xrotation=0,
                    )
            
            # Fix MA legend to top-left if MA indicators are present
            if 'ma_fast' in df_mpf.columns and 'ma_slow' in df_mpf.columns:
                from matplotlib.lines import Line2D
                # Create custom legend handles with explicit labels
                legend_elements = [
                    Line2D([0], [0], color='#00BFFF', linewidth=1.5, label='MA Fast'),
                    Line2D([0], [0], color='#FF6347', linewidth=1.5, label='MA Slow')
                ]
                ax1.legend(handles=legend_elements, loc='upper left', fontsize=8, framealpha=0.7, 
                          facecolor='#1E1E1E', edgecolor='white', labelcolor='#f0f0f0')
            
            logger.debug("Chart plotted successfully")
            
            # Remove any ghost axes that mplfinance may have created
            known_axes = set(id(ax) for ax in all_axes)
            for ax in self.figure.axes[:]:
                if id(ax) not in known_axes:
                    logger.debug(f"Removing ghost axes: pos={ax.get_position()}, visible={ax.get_visible()}")
                    self.figure.delaxes(ax)
            
            # Force all artists to clip to their axes — mplfinance can
            # create artists that leak into the figure margins
            for ax in all_axes:
                for artist in ax.get_children():
                    artist.set_clip_on(True)
            
            self.figure.tight_layout(pad=1.5, h_pad=0.5)
            self.canvas.draw()
            
        except Exception as e:
            logger.error(f"Failed to plot chart data: {e}", exc_info=True)
            self.figure.clear()
            self.figure.text(0.5, 0.5, f'Error: {e}', ha='center', va='center', color='red')
            self.canvas.draw()