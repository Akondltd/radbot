import os
import csv
import time
import logging
from datetime import datetime, timedelta
from PySide6.QtWidgets import (QWidget, QMessageBox, QTableWidget, QTableWidgetItem, 
                               QVBoxLayout, QHBoxLayout, QPushButton, QLabel, 
                               QHeaderView, QFileDialog, QComboBox, QDateTimeEdit,
                               QSpinBox, QFrame)
from PySide6.QtCore import Qt, QDateTime, QTimer
from PySide6.QtGui import QFont, QColor, QBrush
from .trade_history_ui import Ui_TradeHistoryTabMain

logger = logging.getLogger(__name__)

class TradeHistoryTabMain(QWidget):
    def __init__(self, parent=None, database=None):
        super().__init__(parent)
        self.ui = Ui_TradeHistoryTabMain()
        self.ui.setupUi(self)
        self.ui.retranslateUi(self)
        
        # Store database reference
        self.database = database
        
        # Current view settings
        self.current_view = 'daily'  # daily, weekly, monthly, yearly
        self.current_date = datetime.now()
        self.current_wallet = None
        
        # Trade history data
        self.trade_history_data = []
        self.filtered_data = []
        
        # Summary stats widgets (populated per-tab in _setup_summary_bars)
        self.summary_bars = {}
        
        # Initialize UI components
        self._setup_navigation_areas()
        self._setup_summary_bars()
        self._setup_trade_tables()
        self._setup_export_controls()
        
        # Connect signals
        self._connect_signals()
        
        # Load initial data
        self._load_trade_history()
        
        # Set up auto-refresh timer
        self.refresh_timer = QTimer()
        self.refresh_timer.timeout.connect(self._load_trade_history)
        self.refresh_timer.start(600000)  # Refresh every 10 minutes

    def _setup_navigation_areas(self):
        """Setup navigation controls for each time period tab"""
        
        # Create navigation widgets for each period
        daily_nav = self._create_navigation_widget('daily')
        weekly_nav = self._create_navigation_widget('weekly')
        monthly_nav = self._create_navigation_widget('monthly')
        yearly_nav = self._create_navigation_widget('yearly')
        
        # Replace placeholder labels with actual navigation widgets in corner widget
        if hasattr(self.ui, 'nav_container') and hasattr(self.ui, '_nav_labels'):
            # Get the container layout
            container_layout = self.ui.nav_container.layout()
            
            # Remove placeholder labels and add real navigation widgets
            nav_mapping = [
                (0, yearly_nav),   # Index 0 = Yearly
                (1, monthly_nav),  # Index 1 = Monthly
                (2, weekly_nav),   # Index 2 = Weekly
                (3, daily_nav)     # Index 3 = Daily
            ]
            
            for index, nav_widget in nav_mapping:
                # Remove placeholder if it exists
                if index in self.ui._nav_labels:
                    placeholder = self.ui._nav_labels[index]
                    container_layout.removeWidget(placeholder)
                    placeholder.setParent(None)
                    placeholder.deleteLater()
                
                # Add real navigation widget
                container_layout.addWidget(nav_widget)
                nav_widget.hide()  # Hide initially
                self.ui._nav_labels[index] = nav_widget
            
            # Show navigation for default tab (Daily = index 3)
            self.ui._nav_labels[3].show()
        else:
            # Fallback for legacy layout - use setGeometry
            daily_nav.setParent(self.ui.TradeHistoryTabMainDailySubTab)
            daily_nav.setGeometry(590, 10, 201, 30)
            
            weekly_nav.setParent(self.ui.TradeHistoryTabMainWeeklySubTab)
            weekly_nav.setGeometry(590, 10, 201, 30)
            
            monthly_nav.setParent(self.ui.TradeHistoryTabMainMonthlySubTab)
            monthly_nav.setGeometry(590, 10, 201, 30)
            
            yearly_nav.setParent(self.ui.TradeHistoryTabMainYearlySubTab)
            yearly_nav.setGeometry(590, 10, 201, 30)

    def _create_navigation_widget(self, period):
        """Create navigation widget for a specific time period"""
        nav_widget = QFrame()
        layout = QHBoxLayout(nav_widget)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Previous button
        prev_btn = QPushButton("◀")
        prev_btn.setMaximumWidth(30)
        prev_btn.clicked.connect(lambda: self._navigate_time(-1, period))
        
        # Current period label
        period_label = QLabel()
        period_label.setAlignment(Qt.AlignCenter)
        period_label.setObjectName(f"{period}_period_label")
        
        # Next button
        next_btn = QPushButton("▶")
        next_btn.setMaximumWidth(30)
        next_btn.clicked.connect(lambda: self._navigate_time(1, period))
        
        layout.addWidget(prev_btn)
        layout.addWidget(period_label)
        layout.addWidget(next_btn)
        
        self._update_period_label(period_label, period)
        
        return nav_widget

    def _update_period_label(self, label, period):
        """Update the period label text based on current date and period"""
        if period == 'daily':
            label.setText(self.current_date.strftime("%Y-%m-%d"))
        elif period == 'weekly':
            # Show week start and end
            start_of_week = self.current_date - timedelta(days=self.current_date.weekday())
            end_of_week = start_of_week + timedelta(days=6)
            label.setText(f"{start_of_week.strftime('%m/%d')} - {end_of_week.strftime('%m/%d')}")
        elif period == 'monthly':
            label.setText(self.current_date.strftime("%B %Y"))
        elif period == 'yearly':
            label.setText(str(self.current_date.year))

    def _navigate_time(self, direction, period):
        """Navigate time periods (direction: -1 for previous, 1 for next)"""
        if period == 'daily':
            self.current_date += timedelta(days=direction)
        elif period == 'weekly':
            self.current_date += timedelta(weeks=direction)
        elif period == 'monthly':
            if direction == 1:
                if self.current_date.month == 12:
                    self.current_date = self.current_date.replace(year=self.current_date.year + 1, month=1)
                else:
                    self.current_date = self.current_date.replace(month=self.current_date.month + 1)
            else:
                if self.current_date.month == 1:
                    self.current_date = self.current_date.replace(year=self.current_date.year - 1, month=12)
                else:
                    self.current_date = self.current_date.replace(month=self.current_date.month - 1)
        elif period == 'yearly':
            self.current_date = self.current_date.replace(year=self.current_date.year + direction)
        
        # Update all period labels
        for tab_period in ['daily', 'weekly', 'monthly', 'yearly']:
            label = self.findChild(QLabel, f"{tab_period}_period_label")
            if label:
                self._update_period_label(label, tab_period)
        
        # Refresh data for current view
        self.current_view = period
        self._filter_data_by_period()

    def _setup_trade_tables(self):
        """Setup trade history tables in each scroll area"""
        
        # Create tables for each time period
        self.daily_table = self._create_trade_table()
        self.weekly_table = self._create_trade_table()
        self.monthly_table = self._create_trade_table()
        self.yearly_table = self._create_trade_table()
        
        # Period-to-contents mapping
        period_map = [
            ('daily', self.ui.scrollAreaWidgetContents_3, self.daily_table),
            ('weekly', self.ui.scrollAreaWidgetContents_4, self.weekly_table),
            ('monthly', self.ui.scrollAreaWidgetContents_5, self.monthly_table),
            ('yearly', self.ui.scrollAreaWidgetContents_6, self.yearly_table),
        ]
        
        for period, contents, table in period_map:
            layout = QVBoxLayout()
            layout.setContentsMargins(0, 0, 0, 0)
            layout.setSpacing(0)
            if period in self.summary_bars:
                layout.addWidget(self.summary_bars[period])
            layout.addWidget(table)
            contents.setLayout(layout)

    def _setup_summary_bars(self):
        """Create summary stats bars for each period tab."""
        for period in ['daily', 'weekly', 'monthly', 'yearly']:
            bar = QFrame()
            bar.setFrameShape(QFrame.StyledPanel)
            bar_layout = QHBoxLayout(bar)
            bar_layout.setContentsMargins(8, 4, 8, 4)
            bar_layout.setSpacing(20)
            
            trades_label = QLabel("Trades: 0")
            trades_label.setObjectName(f"{period}_summary_trades")
            volume_label = QLabel("Volume: $0.00")
            volume_label.setObjectName(f"{period}_summary_volume")
            pnl_label = QLabel("P/L: $0.00")
            pnl_label.setObjectName(f"{period}_summary_pnl")
            winrate_label = QLabel("Win Rate: -")
            winrate_label.setObjectName(f"{period}_summary_winrate")
            
            for lbl in [trades_label, volume_label, pnl_label, winrate_label]:
                font = lbl.font()
                font.setBold(True)
                lbl.setFont(font)
            
            bar_layout.addWidget(trades_label)
            bar_layout.addWidget(volume_label)
            bar_layout.addWidget(pnl_label)
            bar_layout.addWidget(winrate_label)
            bar_layout.addStretch()
            
            self.summary_bars[period] = bar

    def _create_trade_table(self):
        """Create a trade history table widget"""
        table = QTableWidget()
        
        # Set up columns
        headers = ['Trade ID', 'Date/Time', 'Pair', 'Side', 'Base Amount', 'Quote Amount', 
                  'Price', 'USD Value', 'P/L (Token)', 'P/L (USD)', 'Status', 'Strategy', 'Tx Hash']
        table.setColumnCount(len(headers))
        table.setHorizontalHeaderLabels(headers)
        
        # Configure table appearance
        table.setAlternatingRowColors(True)
        table.setSelectionBehavior(QTableWidget.SelectRows)
        table.setSortingEnabled(True)
        
        # Hide the vertical header (row numbers)
        table.verticalHeader().setVisible(False)
        
        # Set column widths
        header = table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.Fixed)             # Trade ID
        header.setSectionResizeMode(1, QHeaderView.ResizeToContents)  # Date/Time
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)  # Pair
        header.setSectionResizeMode(3, QHeaderView.Fixed)             # Side
        header.setSectionResizeMode(4, QHeaderView.ResizeToContents)  # Base Amount
        header.setSectionResizeMode(5, QHeaderView.ResizeToContents)  # Quote Amount
        header.setSectionResizeMode(6, QHeaderView.ResizeToContents)  # Price
        header.setSectionResizeMode(7, QHeaderView.ResizeToContents)  # USD Value
        header.setSectionResizeMode(8, QHeaderView.ResizeToContents)  # P/L (Token)
        header.setSectionResizeMode(9, QHeaderView.ResizeToContents)  # P/L (USD)
        header.setSectionResizeMode(10, QHeaderView.Fixed)            # Status
        header.setSectionResizeMode(11, QHeaderView.ResizeToContents) # Strategy
        header.setSectionResizeMode(12, QHeaderView.Stretch)          # Tx Hash
        
        table.setColumnWidth(0, 70)   # Trade ID
        table.setColumnWidth(3, 60)   # Side
        table.setColumnWidth(10, 80)  # Status
        
        return table

    def _setup_export_controls(self):
        """Setup export date range controls"""
        # Set default date range (last 30 days)
        end_date = QDateTime.currentDateTime()
        start_date = end_date.addDays(-30)
        
        self.ui.TradeHistoryTabMainExportHistoryStartDateTimeDateInput.setDateTime(start_date)
        self.ui.TradeHistoryTabMainExportHistoryEndDateTimeDateInput.setDateTime(end_date)

    def _connect_signals(self):
        """Connect UI signals to handlers"""
        # Export button
        self.ui.TradeHistoryTabMainExportTradeHistoryButton.clicked.connect(self.export_trade_history)
        
        # Tab change signal
        self.ui.TradeHistoryTabMainDurationTabs.currentChanged.connect(self._on_tab_changed)

    def _on_tab_changed(self, index):
        """Handle tab change to update current view"""
        tab_names = ['yearly', 'monthly', 'weekly', 'daily']
        if 0 <= index < len(tab_names):
            self.current_view = tab_names[index]
            self._filter_data_by_period()

    def _load_trade_history(self):
        """Load trade history data from database"""
        if not self.database:
            return
            
        try:
            # Get all trade history (we'll filter in memory for better performance)
            self.trade_history_data = self.database.get_trade_history(limit=5000)
            self._filter_data_by_period()
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to load trade history: {str(e)}")

    def _filter_data_by_period(self):
        """Filter trade history data based on current view period"""
        if not self.trade_history_data:
            self.filtered_data = []
            self._populate_current_table()
            return
        
        # Calculate time range for current period
        start_time, end_time = self._get_period_time_range()
        
        # Filter data
        self.filtered_data = []
        for trade in self.trade_history_data:
            trade_time = datetime.fromtimestamp(trade['timestamp'])
            if start_time <= trade_time <= end_time:
                self.filtered_data.append(trade)
        
        # Sort by timestamp descending (most recent first)
        self.filtered_data.sort(key=lambda x: x['timestamp'], reverse=True)
        
        # Populate current table
        self._populate_current_table()

    def _get_period_time_range(self):
        """Get start and end time for current period"""
        if self.current_view == 'daily':
            start_time = self.current_date.replace(hour=0, minute=0, second=0, microsecond=0)
            end_time = start_time + timedelta(days=1) - timedelta(microseconds=1)
        elif self.current_view == 'weekly':
            start_of_week = self.current_date - timedelta(days=self.current_date.weekday())
            start_time = start_of_week.replace(hour=0, minute=0, second=0, microsecond=0)
            end_time = start_time + timedelta(days=7) - timedelta(microseconds=1)
        elif self.current_view == 'monthly':
            start_time = self.current_date.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            if self.current_date.month == 12:
                next_month = start_time.replace(year=start_time.year + 1, month=1)
            else:
                next_month = start_time.replace(month=start_time.month + 1)
            end_time = next_month - timedelta(microseconds=1)
        elif self.current_view == 'yearly':
            start_time = self.current_date.replace(month=1, day=1, hour=0, minute=0, second=0, microsecond=0)
            end_time = start_time.replace(year=start_time.year + 1) - timedelta(microseconds=1)
        
        return start_time, end_time

    def _populate_current_table(self):
        """Populate the current view's table with filtered data"""
        # Get current table
        table = self._get_current_table()
        if not table:
            return
        
        # Temporarily disable sorting to prevent interference during population
        table.setSortingEnabled(False)
        
        # Softer colors for profit/loss highlighting
        green_bg = QBrush(QColor(144, 238, 144))  # Light green
        red_bg = QBrush(QColor(255, 160, 160))     # Light red
        buy_bg = QBrush(QColor(200, 235, 200))     # Soft green for BUY
        sell_bg = QBrush(QColor(235, 200, 200))    # Soft red for SELL
        
        # Summary accumulators
        total_trades = 0
        total_volume_usd = 0.0
        total_pnl_usd = 0.0
        profitable_count = 0
        round_trip_count = 0
        
        try:
            # Clear existing data
            table.setRowCount(0)
            
            row_idx = 0
            # Populate with filtered data
            for trade in self.filtered_data:
                # Validate trade data before processing
                if not self._validate_trade_data(trade):
                    continue
                
                table.insertRow(row_idx)
                total_trades += 1
                
                # Format timestamp with error handling
                try:
                    trade_time = datetime.fromtimestamp(trade['timestamp'])
                    time_str = trade_time.strftime("%Y-%m-%d %H:%M:%S")
                except (ValueError, TypeError, OSError):
                    time_str = "Invalid Date"
                
                # Column 0: Trade ID
                trade_id = str(trade.get('trade_id_original', 'N/A'))
                table.setItem(row_idx, 0, QTableWidgetItem(trade_id))
                
                # Column 1: Date/Time
                table.setItem(row_idx, 1, QTableWidgetItem(str(time_str)))
                
                # Column 2: Pair
                table.setItem(row_idx, 2, QTableWidgetItem(str(trade.get('pair', 'Unknown'))))
                
                # Column 3: Side (color-coded)
                side = str(trade.get('side', 'UNKNOWN'))
                side_item = QTableWidgetItem(side)
                if side == 'BUY':
                    side_item.setBackground(buy_bg)
                elif side == 'SELL':
                    side_item.setBackground(sell_bg)
                table.setItem(row_idx, 3, side_item)
                
                # Column 4: Base Amount
                try:
                    amount_base = float(trade.get('amount_base', 0))
                    table.setItem(row_idx, 4, QTableWidgetItem(f"{amount_base:.6f}"))
                except (ValueError, TypeError):
                    table.setItem(row_idx, 4, QTableWidgetItem("0.000000"))
                
                # Column 5: Quote Amount
                try:
                    amount_quote = float(trade.get('amount_quote', 0))
                    table.setItem(row_idx, 5, QTableWidgetItem(f"{amount_quote:.6f}"))
                except (ValueError, TypeError):
                    table.setItem(row_idx, 5, QTableWidgetItem("0.000000"))
                
                # Column 6: Price
                try:
                    price = float(trade.get('price', 0))
                    table.setItem(row_idx, 6, QTableWidgetItem(f"{price:.6f}"))
                except (ValueError, TypeError):
                    table.setItem(row_idx, 6, QTableWidgetItem("0.000000"))
                
                # Column 7: USD Value
                try:
                    usd_value = float(trade.get('usd_value', 0))
                    total_volume_usd += usd_value
                    table.setItem(row_idx, 7, QTableWidgetItem(f"${usd_value:.2f}"))
                except (ValueError, TypeError):
                    table.setItem(row_idx, 7, QTableWidgetItem("$0.00"))
                
                # Column 8: P/L (Token) — from profit string like "5.234 XRD"
                profit_value = trade.get('profit')
                profit_text = profit_value if profit_value else "-"
                profit_item = QTableWidgetItem(profit_text)
                
                if profit_value and profit_value != "-":
                    try:
                        numeric_part = profit_value.split()[0]
                        profit_num = float(numeric_part)
                        if profit_num > 0:
                            profit_item.setBackground(green_bg)
                        elif profit_num < 0:
                            profit_item.setBackground(red_bg)
                    except (ValueError, IndexError):
                        pass
                table.setItem(row_idx, 8, profit_item)
                
                # Column 9: P/L (USD)
                profit_usd = trade.get('profit_usd')
                if profit_usd is not None:
                    pnl_usd = float(profit_usd)
                    total_pnl_usd += pnl_usd
                    round_trip_count += 1
                    if pnl_usd > 0:
                        profitable_count += 1
                    pnl_text = f"${pnl_usd:+.2f}"
                    pnl_item = QTableWidgetItem(pnl_text)
                    if pnl_usd > 0:
                        pnl_item.setBackground(green_bg)
                    elif pnl_usd < 0:
                        pnl_item.setBackground(red_bg)
                else:
                    pnl_item = QTableWidgetItem("-")
                table.setItem(row_idx, 9, pnl_item)
                
                # Column 10: Status
                table.setItem(row_idx, 10, QTableWidgetItem(str(trade.get('status', 'UNKNOWN'))))
                
                # Column 11: Strategy
                table.setItem(row_idx, 11, QTableWidgetItem(str(trade.get('strategy_name', 'Unknown'))))
                
                # Column 12: Transaction Hash (truncated)
                tx_hash = str(trade.get('transaction_hash', ''))
                if len(tx_hash) > 128:
                    tx_display = f"{tx_hash[:8]}...{tx_hash[-8:]}"
                elif len(tx_hash) > 0:
                    tx_display = tx_hash
                else:
                    tx_display = "No Hash"
                table.setItem(row_idx, 12, QTableWidgetItem(tx_display))
                
                row_idx += 1
                
        except Exception as e:
            logger.error(f"Error populating table: {e}", exc_info=True)
            
        finally:
            # Re-enable sorting after population is complete
            table.setSortingEnabled(True)
        
        # Update summary bar for current period
        self._update_summary_bar(total_trades, total_volume_usd, total_pnl_usd, 
                                  profitable_count, round_trip_count)

    def _get_current_table(self):
        """Get the table widget for current view"""
        if self.current_view == 'daily':
            return self.daily_table
        elif self.current_view == 'weekly':
            return self.weekly_table
        elif self.current_view == 'monthly':
            return self.monthly_table
        elif self.current_view == 'yearly':
            return self.yearly_table
        return None

    def _validate_trade_data(self, trade):
        """Validate that trade data contains required fields"""
        if not isinstance(trade, dict):
            return False
            
        required_fields = ['timestamp', 'pair', 'side', 'amount_base', 'amount_quote', 
                          'price', 'usd_value', 'status', 'strategy_name', 'transaction_hash']
        
        for field in required_fields:
            if field not in trade:
                logger.warning(f"Missing field in trade data: {field}")
                return False
                
        return True

    def _update_summary_bar(self, total_trades, total_volume_usd, total_pnl_usd, 
                             profitable_count, round_trip_count):
        """Update the summary stats bar for the current period."""
        period = self.current_view
        if period not in self.summary_bars:
            return
        
        # Find labels by object name
        trades_label = self.findChild(QLabel, f"{period}_summary_trades")
        volume_label = self.findChild(QLabel, f"{period}_summary_volume")
        pnl_label = self.findChild(QLabel, f"{period}_summary_pnl")
        winrate_label = self.findChild(QLabel, f"{period}_summary_winrate")
        
        if trades_label:
            trades_label.setText(f"Trades: {total_trades}")
        if volume_label:
            volume_label.setText(f"Volume: ${total_volume_usd:,.2f}")
        if pnl_label:
            pnl_text = f"P/L: ${total_pnl_usd:+,.2f}"
            pnl_label.setText(pnl_text)
            if total_pnl_usd > 0:
                pnl_label.setStyleSheet("color: green; font-weight: bold;")
            elif total_pnl_usd < 0:
                pnl_label.setStyleSheet("color: red; font-weight: bold;")
            else:
                pnl_label.setStyleSheet("font-weight: bold;")
        if winrate_label:
            if round_trip_count > 0:
                winrate = (profitable_count / round_trip_count) * 100
                winrate_label.setText(f"Win Rate: {winrate:.0f}% ({profitable_count}/{round_trip_count})")
            else:
                winrate_label.setText("Win Rate: -")

    def _split_pair(self, pair_str):
        """Split a pair string like 'HUG/XRD' into (base_currency, quote_currency)."""
        if '/' in pair_str:
            parts = pair_str.split('/', 1)
            return parts[0].strip(), parts[1].strip()
        return pair_str, ''

    def export_trade_history(self):
        """Export trade history to CSV file with format selection."""
        if not self.database:
            QMessageBox.warning(self, "Warning", "No database connection available.")
            return
        
        try:
            # Get date range from UI
            start_datetime = self.ui.TradeHistoryTabMainExportHistoryStartDateTimeDateInput.dateTime()
            end_datetime = self.ui.TradeHistoryTabMainExportHistoryEndDateTimeDateInput.dateTime()
            
            start_timestamp = int(start_datetime.toSecsSinceEpoch())
            end_timestamp = int(end_datetime.toSecsSinceEpoch())
            
            # Get trade history for date range
            trade_data = self.database.get_trade_history(
                start_timestamp=start_timestamp,
                end_timestamp=end_timestamp,
                limit=None
            )
            
            if not trade_data:
                QMessageBox.information(self, "Export", "No trade data found for the selected date range.")
                return
            
            # Ask user which format
            format_dialog = QMessageBox(self)
            format_dialog.setWindowTitle("Export Format")
            format_dialog.setText("Choose CSV export format:")
            format_dialog.setInformativeText(
                "Standard: Full details with USD P/L\n"
                "Koinly: Compatible with Koinly tax software\n"
                "CoinTracker: Compatible with CoinTracker tax software"
            )
            standard_btn = format_dialog.addButton("Standard", QMessageBox.AcceptRole)
            koinly_btn = format_dialog.addButton("Koinly", QMessageBox.AcceptRole)
            cointracker_btn = format_dialog.addButton("CoinTracker", QMessageBox.AcceptRole)
            format_dialog.addButton("Cancel", QMessageBox.RejectRole)
            format_dialog.exec()
            
            clicked = format_dialog.clickedButton()
            if clicked == standard_btn:
                export_format = 'standard'
            elif clicked == koinly_btn:
                export_format = 'koinly'
            elif clicked == cointracker_btn:
                export_format = 'cointracker'
            else:
                return
            
            # Default filename based on format
            date_range = f"{start_datetime.toString('yyyy-MM-dd')}_to_{end_datetime.toString('yyyy-MM-dd')}"
            default_name = f"trade_history_{export_format}_{date_range}.csv"
            
            file_path, _ = QFileDialog.getSaveFileName(
                self, "Export Trade History", default_name, "CSV Files (*.csv)"
            )
            
            if not file_path:
                return
            
            if export_format == 'koinly':
                self._export_koinly(file_path, trade_data)
            elif export_format == 'cointracker':
                self._export_cointracker(file_path, trade_data)
            else:
                self._export_standard(file_path, trade_data)
            
            QMessageBox.information(
                self, "Export Complete",
                f"Trade history exported successfully!\n\n"
                f"Format: {export_format.title()}\n"
                f"File: {file_path}\n"
                f"Records: {len(trade_data)}"
            )
            
        except Exception as e:
            logger.error(f"Export failed: {e}", exc_info=True)
            QMessageBox.critical(self, "Export Error", f"Failed to export trade history: {str(e)}")

    def _export_standard(self, file_path, trade_data):
        """Export in standard format with full details and USD P/L."""
        with open(file_path, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.writer(csvfile)
            
            writer.writerow([
                'Trade ID', 'Date', 'Time', 'Base Currency', 'Quote Currency',
                'Side', 'Base Amount', 'Quote Amount', 'Price',
                'USD Value', 'P/L (Token)', 'P/L (USD)', 'P/L (XRD)',
                'Status', 'Strategy', 'Transaction Hash', 'Wallet Address'
            ])
            
            for trade in trade_data:
                trade_datetime = datetime.fromtimestamp(trade['timestamp'])
                base_currency, quote_currency = self._split_pair(trade['pair'])
                
                profit_token = trade.get('profit', '') or ''
                profit_usd = trade.get('profit_usd')
                profit_xrd = trade.get('profit_xrd')
                
                writer.writerow([
                    trade.get('trade_id_original', ''),
                    trade_datetime.strftime('%Y-%m-%d'),
                    trade_datetime.strftime('%H:%M:%S'),
                    base_currency,
                    quote_currency,
                    trade['side'],
                    f"{float(trade['amount_base']):.8f}",
                    f"{float(trade['amount_quote']):.8f}",
                    f"{trade['price']:.8f}",
                    f"{trade['usd_value']:.2f}",
                    profit_token,
                    f"{profit_usd:.2f}" if profit_usd is not None else '',
                    f"{profit_xrd:.8f}" if profit_xrd is not None else '',
                    trade['status'],
                    trade['strategy_name'],
                    trade['transaction_hash'],
                    trade['wallet_address']
                ])

    def _export_koinly(self, file_path, trade_data):
        """Export in Koinly-compatible CSV format.
        
        Koinly expects: Date, Sent Amount, Sent Currency, Received Amount, 
        Received Currency, Fee Amount, Fee Currency, Net Worth Amount, 
        Net Worth Currency, Label, Description, TxHash
        """
        with open(file_path, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.writer(csvfile)
            
            writer.writerow([
                'Date', 'Sent Amount', 'Sent Currency', 'Received Amount',
                'Received Currency', 'Fee Amount', 'Fee Currency',
                'Net Worth Amount', 'Net Worth Currency', 'Label',
                'Description', 'TxHash'
            ])
            
            for trade in trade_data:
                trade_datetime = datetime.fromtimestamp(trade['timestamp'])
                base_currency, quote_currency = self._split_pair(trade['pair'])
                
                amount_base = float(trade['amount_base'])
                amount_quote = float(trade['amount_quote'])
                
                if trade['side'] == 'BUY':
                    # Buying base: sent quote, received base
                    sent_amount = f"{amount_quote:.8f}"
                    sent_currency = quote_currency
                    received_amount = f"{amount_base:.8f}"
                    received_currency = base_currency
                else:
                    # Selling base: sent base, received quote
                    sent_amount = f"{amount_base:.8f}"
                    sent_currency = base_currency
                    received_amount = f"{amount_quote:.8f}"
                    received_currency = quote_currency
                
                # Koinly date format: YYYY-MM-DD HH:MM UTC
                koinly_date = trade_datetime.strftime('%Y-%m-%d %H:%M UTC')
                
                writer.writerow([
                    koinly_date,
                    sent_amount,
                    sent_currency,
                    received_amount,
                    received_currency,
                    '',  # Fee Amount (network fee not tracked per-trade)
                    '',  # Fee Currency
                    f"{trade['usd_value']:.2f}",
                    'USD',
                    '',  # Label
                    f"{trade['strategy_name']} trade via RadBot",
                    trade['transaction_hash']
                ])

    def _export_cointracker(self, file_path, trade_data):
        """Export in CoinTracker-compatible CSV format.
        
        CoinTracker expects: Date, Type, Received Quantity, Received Currency,
        Sent Quantity, Sent Currency, Fee Amount, Fee Currency, Tag
        """
        with open(file_path, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.writer(csvfile)
            
            writer.writerow([
                'Date', 'Type', 'Received Quantity', 'Received Currency',
                'Sent Quantity', 'Sent Currency', 'Fee Amount', 'Fee Currency', 'Tag'
            ])
            
            for trade in trade_data:
                trade_datetime = datetime.fromtimestamp(trade['timestamp'])
                base_currency, quote_currency = self._split_pair(trade['pair'])
                
                amount_base = float(trade['amount_base'])
                amount_quote = float(trade['amount_quote'])
                
                if trade['side'] == 'BUY':
                    received_qty = f"{amount_base:.8f}"
                    received_currency = base_currency
                    sent_qty = f"{amount_quote:.8f}"
                    sent_currency = quote_currency
                else:
                    received_qty = f"{amount_quote:.8f}"
                    received_currency = quote_currency
                    sent_qty = f"{amount_base:.8f}"
                    sent_currency = base_currency
                
                # CoinTracker date format: MM/DD/YYYY HH:MM:SS
                ct_date = trade_datetime.strftime('%m/%d/%Y %H:%M:%S')
                
                writer.writerow([
                    ct_date,
                    'Trade',
                    received_qty,
                    received_currency,
                    sent_qty,
                    sent_currency,
                    '',  # Fee Amount
                    '',  # Fee Currency
                    trade['strategy_name']
                ])

    def refresh_data(self):
        """Manually refresh trade history data"""
        self._load_trade_history()

    def set_wallet_filter(self, wallet_address):
        """Set wallet address filter"""
        self.current_wallet = wallet_address
        self._load_trade_history()

    def get_trade_summary(self):
        """Get summary statistics for current filtered data"""
        if not self.filtered_data:
            return {
                'total_trades': 0,
                'total_volume': 0.0,
                'total_pnl_usd': 0.0,
                'buy_trades': 0,
                'sell_trades': 0,
                'profitable_count': 0,
                'round_trip_count': 0
            }
        
        total_trades = len(self.filtered_data)
        total_volume = sum(float(trade.get('usd_value', 0)) for trade in self.filtered_data)
        buy_trades = sum(1 for trade in self.filtered_data if trade['side'] == 'BUY')
        sell_trades = total_trades - buy_trades
        
        total_pnl_usd = 0.0
        profitable_count = 0
        round_trip_count = 0
        for trade in self.filtered_data:
            pnl = trade.get('profit_usd')
            if pnl is not None:
                total_pnl_usd += float(pnl)
                round_trip_count += 1
                if float(pnl) > 0:
                    profitable_count += 1
        
        return {
            'total_trades': total_trades,
            'total_volume': total_volume,
            'total_pnl_usd': total_pnl_usd,
            'buy_trades': buy_trades,
            'sell_trades': sell_trades,
            'profitable_count': profitable_count,
            'round_trip_count': round_trip_count
        }