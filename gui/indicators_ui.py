from PySide6.QtCore import QCoreApplication, QRect, Qt
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QCheckBox, QGroupBox, QLabel, QLineEdit, QPushButton, QWidget,
    QVBoxLayout, QHBoxLayout, QGridLayout, QFormLayout, QSizePolicy
)
from gui import resources_rc

# Toggle between layout-based (True) and legacy setGeometry (False)
USE_RESPONSIVE_LAYOUTS = True

class Ui_IndicatorsTabMain(object):
    def setupUi(self, IndicatorsTabMain):
        if USE_RESPONSIVE_LAYOUTS:
            self.setupUi_layouts(IndicatorsTabMain)
        else:
            self.setupUi_legacy(IndicatorsTabMain)
    
    def setupUi_layouts(self, IndicatorsTabMain):
        """Layout-based responsive UI setup"""
        IndicatorsTabMain.setObjectName("IndicatorsTabMain")
        
        # Main vertical layout
        main_layout = QVBoxLayout(IndicatorsTabMain)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(15)
        
        # Top row: AI Strategy box + Description text (horizontal layout)
        top_row = QHBoxLayout()
        top_row.setSpacing(20)
        
        # AI Strategy Group Box (left side)
        self.IndicatorsTabMainAIStrategyGroupBox = QGroupBox("AI Strategy")
        self.IndicatorsTabMainAIStrategyGroupBox.setObjectName("IndicatorsTabMainAIStrategyGroupBox")
        self.IndicatorsTabMainAIStrategyGroupBox.setMinimumWidth(220)
        self.IndicatorsTabMainAIStrategyGroupBox.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        
        ai_layout = QVBoxLayout(self.IndicatorsTabMainAIStrategyGroupBox)
        ai_layout.setContentsMargins(10, 15, 10, 10)
        
        self.IndicatorsTabMainAIStrategyRSIPeriodTitle = QLabel()
        self.IndicatorsTabMainAIStrategyRSIPeriodTitle.setObjectName("IndicatorsTabMainAIStrategyRSIPeriodTitle")
        self.IndicatorsTabMainAIStrategyRSIPeriodTitle.setWordWrap(True)
        ai_layout.addWidget(self.IndicatorsTabMainAIStrategyRSIPeriodTitle)
        
        top_row.addWidget(self.IndicatorsTabMainAIStrategyGroupBox, stretch=1)
        
        # Description text (right side - expands to fill)
        self.IndicatorsTabMainIndicatorsText = QLabel()
        self.IndicatorsTabMainIndicatorsText.setObjectName("IndicatorsTabMainIndicatorsText")
        self.IndicatorsTabMainIndicatorsText.setWordWrap(True)
        self.IndicatorsTabMainIndicatorsText.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)
        top_row.addWidget(self.IndicatorsTabMainIndicatorsText, stretch=2)
        
        main_layout.addLayout(top_row)
        
        # Grid layout for indicator boxes (2 rows x 3 columns)
        grid_layout = QGridLayout()
        grid_layout.setSpacing(15)
        
        # Set column stretch factors (all equal)
        grid_layout.setColumnStretch(0, 1)
        grid_layout.setColumnStretch(1, 1)
        grid_layout.setColumnStretch(2, 1)
        
        # Set row stretch factors (both equal)
        grid_layout.setRowStretch(0, 1)
        grid_layout.setRowStretch(1, 1)
        
        # Row 1: RSI, MA Cross, BB
        # Row 2: MACD, Ping Pong, (empty)
        
        # RSI Group Box (Row 0, Col 0)
        self.IndicatorsTabMainRSIGroupBox = self._create_rsi_group()
        grid_layout.addWidget(self.IndicatorsTabMainRSIGroupBox, 0, 0)
        
        # MA Cross Group Box (Row 0, Col 1)
        self.IndicatorsTabMainMACrossGroupBox = self._create_macross_group()
        grid_layout.addWidget(self.IndicatorsTabMainMACrossGroupBox, 0, 1)
        
        # Bollinger Bands Group Box (Row 0, Col 2)
        self.IndicatorsTabMainBBGroupBox = self._create_bb_group()
        grid_layout.addWidget(self.IndicatorsTabMainBBGroupBox, 0, 2)
        
        # MACD Group Box (Row 1, Col 0)
        self.IndicatorsTabMainMACDGroupBox = self._create_macd_group()
        grid_layout.addWidget(self.IndicatorsTabMainMACDGroupBox, 1, 0)
        
        # Ping Pong Group Box (Row 1, Col 1, spans 2 columns)
        self.IndicatorsTabMainPingPongGroupBox = self._create_pingpong_group()
        grid_layout.addWidget(self.IndicatorsTabMainPingPongGroupBox, 1, 1, 1, 2)
        
        main_layout.addLayout(grid_layout, stretch=1)  # Grid gets stretch factor
        
        # Bottom section: Save button (right-aligned)
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        self.IndicatorTabMainSaveAsDefaultSettingsButton = QPushButton("Save As Default Settings")
        self.IndicatorTabMainSaveAsDefaultSettingsButton.setObjectName("IndicatorTabMainSaveAsDefaultSettingsButton")
        self.IndicatorTabMainSaveAsDefaultSettingsButton.setMinimumSize(180, 70)
        self.IndicatorTabMainSaveAsDefaultSettingsButton.setMaximumWidth(200)
        button_layout.addWidget(self.IndicatorTabMainSaveAsDefaultSettingsButton)
        
        main_layout.addLayout(button_layout)  # No stretch after button
        
        self.retranslateUi(IndicatorsTabMain)
    
    def _create_rsi_group(self):
        """Create RSI indicator group box"""
        group = QGroupBox("Relative Strength Index")
        group.setObjectName("IndicatorsTabMainRSIGroupBox")
        group.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        
        form_layout = QFormLayout(group)
        form_layout.setContentsMargins(10, 15, 10, 10)
        form_layout.setSpacing(10)
        form_layout.setFieldGrowthPolicy(QFormLayout.FieldGrowthPolicy.ExpandingFieldsGrow)
        
        self.IndicatorsTabMainRSIGroupBoxRSILowValueTitle = QLabel("RSI Low Value")
        self.IndicatorsTabMainRSIGroupBoxRSILowValueTitle.setObjectName("IndicatorsTabMainRSIGroupBoxRSILowValueTitle")
        self.IndicatorsTabMainRSIGroupBoxLowValueTextInput = QLineEdit()
        self.IndicatorsTabMainRSIGroupBoxLowValueTextInput.setObjectName("IndicatorsTabMainRSIGroupBoxLowValueTextInput")
        form_layout.addRow(self.IndicatorsTabMainRSIGroupBoxRSILowValueTitle, self.IndicatorsTabMainRSIGroupBoxLowValueTextInput)
        
        self.IndicatorsTabMainRSIGroupBoxHighValueTitle = QLabel("RSI High Value")
        self.IndicatorsTabMainRSIGroupBoxHighValueTitle.setObjectName("IndicatorsTabMainRSIGroupBoxHighValueTitle")
        self.IndicatorsTabMainRSIGroupBoxHighValueTextInput = QLineEdit()
        self.IndicatorsTabMainRSIGroupBoxHighValueTextInput.setObjectName("IndicatorsTabMainRSIGroupBoxHighValueTextInput")
        form_layout.addRow(self.IndicatorsTabMainRSIGroupBoxHighValueTitle, self.IndicatorsTabMainRSIGroupBoxHighValueTextInput)
        
        self.IndicatorsTabMainRSIGroupBoxPeriodTitle = QLabel("RSI Period")
        self.IndicatorsTabMainRSIGroupBoxPeriodTitle.setObjectName("IndicatorsTabMainRSIGroupBoxPeriodTitle")
        self.IndicatorsTabMainRSIGroupBoxPeriodTextInput = QLineEdit()
        self.IndicatorsTabMainRSIGroupBoxPeriodTextInput.setObjectName("IndicatorsTabMainRSIGroupBoxPeriodTextInput")
        form_layout.addRow(self.IndicatorsTabMainRSIGroupBoxPeriodTitle, self.IndicatorsTabMainRSIGroupBoxPeriodTextInput)
        
        return group
    
    def _create_macross_group(self):
        """Create MA Crossover indicator group box"""
        group = QGroupBox("Moving Average Crossover")
        group.setObjectName("IndicatorsTabMainMACrossGroupBox")
        group.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        
        form_layout = QFormLayout(group)
        form_layout.setContentsMargins(10, 15, 10, 10)
        form_layout.setSpacing(10)
        form_layout.setFieldGrowthPolicy(QFormLayout.FieldGrowthPolicy.ExpandingFieldsGrow)
        
        self.IndicatorsTabMainMACrossGroupBoxShortTimeTitle = QLabel("MA Cross Fast")
        self.IndicatorsTabMainMACrossGroupBoxShortTimeTitle.setObjectName("IndicatorsTabMainMACrossGroupBoxShortTimeTitle")
        self.IndicatorsTabMainMACrossGroupBoxShortTimeTextInput = QLineEdit()
        self.IndicatorsTabMainMACrossGroupBoxShortTimeTextInput.setObjectName("IndicatorsTabMainMACrossGroupBoxShortTimeTextInput")
        form_layout.addRow(self.IndicatorsTabMainMACrossGroupBoxShortTimeTitle, self.IndicatorsTabMainMACrossGroupBoxShortTimeTextInput)
        
        self.IndicatorsTabMainMACrossGroupBoxLongTimeTitle = QLabel("MA Cross Slow")
        self.IndicatorsTabMainMACrossGroupBoxLongTimeTitle.setObjectName("IndicatorsTabMainMACrossGroupBoxLongTimeTitle")
        self.IndicatorsTabMainMACrossGroupBoxLongTimeTextInput = QLineEdit()
        self.IndicatorsTabMainMACrossGroupBoxLongTimeTextInput.setObjectName("IndicatorsTabMainMACrossGroupBoxLongTimeTextInput")
        form_layout.addRow(self.IndicatorsTabMainMACrossGroupBoxLongTimeTitle, self.IndicatorsTabMainMACrossGroupBoxLongTimeTextInput)
        
        return group
    
    def _create_bb_group(self):
        """Create Bollinger Bands indicator group box"""
        group = QGroupBox("Bollinger Bands")
        group.setObjectName("IndicatorsTabMainBBGroupBox")
        group.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        
        form_layout = QFormLayout(group)
        form_layout.setContentsMargins(10, 15, 10, 10)
        form_layout.setSpacing(10)
        form_layout.setFieldGrowthPolicy(QFormLayout.FieldGrowthPolicy.ExpandingFieldsGrow)
        
        self.IndicatorsTabMainBBGroupBoxBBPeriodTitle = QLabel("BB Period")
        self.IndicatorsTabMainBBGroupBoxBBPeriodTitle.setObjectName("IndicatorsTabMainBBGroupBoxBBPeriodTitle")
        self.IndicatorsTabMainBBGroupBoxBBPeriodTextInput = QLineEdit()
        self.IndicatorsTabMainBBGroupBoxBBPeriodTextInput.setObjectName("IndicatorsTabMainBBGroupBoxBBPeriodTextInput")
        form_layout.addRow(self.IndicatorsTabMainBBGroupBoxBBPeriodTitle, self.IndicatorsTabMainBBGroupBoxBBPeriodTextInput)
        
        self.IndicatorsTabMainBBGroupBoxBBStdDevMultiplierTitle = QLabel("BB Std Dev Multiplier")
        self.IndicatorsTabMainBBGroupBoxBBStdDevMultiplierTitle.setObjectName("IndicatorsTabMainBBGroupBoxBBStdDevMultiplierTitle")
        self.IndicatorsTabMainBBGroupBoxBBStdDevMultiplierTextInput = QLineEdit()
        self.IndicatorsTabMainBBGroupBoxBBStdDevMultiplierTextInput.setObjectName("IndicatorsTabMainBBGroupBoxBBStdDevMultiplierTextInput")
        form_layout.addRow(self.IndicatorsTabMainBBGroupBoxBBStdDevMultiplierTitle, self.IndicatorsTabMainBBGroupBoxBBStdDevMultiplierTextInput)
        
        return group
    
    def _create_macd_group(self):
        """Create MACD indicator group box"""
        group = QGroupBox("Moving Average Convergence Divergence")
        group.setObjectName("IndicatorsTabMainMACDGroupBox")
        group.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        
        form_layout = QFormLayout(group)
        form_layout.setContentsMargins(10, 15, 10, 10)
        form_layout.setSpacing(10)
        form_layout.setFieldGrowthPolicy(QFormLayout.FieldGrowthPolicy.ExpandingFieldsGrow)
        
        self.IndicatorsTabMainMACDGroupBoxMACDLowTitle = QLabel("MACD Fast Timeframe")
        self.IndicatorsTabMainMACDGroupBoxMACDLowTitle.setObjectName("IndicatorsTabMainMACDGroupBoxMACDLowTitle")
        self.IndicatorsTabMainMACDGroupBoxMACDLowTextInput = QLineEdit()
        self.IndicatorsTabMainMACDGroupBoxMACDLowTextInput.setObjectName("IndicatorsTabMainMACDGroupBoxMACDLowTextInput")
        form_layout.addRow(self.IndicatorsTabMainMACDGroupBoxMACDLowTitle, self.IndicatorsTabMainMACDGroupBoxMACDLowTextInput)
        
        self.IndicatorsTabMainMACDGroupBoxMACDHighTitle = QLabel("MACD Slow Timeframe")
        self.IndicatorsTabMainMACDGroupBoxMACDHighTitle.setObjectName("IndicatorsTabMainMACDGroupBoxMACDHighTitle")
        self.IndicatorsTabMainMACDGroupBoxMACDHighTextInput = QLineEdit()
        self.IndicatorsTabMainMACDGroupBoxMACDHighTextInput.setObjectName("IndicatorsTabMainMACDGroupBoxMACDHighTextInput")
        form_layout.addRow(self.IndicatorsTabMainMACDGroupBoxMACDHighTitle, self.IndicatorsTabMainMACDGroupBoxMACDHighTextInput)
        
        self.IndicatorsTabMainMACDGroupBoxMACDPeriodTitle = QLabel("MACD Signal Period")
        self.IndicatorsTabMainMACDGroupBoxMACDPeriodTitle.setObjectName("IndicatorsTabMainMACDGroupBoxMACDPeriodTitle")
        self.IndicatorsTabMainMACDGroupBoxMACDPeriodTextInput = QLineEdit()
        self.IndicatorsTabMainMACDGroupBoxMACDPeriodTextInput.setObjectName("IndicatorsTabMainMACDGroupBoxMACDPeriodTextInput")
        form_layout.addRow(self.IndicatorsTabMainMACDGroupBoxMACDPeriodTitle, self.IndicatorsTabMainMACDGroupBoxMACDPeriodTextInput)
        
        return group
    
    def _create_pingpong_group(self):
        """Create Ping Pong group box"""
        group = QGroupBox("Ping Pong")
        group.setObjectName("IndicatorsTabMainPingPongGroupBox")
        group.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        
        layout = QVBoxLayout(group)
        layout.setContentsMargins(10, 15, 10, 10)
        layout.setSpacing(10)
        
        self.IndicatorsTabMainPingPongGroupBoxText = QLabel()
        self.IndicatorsTabMainPingPongGroupBoxText.setObjectName("IndicatorsTabMainPingPongGroupBoxText")
        self.IndicatorsTabMainPingPongGroupBoxText.setWordWrap(True)
        layout.addWidget(self.IndicatorsTabMainPingPongGroupBoxText)
        
        # Buy/Sell price inputs in horizontal layout
        price_layout = QHBoxLayout()
        
        self.IndicatorsTabMainPingPongGroupBoxBuyPriceTitle = QLabel("Buy Price")
        self.IndicatorsTabMainPingPongGroupBoxBuyPriceTitle.setObjectName("IndicatorsTabMainPingPongGroupBoxBuyPriceTitle")
        price_layout.addWidget(self.IndicatorsTabMainPingPongGroupBoxBuyPriceTitle)
        
        self.IndicatorsTabMainPingPongGroupBoxBuyPriceInput = QLineEdit()
        self.IndicatorsTabMainPingPongGroupBoxBuyPriceInput.setObjectName("IndicatorsTabMainPingPongGroupBoxBuyPriceInput")
        self.IndicatorsTabMainPingPongGroupBoxBuyPriceInput.setMaximumWidth(100)
        price_layout.addWidget(self.IndicatorsTabMainPingPongGroupBoxBuyPriceInput)
        
        price_layout.addSpacing(20)
        
        self.IndicatorsTabMainPingPongGroupBoxSellPriceTitle = QLabel("Sell Price")
        self.IndicatorsTabMainPingPongGroupBoxSellPriceTitle.setObjectName("IndicatorsTabMainPingPongGroupBoxSellPriceTitle")
        price_layout.addWidget(self.IndicatorsTabMainPingPongGroupBoxSellPriceTitle)
        
        self.IndicatorsTabMainPingPongGroupBoxSellPriceInput = QLineEdit()
        self.IndicatorsTabMainPingPongGroupBoxSellPriceInput.setObjectName("IndicatorsTabMainPingPongGroupBoxSellPriceInput")
        self.IndicatorsTabMainPingPongGroupBoxSellPriceInput.setMaximumWidth(100)
        price_layout.addWidget(self.IndicatorsTabMainPingPongGroupBoxSellPriceInput)
        
        price_layout.addStretch()
        layout.addLayout(price_layout)
        
        return group
    
    def setupUi_legacy(self, IndicatorsTabMain):
        """Legacy setGeometry-based UI setup"""
        IndicatorsTabMain.setObjectName("IndicatorsTabMain")
        IndicatorsTabMain.resize(800, 570)
        
        font1 = QFont()
        font1.setPointSize(10)
        font1.setBold(True)
        font1.setWeight(QFont.Weight.Bold)
        
        # AI Strategy Group Box
        self.IndicatorsTabMainAIStrategyGroupBox = QGroupBox(IndicatorsTabMain)
        self.IndicatorsTabMainAIStrategyGroupBox.setObjectName("IndicatorsTabMainAIStrategyGroupBox")
        self.IndicatorsTabMainAIStrategyGroupBox.setGeometry(QRect(30, 20, 221, 111))
        
        self.IndicatorsTabMainAIStrategyRSIPeriodTitle = QLabel(self.IndicatorsTabMainAIStrategyGroupBox)
        self.IndicatorsTabMainAIStrategyRSIPeriodTitle.setObjectName("IndicatorsTabMainAIStrategyRSIPeriodTitle")
        self.IndicatorsTabMainAIStrategyRSIPeriodTitle.setGeometry(QRect(10, 25, 201, 70))
        self.IndicatorsTabMainAIStrategyRSIPeriodTitle.setWordWrap(True)
        
        self.IndicatorsTabMainIndicatorsText = QLabel(IndicatorsTabMain)
        self.IndicatorsTabMainIndicatorsText.setObjectName("IndicatorsTabMainIndicatorsText")
        self.IndicatorsTabMainIndicatorsText.setGeometry(QRect(270, 30, 495, 70))
        self.IndicatorsTabMainIndicatorsText.setWordWrap(True)
        
        # RSI Group Box
        self.IndicatorsTabMainRSIGroupBox = QGroupBox(IndicatorsTabMain)
        self.IndicatorsTabMainRSIGroupBox.setObjectName("IndicatorsTabMainRSIGroupBox")
        self.IndicatorsTabMainRSIGroupBox.setGeometry(QRect(30, 150, 221, 121))
        
        self.IndicatorsTabMainRSIGroupBoxRSILowValueTitle = QLabel(self.IndicatorsTabMainRSIGroupBox)
        self.IndicatorsTabMainRSIGroupBoxRSILowValueTitle.setObjectName("IndicatorsTabMainRSIGroupBoxRSILowValueTitle")
        self.IndicatorsTabMainRSIGroupBoxRSILowValueTitle.setGeometry(QRect(10, 30, 81, 16))
        
        self.IndicatorsTabMainRSIGroupBoxHighValueTitle = QLabel(self.IndicatorsTabMainRSIGroupBox)
        self.IndicatorsTabMainRSIGroupBoxHighValueTitle.setObjectName("IndicatorsTabMainRSIGroupBoxHighValueTitle")
        self.IndicatorsTabMainRSIGroupBoxHighValueTitle.setGeometry(QRect(10, 60, 81, 16))
        
        self.IndicatorsTabMainRSIGroupBoxPeriodTitle = QLabel(self.IndicatorsTabMainRSIGroupBox)
        self.IndicatorsTabMainRSIGroupBoxPeriodTitle.setObjectName("IndicatorsTabMainRSIGroupBoxPeriodTitle")
        self.IndicatorsTabMainRSIGroupBoxPeriodTitle.setGeometry(QRect(10, 90, 91, 16))
        
        self.IndicatorsTabMainRSIGroupBoxLowValueTextInput = QLineEdit(self.IndicatorsTabMainRSIGroupBox)
        self.IndicatorsTabMainRSIGroupBoxLowValueTextInput.setObjectName("IndicatorsTabMainRSIGroupBoxLowValueTextInput")
        self.IndicatorsTabMainRSIGroupBoxLowValueTextInput.setGeometry(QRect(130, 30, 71, 22))
        
        self.IndicatorsTabMainRSIGroupBoxHighValueTextInput = QLineEdit(self.IndicatorsTabMainRSIGroupBox)
        self.IndicatorsTabMainRSIGroupBoxHighValueTextInput.setObjectName("IndicatorsTabMainRSIGroupBoxHighValueTextInput")
        self.IndicatorsTabMainRSIGroupBoxHighValueTextInput.setGeometry(QRect(130, 60, 71, 22))
        
        self.IndicatorsTabMainRSIGroupBoxPeriodTextInput = QLineEdit(self.IndicatorsTabMainRSIGroupBox)
        self.IndicatorsTabMainRSIGroupBoxPeriodTextInput.setObjectName("IndicatorsTabMainRSIGroupBoxPeriodTextInput")
        self.IndicatorsTabMainRSIGroupBoxPeriodTextInput.setGeometry(QRect(130, 90, 71, 22))
        
        # Moving Average Crossover Group Box
        self.IndicatorsTabMainMACrossGroupBox = QGroupBox(IndicatorsTabMain)
        self.IndicatorsTabMainMACrossGroupBox.setObjectName("IndicatorsTabMainMACrossGroupBox")
        self.IndicatorsTabMainMACrossGroupBox.setGeometry(QRect(270, 150, 241, 121))
        
        self.IndicatorsTabMainMACrossGroupBoxShortTimeTitle = QLabel(self.IndicatorsTabMainMACrossGroupBox)
        self.IndicatorsTabMainMACrossGroupBoxShortTimeTitle.setObjectName("IndicatorsTabMainMACrossGroupBoxShortTimeTitle")
        self.IndicatorsTabMainMACrossGroupBoxShortTimeTitle.setGeometry(QRect(10, 40, 151, 16))
        
        self.IndicatorsTabMainMACrossGroupBoxLongTimeTitle = QLabel(self.IndicatorsTabMainMACrossGroupBox)
        self.IndicatorsTabMainMACrossGroupBoxLongTimeTitle.setObjectName("IndicatorsTabMainMACrossGroupBoxLongTimeTitle")
        self.IndicatorsTabMainMACrossGroupBoxLongTimeTitle.setGeometry(QRect(10, 80, 151, 16))
        
        self.IndicatorsTabMainMACrossGroupBoxShortTimeTextInput = QLineEdit(self.IndicatorsTabMainMACrossGroupBox)
        self.IndicatorsTabMainMACrossGroupBoxShortTimeTextInput.setObjectName("IndicatorsTabMainMACrossGroupBoxShortTimeTextInput")
        self.IndicatorsTabMainMACrossGroupBoxShortTimeTextInput.setGeometry(QRect(170, 40, 61, 22))
        
        self.IndicatorsTabMainMACrossGroupBoxLongTimeTextInput = QLineEdit(self.IndicatorsTabMainMACrossGroupBox)
        self.IndicatorsTabMainMACrossGroupBoxLongTimeTextInput.setObjectName("IndicatorsTabMainMACrossGroupBoxLongTimeTextInput")
        self.IndicatorsTabMainMACrossGroupBoxLongTimeTextInput.setGeometry(QRect(170, 80, 61, 22))
        
        # Bollinger Bands Group Box
        self.IndicatorsTabMainBBGroupBox = QGroupBox(IndicatorsTabMain)
        self.IndicatorsTabMainBBGroupBox.setObjectName("IndicatorsTabMainBBGroupBox")
        self.IndicatorsTabMainBBGroupBox.setGeometry(QRect(530, 150, 231, 121))
        
        self.IndicatorsTabMainBBGroupBoxBBPeriodTitle = QLabel(self.IndicatorsTabMainBBGroupBox)
        self.IndicatorsTabMainBBGroupBoxBBPeriodTitle.setObjectName("IndicatorsTabMainBBGroupBoxBBPeriodTitle")
        self.IndicatorsTabMainBBGroupBoxBBPeriodTitle.setGeometry(QRect(10, 40, 91, 16))
        
        self.IndicatorsTabMainBBGroupBoxBBStdDevMultiplierTitle = QLabel(self.IndicatorsTabMainBBGroupBox)
        self.IndicatorsTabMainBBGroupBoxBBStdDevMultiplierTitle.setObjectName("IndicatorsTabMainBBGroupBoxBBStdDevMultiplierTitle")
        self.IndicatorsTabMainBBGroupBoxBBStdDevMultiplierTitle.setGeometry(QRect(10, 80, 111, 16))
        
        self.IndicatorsTabMainBBGroupBoxBBPeriodTextInput = QLineEdit(self.IndicatorsTabMainBBGroupBox)
        self.IndicatorsTabMainBBGroupBoxBBPeriodTextInput.setObjectName("IndicatorsTabMainBBGroupBoxBBPeriodTextInput")
        self.IndicatorsTabMainBBGroupBoxBBPeriodTextInput.setGeometry(QRect(145, 40, 51, 22))
        
        self.IndicatorsTabMainBBGroupBoxBBStdDevMultiplierTextInput = QLineEdit(self.IndicatorsTabMainBBGroupBox)
        self.IndicatorsTabMainBBGroupBoxBBStdDevMultiplierTextInput.setObjectName("IndicatorsTabMainBBGroupBoxBBStdDevMultiplierTextInput")
        self.IndicatorsTabMainBBGroupBoxBBStdDevMultiplierTextInput.setGeometry(QRect(145, 80, 51, 22))
        
        # MACD Group Box
        self.IndicatorsTabMainMACDGroupBox = QGroupBox(IndicatorsTabMain)
        self.IndicatorsTabMainMACDGroupBox.setObjectName("IndicatorsTabMainMACDGroupBox")
        self.IndicatorsTabMainMACDGroupBox.setGeometry(QRect(30, 290, 301, 121))
        
        self.IndicatorsTabMainMACDGroupBoxMACDLowTitle = QLabel(self.IndicatorsTabMainMACDGroupBox)
        self.IndicatorsTabMainMACDGroupBoxMACDLowTitle.setObjectName("IndicatorsTabMainMACDGroupBoxMACDLowTitle")
        self.IndicatorsTabMainMACDGroupBoxMACDLowTitle.setGeometry(QRect(10, 30, 121, 16))
        
        self.IndicatorsTabMainMACDGroupBoxMACDHighTitle = QLabel(self.IndicatorsTabMainMACDGroupBox)
        self.IndicatorsTabMainMACDGroupBoxMACDHighTitle.setObjectName("IndicatorsTabMainMACDGroupBoxMACDHighTitle")
        self.IndicatorsTabMainMACDGroupBoxMACDHighTitle.setGeometry(QRect(10, 60, 131, 16))
        
        self.IndicatorsTabMainMACDGroupBoxMACDPeriodTitle = QLabel(self.IndicatorsTabMainMACDGroupBox)
        self.IndicatorsTabMainMACDGroupBoxMACDPeriodTitle.setObjectName("IndicatorsTabMainMACDGroupBoxMACDPeriodTitle")
        self.IndicatorsTabMainMACDGroupBoxMACDPeriodTitle.setGeometry(QRect(10, 90, 141, 16))
        
        self.IndicatorsTabMainMACDGroupBoxMACDLowTextInput = QLineEdit(self.IndicatorsTabMainMACDGroupBox)
        self.IndicatorsTabMainMACDGroupBoxMACDLowTextInput.setObjectName("IndicatorsTabMainMACDGroupBoxMACDLowTextInput")
        self.IndicatorsTabMainMACDGroupBoxMACDLowTextInput.setGeometry(QRect(170, 30, 113, 22))
        
        self.IndicatorsTabMainMACDGroupBoxMACDHighTextInput = QLineEdit(self.IndicatorsTabMainMACDGroupBox)
        self.IndicatorsTabMainMACDGroupBoxMACDHighTextInput.setObjectName("IndicatorsTabMainMACDGroupBoxMACDHighTextInput")
        self.IndicatorsTabMainMACDGroupBoxMACDHighTextInput.setGeometry(QRect(170, 60, 113, 22))
        
        self.IndicatorsTabMainMACDGroupBoxMACDPeriodTextInput = QLineEdit(self.IndicatorsTabMainMACDGroupBox)
        self.IndicatorsTabMainMACDGroupBoxMACDPeriodTextInput.setObjectName("IndicatorsTabMainMACDGroupBoxMACDPeriodTextInput")
        self.IndicatorsTabMainMACDGroupBoxMACDPeriodTextInput.setGeometry(QRect(170, 90, 113, 22))
        
        # Ping Pong Group Box
        self.IndicatorsTabMainPingPongGroupBox = QGroupBox(IndicatorsTabMain)
        self.IndicatorsTabMainPingPongGroupBox.setObjectName("IndicatorsTabMainPingPongGroupBox")
        self.IndicatorsTabMainPingPongGroupBox.setGeometry(QRect(350, 290, 411, 121))
        
        self.IndicatorsTabMainPingPongGroupBoxText = QLabel(self.IndicatorsTabMainPingPongGroupBox)
        self.IndicatorsTabMainPingPongGroupBoxText.setObjectName("IndicatorsTabMainPingPongGroupBoxText")
        self.IndicatorsTabMainPingPongGroupBoxText.setGeometry(QRect(10, 20, 371, 51))
        self.IndicatorsTabMainPingPongGroupBoxText.setWordWrap(True)
        
        self.IndicatorsTabMainPingPongGroupBoxBuyPriceTitle = QLabel(self.IndicatorsTabMainPingPongGroupBox)
        self.IndicatorsTabMainPingPongGroupBoxBuyPriceTitle.setObjectName("IndicatorsTabMainPingPongGroupBoxBuyPriceTitle")
        self.IndicatorsTabMainPingPongGroupBoxBuyPriceTitle.setGeometry(QRect(10, 80, 51, 16))
        
        self.IndicatorsTabMainPingPongGroupBoxSellPriceTitle = QLabel(self.IndicatorsTabMainPingPongGroupBox)
        self.IndicatorsTabMainPingPongGroupBoxSellPriceTitle.setObjectName("IndicatorsTabMainPingPongGroupBoxSellPriceTitle")
        self.IndicatorsTabMainPingPongGroupBoxSellPriceTitle.setGeometry(QRect(180, 80, 49, 16))
        
        self.IndicatorsTabMainPingPongGroupBoxBuyPriceInput = QLineEdit(self.IndicatorsTabMainPingPongGroupBox)
        self.IndicatorsTabMainPingPongGroupBoxBuyPriceInput.setObjectName("IndicatorsTabMainPingPongGroupBoxBuyPriceInput")
        self.IndicatorsTabMainPingPongGroupBoxBuyPriceInput.setGeometry(QRect(80, 80, 81, 22))
        
        self.IndicatorsTabMainPingPongGroupBoxSellPriceInput = QLineEdit(self.IndicatorsTabMainPingPongGroupBox)
        self.IndicatorsTabMainPingPongGroupBoxSellPriceInput.setObjectName("IndicatorsTabMainPingPongGroupBoxSellPriceInput")
        self.IndicatorsTabMainPingPongGroupBoxSellPriceInput.setGeometry(QRect(242, 80, 81, 22))
        
        # Save As Default Settings Button
        self.IndicatorTabMainSaveAsDefaultSettingsButton = QPushButton(IndicatorsTabMain)
        self.IndicatorTabMainSaveAsDefaultSettingsButton.setObjectName("IndicatorTabMainSaveAsDefaultSettingsButton")
        self.IndicatorTabMainSaveAsDefaultSettingsButton.setGeometry(QRect(580, 440, 181, 71))
        
        self.retranslateUi(IndicatorsTabMain)
    
    def retranslateUi(self, IndicatorsTabMain):
        """Set all UI text/translations"""
        _translate = QCoreApplication.translate
        IndicatorsTabMain.setWindowTitle(_translate("AkondRadBotMainWindow", "Indicators"))
        
        self.IndicatorsTabMainAIStrategyGroupBox.setTitle(_translate("AkondRadBotMainWindow", "AI Strategy"))
        self.IndicatorsTabMainAIStrategyRSIPeriodTitle.setText(_translate("AkondRadBotMainWindow", "The AI Strategy uses its own settings which change over time dependent on market conditions. Read more about it in the help tab."))
        self.IndicatorsTabMainIndicatorsText.setText(_translate("AkondRadBotMainWindow", "These are the default indicator settings that will be used when you create trades using the RSI, MACross, BB or MACD indicators. Each trade can then be further fine tuned by editing it from the Active Trades 'Edit' page"))
        
        self.IndicatorsTabMainRSIGroupBox.setTitle(_translate("AkondRadBotMainWindow", "Relative Strength Index"))
        self.IndicatorsTabMainRSIGroupBoxRSILowValueTitle.setText(_translate("AkondRadBotMainWindow", "RSI Low Value"))
        self.IndicatorsTabMainRSIGroupBoxHighValueTitle.setText(_translate("AkondRadBotMainWindow", "RSI High Value"))
        self.IndicatorsTabMainRSIGroupBoxPeriodTitle.setText(_translate("AkondRadBotMainWindow", "RSI Period"))
        self.IndicatorsTabMainRSIGroupBoxLowValueTextInput.setText(_translate("AkondRadBotMainWindow", "30"))
        self.IndicatorsTabMainRSIGroupBoxHighValueTextInput.setText(_translate("AkondRadBotMainWindow", "70"))
        self.IndicatorsTabMainRSIGroupBoxPeriodTextInput.setText(_translate("AkondRadBotMainWindow", "14"))
        
        self.IndicatorsTabMainMACrossGroupBox.setTitle(_translate("AkondRadBotMainWindow", "Moving Average Crossover"))
        self.IndicatorsTabMainMACrossGroupBoxShortTimeTitle.setText(_translate("AkondRadBotMainWindow", "MA Cross Fast"))
        self.IndicatorsTabMainMACrossGroupBoxLongTimeTitle.setText(_translate("AkondRadBotMainWindow", "MA Cross Slow"))
        self.IndicatorsTabMainMACrossGroupBoxShortTimeTextInput.setText(_translate("AkondRadBotMainWindow", "8"))
        self.IndicatorsTabMainMACrossGroupBoxLongTimeTextInput.setText(_translate("AkondRadBotMainWindow", "22"))
        
        self.IndicatorsTabMainBBGroupBox.setTitle(_translate("AkondRadBotMainWindow", "Bollinger Bands"))
        self.IndicatorsTabMainBBGroupBoxBBPeriodTitle.setText(_translate("AkondRadBotMainWindow", "BB Period"))
        self.IndicatorsTabMainBBGroupBoxBBStdDevMultiplierTitle.setText(_translate("AkondRadBotMainWindow", "BB Std Dev Multiplier"))
        self.IndicatorsTabMainBBGroupBoxBBPeriodTextInput.setText(_translate("AkondRadBotMainWindow", "20"))
        self.IndicatorsTabMainBBGroupBoxBBStdDevMultiplierTextInput.setText(_translate("AkondRadBotMainWindow", "2"))
        
        self.IndicatorsTabMainMACDGroupBox.setTitle(_translate("AkondRadBotMainWindow", "Moving Average Convergence Divergence"))
        self.IndicatorsTabMainMACDGroupBoxMACDLowTitle.setText(_translate("AkondRadBotMainWindow", "MACD Fast Timeframe"))
        self.IndicatorsTabMainMACDGroupBoxMACDHighTitle.setText(_translate("AkondRadBotMainWindow", "MACD Slow Timeframe"))
        self.IndicatorsTabMainMACDGroupBoxMACDPeriodTitle.setText(_translate("AkondRadBotMainWindow", "MACD Signal Period"))
        self.IndicatorsTabMainMACDGroupBoxMACDLowTextInput.setText(_translate("AkondRadBotMainWindow", "12"))
        self.IndicatorsTabMainMACDGroupBoxMACDHighTextInput.setText(_translate("AkondRadBotMainWindow", "26"))
        self.IndicatorsTabMainMACDGroupBoxMACDPeriodTextInput.setText(_translate("AkondRadBotMainWindow", "9"))
        
        self.IndicatorsTabMainPingPongGroupBox.setTitle(_translate("AkondRadBotMainWindow", "Ping Pong"))
        self.IndicatorsTabMainPingPongGroupBoxText.setText(_translate(
            "AkondRadBotMainWindow",
            "<html><head/><body><p>A simple indicator that does best against stable markets, like stable coins. Prices need to be set on a per trade basis, not here. It buys and sells at set prices for known profit margins. Example; USDT &lt;-&gt; USDC</p></body></html>"
        ))
        self.IndicatorsTabMainPingPongGroupBoxBuyPriceTitle.setText(_translate("AkondRadBotMainWindow", "Buy Price"))
        self.IndicatorsTabMainPingPongGroupBoxSellPriceTitle.setText(_translate("AkondRadBotMainWindow", "Sell Price"))
        self.IndicatorsTabMainPingPongGroupBoxBuyPriceInput.setText(_translate("AkondRadBotMainWindow", "0.98"))
        self.IndicatorsTabMainPingPongGroupBoxSellPriceInput.setText(_translate("AkondRadBotMainWindow", "1.02"))
        
        self.IndicatorTabMainSaveAsDefaultSettingsButton.setText(_translate("AkondRadBotMainWindow", "Save As Default Settings"))
