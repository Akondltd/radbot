from PySide6.QtCore import (QCoreApplication, QDate, QDateTime, QLocale,
    QMetaObject, QObject, QPoint, QRect,
    QSize, QTime, QUrl, Qt)
from PySide6.QtGui import (QBrush, QColor, QConicalGradient, QCursor,
    QFont, QFontDatabase, QGradient, QIcon,
    QImage, QKeySequence, QLinearGradient, QPainter,
    QPalette, QPixmap, QRadialGradient, QTransform)
from PySide6.QtWidgets import (QApplication, QCheckBox, QDateTimeEdit, QFrame,
    QGraphicsView, QGroupBox, QHeaderView, QLabel,
    QLineEdit, QMainWindow, QPushButton, QRadioButton,
    QScrollArea, QSizePolicy, QStackedWidget, QTabWidget,
    QTextEdit, QTreeView, QWidget, QVBoxLayout, QHBoxLayout,
    QGridLayout, QFormLayout, QSpacerItem)

from gui.components.toggle_switch import ToggleSwitch

from gui import resources_rc

# Toggle between responsive layouts and legacy setGeometry positioning  
USE_RESPONSIVE_LAYOUTS = True  # Set True to enable responsive layouts

class Ui_CreateTradeTabMain(object):
    def setupUi(self, CreateTradeTabMain):
        if USE_RESPONSIVE_LAYOUTS:
            self._setupUi_responsive(CreateTradeTabMain)
        else:
            self._setupUi_legacy(CreateTradeTabMain)
        
        self.retranslateUi(CreateTradeTabMain)
    
    def _setupUi_responsive(self, CreateTradeTabMain):
        """Responsive layout implementation"""
        CreateTradeTabMain.setObjectName(u"CreateTradeTabMain")
        
        # Main layout for the tab
        main_layout = QVBoxLayout(CreateTradeTabMain)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # Fonts
        font = QFont()
        font.setBold(True)
        font1 = QFont()
        font1.setPointSize(10)
        font1.setBold(True)
        font1.setWeight(QFont.Weight.Bold)
        font3 = QFont()
        font3.setFamilies([u"Segoe UI"])
        font3.setPointSize(14)
        
        # Stacked Widget
        self.CreateTradeTabMenu = QStackedWidget()
        self.CreateTradeTabMenu.setObjectName(u"CreateTradeTabMenu")
        main_layout.addWidget(self.CreateTradeTabMenu)
        
        # PAGE 1: Configure Trade Pairs
        self._setup_page1_responsive(font, font1)
        
        # PAGE 2: Create Trade
        self._setup_page2_responsive(font, font1)
        
        # Set Create Trade page as default
        self.CreateTradeTabMenu.setCurrentIndex(1)
    
    def _setup_page1_responsive(self, font, font1):
        """Setup page 1 with responsive layouts"""
        self.ConfigTradePairsSubTab = QWidget()
        self.ConfigTradePairsSubTab.setObjectName(u"ConfigTradePairsSubTab")
        
        page1_layout = QVBoxLayout(self.ConfigTradePairsSubTab)
        page1_layout.setContentsMargins(10, 10, 10, 10)
        page1_layout.setSpacing(10)
        
        # Back button
        self.CreateTradeTabConfigureTradePairsBackButton = QPushButton(u"Back")
        self.CreateTradeTabConfigureTradePairsBackButton.setObjectName(u"CreateTradeTabConfigureTradePairsBackButton")
        self.CreateTradeTabConfigureTradePairsBackButton.setMaximumWidth(140)
        page1_layout.addWidget(self.CreateTradeTabConfigureTradePairsBackButton, 0, Qt.AlignmentFlag.AlignLeft)
        
        # Top text labels
        top_text_layout = QHBoxLayout()
        top_text_layout.setSpacing(10)
        
        self.CreateTradeTabConfigureTradePairsSubTabTextLabel = QLabel()
        self.CreateTradeTabConfigureTradePairsSubTabTextLabel.setObjectName(u"CreateTradeTabConfigureTradePairsSubTabTextLabel")
        self.CreateTradeTabConfigureTradePairsSubTabTextLabel.setWordWrap(True)
        self.CreateTradeTabConfigureTradePairsSubTabTextLabel.setMinimumHeight(155)
        top_text_layout.addWidget(self.CreateTradeTabConfigureTradePairsSubTabTextLabel, 1)
        
        self.CreateTradeTabConfigureTradePairsSubTabTextLabel2 = QLabel()
        self.CreateTradeTabConfigureTradePairsSubTabTextLabel2.setObjectName(u"CreateTradeTabConfigureTradePairsSubTabTextLabel2")
        self.CreateTradeTabConfigureTradePairsSubTabTextLabel2.setWordWrap(True)
        self.CreateTradeTabConfigureTradePairsSubTabTextLabel2.setMinimumHeight(155)
        top_text_layout.addWidget(self.CreateTradeTabConfigureTradePairsSubTabTextLabel2, 1)
        
        self.CreateTradeTabConfigureTradePairsSubTabTextLabel3 = QLabel()
        self.CreateTradeTabConfigureTradePairsSubTabTextLabel3.setObjectName(u"CreateTradeTabConfigureTradePairsSubTabTextLabel3")
        self.CreateTradeTabConfigureTradePairsSubTabTextLabel3.setWordWrap(True)
        self.CreateTradeTabConfigureTradePairsSubTabTextLabel3.setMinimumHeight(155)
        top_text_layout.addWidget(self.CreateTradeTabConfigureTradePairsSubTabTextLabel3, 1)
        
        page1_layout.addLayout(top_text_layout)
        
        # Main 3-column layout
        main_content_layout = QHBoxLayout()
        main_content_layout.setSpacing(10)
        
        # LEFT: Find Pools
        left_layout = QVBoxLayout()
        
        self.CreateTradeTabConfigureTradePairsFindPoolsTitleTab = QLabel(u"Find Pools:")
        self.CreateTradeTabConfigureTradePairsFindPoolsTitleTab.setObjectName(u"CreateTradeTabConfigureTradePairsFindPoolsTitleTab")
        left_layout.addWidget(self.CreateTradeTabConfigureTradePairsFindPoolsTitleTab)
        
        token_buttons = QHBoxLayout()
        self.CreateTradeTabConfigureTradePairsFindPoolsTokenAButton = QPushButton()
        self.CreateTradeTabConfigureTradePairsFindPoolsTokenAButton.setObjectName(u"CreateTradeTabConfigureTradePairsFindPoolsTokenAButton")
        self.CreateTradeTabConfigureTradePairsFindPoolsTokenAButton.setMinimumHeight(30)
        token_buttons.addWidget(self.CreateTradeTabConfigureTradePairsFindPoolsTokenAButton)
        
        self.CreateTradeTabConfigureTradePairsFindPoolsTokenBButton = QPushButton()
        self.CreateTradeTabConfigureTradePairsFindPoolsTokenBButton.setObjectName(u"CreateTradeTabConfigureTradePairsFindPoolsTokenBButton")
        self.CreateTradeTabConfigureTradePairsFindPoolsTokenBButton.setMinimumHeight(30)
        token_buttons.addWidget(self.CreateTradeTabConfigureTradePairsFindPoolsTokenBButton)
        left_layout.addLayout(token_buttons)
        
        self.CreateTradeTabConfigureTradePairsFindPoolsSearchButton = QPushButton()
        self.CreateTradeTabConfigureTradePairsFindPoolsSearchButton.setObjectName(u"CreateTradeTabConfigureTradePairsFindPoolsSearchButton")
        self.CreateTradeTabConfigureTradePairsFindPoolsSearchButton.setMinimumHeight(30)
        left_layout.addWidget(self.CreateTradeTabConfigureTradePairsFindPoolsSearchButton)
        
        self.CreateTradeTabConfigureTradePairsFindPoolsTextArea = QLabel()
        self.CreateTradeTabConfigureTradePairsFindPoolsTextArea.setObjectName(u"CreateTradeTabConfigureTradePairsFindPoolsTextArea")
        self.CreateTradeTabConfigureTradePairsFindPoolsTextArea.setWordWrap(True)
        left_layout.addWidget(self.CreateTradeTabConfigureTradePairsFindPoolsTextArea)
        
        self.CreateTradeTabConfigureTradePairsFindPoolsScrollArea = QScrollArea()
        self.CreateTradeTabConfigureTradePairsFindPoolsScrollArea.setObjectName(u"CreateTradeTabConfigureTradePairsFindPoolsScrollArea")
        self.CreateTradeTabConfigureTradePairsFindPoolsScrollArea.setWidgetResizable(True)
        self.scrollAreaWidgetContents_11 = QWidget()
        self.scrollAreaWidgetContents_11.setObjectName(u"scrollAreaWidgetContents_11")
        self.CreateTradeTabConfigureTradePairsFindPoolsScrollArea.setWidget(self.scrollAreaWidgetContents_11)
        left_layout.addWidget(self.CreateTradeTabConfigureTradePairsFindPoolsScrollArea, 1)
        
        main_content_layout.addLayout(left_layout, 3)
        
        # Arrow
        self.CreateTradeTabConfigureTradePairsSubTabRightArrowImage_2 = QLabel()
        self.CreateTradeTabConfigureTradePairsSubTabRightArrowImage_2.setObjectName(u"CreateTradeTabConfigureTradePairsSubTabRightArrowImage_2")
        self.CreateTradeTabConfigureTradePairsSubTabRightArrowImage_2.setPixmap(QPixmap(u":/images/images/right.png"))
        self.CreateTradeTabConfigureTradePairsSubTabRightArrowImage_2.setScaledContents(True)
        self.CreateTradeTabConfigureTradePairsSubTabRightArrowImage_2.setFixedSize(50, 50)
        main_content_layout.addWidget(self.CreateTradeTabConfigureTradePairsSubTabRightArrowImage_2, 0, Qt.AlignmentFlag.AlignCenter)
        
        # MIDDLE: Astrolescent
        middle_layout = QVBoxLayout()
        
        self.CreateTradeTabConfigureTradePairsSubTabAstrolescentTitleLabel = QLabel()
        self.CreateTradeTabConfigureTradePairsSubTabAstrolescentTitleLabel.setObjectName(u"CreateTradeTabConfigureTradePairsSubTabAstrolescentTitleLabel")
        middle_layout.addWidget(self.CreateTradeTabConfigureTradePairsSubTabAstrolescentTitleLabel)
        
        self.CreateTradeTabConfigureTradePairsSubTabAstrolescentScrollArea = QScrollArea()
        self.CreateTradeTabConfigureTradePairsSubTabAstrolescentScrollArea.setObjectName(u"CreateTradeTabConfigureTradePairsSubTabAstrolescentScrollArea")
        self.CreateTradeTabConfigureTradePairsSubTabAstrolescentScrollArea.setWidgetResizable(True)
        self.scrollAreaWidgetContents_8 = QWidget()
        self.scrollAreaWidgetContents_8.setObjectName(u"scrollAreaWidgetContents_8")
        self.CreateTradeTabConfigureTradePairsSubTabAstrolescentScrollArea.setWidget(self.scrollAreaWidgetContents_8)
        middle_layout.addWidget(self.CreateTradeTabConfigureTradePairsSubTabAstrolescentScrollArea, 1)
        
        main_content_layout.addLayout(middle_layout, 2)
        
        # Arrows vertical
        arrows_layout = QVBoxLayout()
        arrows_layout.addStretch()
        
        self.CreateTradeTabConfigureTradePairsSubTabRightArrowImage = QLabel()
        self.CreateTradeTabConfigureTradePairsSubTabRightArrowImage.setObjectName(u"CreateTradeTabConfigureTradePairsSubTabRightArrowImage")
        self.CreateTradeTabConfigureTradePairsSubTabRightArrowImage.setPixmap(QPixmap(u":/images/images/right.png"))
        self.CreateTradeTabConfigureTradePairsSubTabRightArrowImage.setScaledContents(True)
        self.CreateTradeTabConfigureTradePairsSubTabRightArrowImage.setFixedSize(50, 50)
        arrows_layout.addWidget(self.CreateTradeTabConfigureTradePairsSubTabRightArrowImage)
        
        arrows_layout.addSpacing(50)
        
        self.CreateTradeTabConfigureTradePairsSubTabLeftArrowImage = QLabel()
        self.CreateTradeTabConfigureTradePairsSubTabLeftArrowImage.setObjectName(u"CreateTradeTabConfigureTradePairsSubTabLeftArrowImage")
        self.CreateTradeTabConfigureTradePairsSubTabLeftArrowImage.setPixmap(QPixmap(u":/images/images/left.png"))
        self.CreateTradeTabConfigureTradePairsSubTabLeftArrowImage.setScaledContents(True)
        self.CreateTradeTabConfigureTradePairsSubTabLeftArrowImage.setFixedSize(50, 50)
        arrows_layout.addWidget(self.CreateTradeTabConfigureTradePairsSubTabLeftArrowImage)
        
        arrows_layout.addStretch()
        main_content_layout.addLayout(arrows_layout, 0)
        
        # RIGHT: RadBot
        right_layout = QVBoxLayout()
        
        self.CreateTradeTabConfigureTradePairsSubTabRadBotTitleLabel = QLabel()
        self.CreateTradeTabConfigureTradePairsSubTabRadBotTitleLabel.setObjectName(u"CreateTradeTabConfigureTradePairsSubTabRadBotTitleLabel")
        right_layout.addWidget(self.CreateTradeTabConfigureTradePairsSubTabRadBotTitleLabel)
        
        self.CreateTradeTabConfigureTradePairsSubTabRadBotScrollArea = QScrollArea()
        self.CreateTradeTabConfigureTradePairsSubTabRadBotScrollArea.setObjectName(u"CreateTradeTabConfigureTradePairsSubTabRadBotScrollArea")
        self.CreateTradeTabConfigureTradePairsSubTabRadBotScrollArea.setWidgetResizable(True)
        self.scrollAreaWidgetContents_9 = QWidget()
        self.scrollAreaWidgetContents_9.setObjectName(u"scrollAreaWidgetContents_9")
        self.CreateTradeTabConfigureTradePairsSubTabRadBotScrollArea.setWidget(self.scrollAreaWidgetContents_9)
        right_layout.addWidget(self.CreateTradeTabConfigureTradePairsSubTabRadBotScrollArea, 1)
        
        main_content_layout.addLayout(right_layout, 2)
        
        page1_layout.addLayout(main_content_layout, 1)
        
        self.CreateTradeTabMenu.addWidget(self.ConfigTradePairsSubTab)
    
    def _setup_page2_responsive(self, font, font1):
        """Setup page 2 with responsive layouts - FRAME ONE COMPLETE"""
        self.CreateTradeSubTab = QWidget()
        self.CreateTradeSubTab.setObjectName(u"CreateTradeSubTab")
        
        page2_layout = QVBoxLayout(self.CreateTradeSubTab)
        page2_layout.setContentsMargins(10, 10, 10, 10)
        page2_layout.setSpacing(5)
        
        # Font for tooltips
        font3 = QFont()
        font3.setFamilies([u"Segoe UI"])
        font3.setPointSize(14)
        
        # ====== FRAME ONE: Main Trade Configuration ======
        self.CreateTradeTabMainCreateTradeSubTabFrameOne = QFrame()
        self.CreateTradeTabMainCreateTradeSubTabFrameOne.setObjectName(u"CreateTradeTabMainCreateTradeSubTabFrameOne")
        self.CreateTradeTabMainCreateTradeSubTabFrameOne.setFrameShape(QFrame.Shape.StyledPanel)
        self.CreateTradeTabMainCreateTradeSubTabFrameOne.setLineWidth(2)
        self.CreateTradeTabMainCreateTradeSubTabFrameOne.setMinimumHeight(155)
        
        frame_one_layout = QGridLayout(self.CreateTradeTabMainCreateTradeSubTabFrameOne)
        frame_one_layout.setContentsMargins(10, 5, 10, 5)  # Reduced vertical margins
        frame_one_layout.setSpacing(5)  # Reduced spacing
        
        # Set column stretch factors: 34%, 1% space, 30%, 1% space, 34%
        frame_one_layout.setColumnStretch(0, 34)  # Left column
        frame_one_layout.setColumnStretch(1, 1)   # Spacer
        frame_one_layout.setColumnStretch(2, 15)  # Middle column (spans 2 for toggles)
        frame_one_layout.setColumnStretch(3, 15)  # Middle column continuation
        frame_one_layout.setColumnStretch(4, 1)   # Spacer
        frame_one_layout.setColumnStretch(5, 34)  # Right column
        
        # LEFT COLUMN: Trade Pair Selection (col 0)
        self.CreateTradeTabMainCreateTradeSubTabSelectTradePairTitle = QLabel()
        self.CreateTradeTabMainCreateTradeSubTabSelectTradePairTitle.setObjectName(u"CreateTradeTabMainCreateTradeSubTabSelectTradePairTitle")
        frame_one_layout.addWidget(self.CreateTradeTabMainCreateTradeSubTabSelectTradePairTitle, 0, 0, 1, 1)
        
        self.CreateTradeTabMainCreateTradeSubTabSelectTradePairScrollArea = QScrollArea()
        self.CreateTradeTabMainCreateTradeSubTabSelectTradePairScrollArea.setObjectName(u"CreateTradeTabMainCreateTradeSubTabSelectTradePairScrollArea")
        self.CreateTradeTabMainCreateTradeSubTabSelectTradePairScrollArea.setWidgetResizable(True)
        self.scrollAreaWidgetContents_10 = QWidget()
        self.scrollAreaWidgetContents_10.setObjectName(u"scrollAreaWidgetContents_10")
        self.CreateTradeTabMainCreateTradeSubTabSelectTradePairScrollArea.setWidget(self.scrollAreaWidgetContents_10)
        frame_one_layout.addWidget(self.CreateTradeTabMainCreateTradeSubTabSelectTradePairScrollArea, 1, 0, 4, 1)
        
        # MIDDLE COLUMN: Current Prices & Token Selection (col 2-3, skip col 1 for spacing)
        self.CreateTradeTabMainCreateTradeSubTabCurrentPricesTitle = QLabel()
        self.CreateTradeTabMainCreateTradeSubTabCurrentPricesTitle.setObjectName(u"CreateTradeTabMainCreateTradeSubTabCurrentPricesTitle")
        self.CreateTradeTabMainCreateTradeSubTabCurrentPricesTitle.setFont(font)
        frame_one_layout.addWidget(self.CreateTradeTabMainCreateTradeSubTabCurrentPricesTitle, 0, 2, 1, 2)
        
        self.CreateTradeTabMainCreateTradeSubTabCurrentPricesTextOne = QLabel()
        self.CreateTradeTabMainCreateTradeSubTabCurrentPricesTextOne.setObjectName(u"CreateTradeTabMainCreateTradeSubTabCurrentPricesTextOne")
        self.CreateTradeTabMainCreateTradeSubTabCurrentPricesTextOne.setAlignment(Qt.AlignmentFlag.AlignCenter)
        frame_one_layout.addWidget(self.CreateTradeTabMainCreateTradeSubTabCurrentPricesTextOne, 1, 2, 1, 2)
        
        self.CreateTradeTabMainCreateTradeSubTabCurrentPricesTextTwo = QLabel()
        self.CreateTradeTabMainCreateTradeSubTabCurrentPricesTextTwo.setObjectName(u"CreateTradeTabMainCreateTradeSubTabCurrentPricesTextTwo")
        self.CreateTradeTabMainCreateTradeSubTabCurrentPricesTextTwo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        frame_one_layout.addWidget(self.CreateTradeTabMainCreateTradeSubTabCurrentPricesTextTwo, 2, 2, 1, 2)
        
        # Start Token Toggle Switch
        start_token_container = QVBoxLayout()
        self.CreateTradeTabMainCreateTradeSubTabStartTokenTitle = QLabel()
        self.CreateTradeTabMainCreateTradeSubTabStartTokenTitle.setObjectName(u"CreateTradeTabMainCreateTradeSubTabStartTokenTitle")
        start_token_container.addWidget(self.CreateTradeTabMainCreateTradeSubTabStartTokenTitle)
        
        self.CreateTradeTabMainCreateTradeSubTabStartTokenToggle = ToggleSwitch(left_text="Token 1", right_text="Token 2")
        self.CreateTradeTabMainCreateTradeSubTabStartTokenToggle.setObjectName(u"CreateTradeTabMainCreateTradeSubTabStartTokenToggle")
        start_token_container.addWidget(self.CreateTradeTabMainCreateTradeSubTabStartTokenToggle)
        frame_one_layout.addLayout(start_token_container, 3, 2, 1, 1)
        
        # Accumulate Token Toggle Switch
        accumulate_token_container = QVBoxLayout()
        self.CreateTradeTabMainCreateTradeSubTabAccumulateTokenTitle = QLabel()
        self.CreateTradeTabMainCreateTradeSubTabAccumulateTokenTitle.setObjectName(u"CreateTradeTabMainCreateTradeSubTabAccumulateTokenTitle")
        accumulate_token_container.addWidget(self.CreateTradeTabMainCreateTradeSubTabAccumulateTokenTitle)
        
        self.CreateTradeTabMainCreateTradeSubTabAccumulateTokenToggle = ToggleSwitch(left_text="Token 1", right_text="Token 2")
        self.CreateTradeTabMainCreateTradeSubTabAccumulateTokenToggle.setObjectName(u"CreateTradeTabMainCreateTradeSubTabAccumulateTokenToggle")
        accumulate_token_container.addWidget(self.CreateTradeTabMainCreateTradeSubTabAccumulateTokenToggle)
        frame_one_layout.addLayout(accumulate_token_container, 3, 3, 1, 1)
        
        # Configure Trade Pairs Button (bottom center)
        self.CreateTradeTabMainCreateTradeSubTabConfigureTradePairsButton = QPushButton()
        self.CreateTradeTabMainCreateTradeSubTabConfigureTradePairsButton.setObjectName(u"CreateTradeTabMainCreateTradeSubTabConfigureTradePairsButton")
        self.CreateTradeTabMainCreateTradeSubTabConfigureTradePairsButton.setMinimumHeight(30)
        frame_one_layout.addWidget(self.CreateTradeTabMainCreateTradeSubTabConfigureTradePairsButton, 4, 2, 1, 2)
        
        # RIGHT COLUMN: Token Amount & Stops (col 5, skip col 4 for spacing)
        # Title at row 0 to align with other columns
        self.CreateTradeTabMainCreateTradeSubTabTradeTokenAmountTitle = QLabel()
        self.CreateTradeTabMainCreateTradeSubTabTradeTokenAmountTitle.setObjectName(u"CreateTradeTabMainCreateTradeSubTabTradeTokenAmountTitle")
        frame_one_layout.addWidget(self.CreateTradeTabMainCreateTradeSubTabTradeTokenAmountTitle, 0, 5, 1, 1)
        
        # Content container starting at row 1
        trade_amount_container = QVBoxLayout()
        
        self.CreateTradeTabMainCreateTradeSubTabTradeTokenAmountText = QLabel()
        self.CreateTradeTabMainCreateTradeSubTabTradeTokenAmountText.setObjectName(u"CreateTradeTabMainCreateTradeSubTabTradeTokenAmountText")
        self.CreateTradeTabMainCreateTradeSubTabTradeTokenAmountText.setWordWrap(True)
        self.CreateTradeTabMainCreateTradeSubTabTradeTokenAmountText.setMaximumHeight(30)
        trade_amount_container.addWidget(self.CreateTradeTabMainCreateTradeSubTabTradeTokenAmountText)
        
        self.CreateTradeTabMainCreateTradeSubTabTradeTokenAmountField = QLineEdit()
        self.CreateTradeTabMainCreateTradeSubTabTradeTokenAmountField.setObjectName(u"CreateTradeTabMainCreateTradeSubTabTradeTokenAmountField")
        trade_amount_container.addWidget(self.CreateTradeTabMainCreateTradeSubTabTradeTokenAmountField)
        
        # Stop Loss and Trailing Stop in 50/50 side-by-side layout
        stops_container = QHBoxLayout()
        stops_container.setSpacing(10)
        
        # LEFT 50%: Stop Loss
        stoploss_column = QVBoxLayout()
        stoploss_row = QHBoxLayout()
        self.CreateTradeTabMainCreateTradeSubTabStopLossTitle = QLabel()
        self.CreateTradeTabMainCreateTradeSubTabStopLossTitle.setObjectName(u"CreateTradeTabMainCreateTradeSubTabStopLossTitle")
        stoploss_row.addWidget(self.CreateTradeTabMainCreateTradeSubTabStopLossTitle)
        
        stoploss_row.addStretch()  # Add space between label and input
        
        self.CreateTradeTabMainCreateTradeSubTabStopLossInput = QLineEdit()
        self.CreateTradeTabMainCreateTradeSubTabStopLossInput.setObjectName(u"CreateTradeTabMainCreateTradeSubTabStopLossInput")
        self.CreateTradeTabMainCreateTradeSubTabStopLossInput.setMaximumWidth(40)
        self.CreateTradeTabMainCreateTradeSubTabStopLossInput.setAlignment(Qt.AlignmentFlag.AlignRight|Qt.AlignmentFlag.AlignTrailing|Qt.AlignmentFlag.AlignVCenter)
        stoploss_row.addWidget(self.CreateTradeTabMainCreateTradeSubTabStopLossInput)
        
        self.CreateTradeTabMainCreateTradeSubTabStopLossText = QLabel(u"%")
        self.CreateTradeTabMainCreateTradeSubTabStopLossText.setObjectName(u"CreateTradeTabMainCreateTradeSubTabStopLossText")
        stoploss_row.addWidget(self.CreateTradeTabMainCreateTradeSubTabStopLossText)
        stoploss_column.addLayout(stoploss_row)
        
        # Trailing Stop (below Stop Loss in same column)
        trailingstop_row = QHBoxLayout()
        self.CreateTradeTabMainCreateTradeSubTabTrailingStopTitle = QLabel()
        self.CreateTradeTabMainCreateTradeSubTabTrailingStopTitle.setObjectName(u"CreateTradeTabMainCreateTradeSubTabTrailingStopTitle")
        trailingstop_row.addWidget(self.CreateTradeTabMainCreateTradeSubTabTrailingStopTitle)
        
        trailingstop_row.addStretch()  # Add space between label and input
        
        self.CreateTradeTabMainCreateTradeSubTabTrailingStopInput = QLineEdit()
        self.CreateTradeTabMainCreateTradeSubTabTrailingStopInput.setObjectName(u"CreateTradeTabMainCreateTradeSubTabTrailingStopInput")
        self.CreateTradeTabMainCreateTradeSubTabTrailingStopInput.setMaximumWidth(40)
        self.CreateTradeTabMainCreateTradeSubTabTrailingStopInput.setAlignment(Qt.AlignmentFlag.AlignRight|Qt.AlignmentFlag.AlignTrailing|Qt.AlignmentFlag.AlignVCenter)
        trailingstop_row.addWidget(self.CreateTradeTabMainCreateTradeSubTabTrailingStopInput)
        
        self.CreateTradeTabMainCreateTradeSubTabTrailingStopText = QLabel(u"%")
        self.CreateTradeTabMainCreateTradeSubTabTrailingStopText.setObjectName(u"CreateTradeTabMainCreateTradeSubTabTrailingStopText")
        trailingstop_row.addWidget(self.CreateTradeTabMainCreateTradeSubTabTrailingStopText)
        stoploss_column.addLayout(trailingstop_row)
        
        stops_container.addLayout(stoploss_column, 1)  # Left 50%
        
        # RIGHT 50%: Info tooltip and disabled text (aligned with Stop Loss row)
        info_column = QVBoxLayout()
        info_row = QHBoxLayout()
        
        self.CreateTradeTabMainCreateTradeSubTabStopsTooltip = QLabel()
        self.CreateTradeTabMainCreateTradeSubTabStopsTooltip.setObjectName(u"CreateTradeTabMainCreateTradeSubTabStopsTooltip")
        self.CreateTradeTabMainCreateTradeSubTabStopsTooltip.setFont(font3)
        self.CreateTradeTabMainCreateTradeSubTabStopsTooltip.setMaximumWidth(21)
        info_row.addWidget(self.CreateTradeTabMainCreateTradeSubTabStopsTooltip)
        
        self.CreateTradeTabMainCreateTradeSubTabStopsText = QLabel()
        self.CreateTradeTabMainCreateTradeSubTabStopsText.setObjectName(u"CreateTradeTabMainCreateTradeSubTabStopsText")
        info_row.addWidget(self.CreateTradeTabMainCreateTradeSubTabStopsText)
        info_row.addStretch()
        info_column.addLayout(info_row)
        info_column.addStretch()  # Empty space below for second row
        
        stops_container.addLayout(info_column, 1)  # Right 50%
        
        trade_amount_container.addLayout(stops_container)
        
        # Add stretch to push content to top
        trade_amount_container.addStretch()
        
        frame_one_layout.addLayout(trade_amount_container, 1, 5, 4, 1)
        
        page2_layout.addWidget(self.CreateTradeTabMainCreateTradeSubTabFrameOne)
        
        # Add expanding spacer between top frame and indicators section
        page2_layout.addItem(QSpacerItem(20, 20, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding))
        
        # ====== INDICATORS SECTION ======
        # Title row with label_7 on the right
        indicators_title_row = QHBoxLayout()
        self.CreateTradeTabMainCreateTradeSubTabSelectTradeIndicatorsTitle = QLabel()
        self.CreateTradeTabMainCreateTradeSubTabSelectTradeIndicatorsTitle.setObjectName(u"CreateTradeTabMainCreateTradeSubTabSelectTradeIndicatorsTitle")
        indicators_title_row.addWidget(self.CreateTradeTabMainCreateTradeSubTabSelectTradeIndicatorsTitle)
        
        self.label_7 = QLabel()
        self.label_7.setObjectName(u"label_7")
        indicators_title_row.addWidget(self.label_7)
        indicators_title_row.addStretch()
        
        page2_layout.addLayout(indicators_title_row)
        
        self.CreateTradeTabMainCreateTradeSubTabSelectTradeIndicatorsTextOne = QLabel()
        self.CreateTradeTabMainCreateTradeSubTabSelectTradeIndicatorsTextOne.setObjectName(u"CreateTradeTabMainCreateTradeSubTabSelectTradeIndicatorsTextOne")
        self.CreateTradeTabMainCreateTradeSubTabSelectTradeIndicatorsTextOne.setWordWrap(True)
        page2_layout.addWidget(self.CreateTradeTabMainCreateTradeSubTabSelectTradeIndicatorsTextOne)
        
        # Indicator frames in 2x2 grid
        indicators_grid = QGridLayout()
        indicators_grid.setSpacing(10)
        
        # RSI Frame (row 0, col 0)
        self.CreateTradeTabMainCreateTradeSubTabRSIFrame = QFrame()
        self.CreateTradeTabMainCreateTradeSubTabRSIFrame.setObjectName(u"CreateTradeTabMainCreateTradeSubTabRSIFrame")
        self.CreateTradeTabMainCreateTradeSubTabRSIFrame.setFrameShape(QFrame.Shape.StyledPanel)
        self.CreateTradeTabMainCreateTradeSubTabRSIFrame.setMinimumHeight(32)
        self.CreateTradeTabMainCreateTradeSubTabRSIFrame.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        rsi_layout = QHBoxLayout(self.CreateTradeTabMainCreateTradeSubTabRSIFrame)
        rsi_layout.setContentsMargins(5, 0, 5, 0)
        
        self.CreateTradeTabMainCreateTradeSubTabRSICheckbox = QCheckBox()
        self.CreateTradeTabMainCreateTradeSubTabRSICheckbox.setObjectName(u"CreateTradeTabMainCreateTradeSubTabRSICheckbox")
        self.CreateTradeTabMainCreateTradeSubTabRSICheckbox.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        rsi_layout.addWidget(self.CreateTradeTabMainCreateTradeSubTabRSICheckbox, 1)
        
        self.CreateTradeTabMainCreateTradeSubTabRSIInfoTooltip = QLabel()
        self.CreateTradeTabMainCreateTradeSubTabRSIInfoTooltip.setObjectName(u"CreateTradeTabMainCreateTradeSubTabRSIInfoTooltip")
        self.CreateTradeTabMainCreateTradeSubTabRSIInfoTooltip.setFont(font3)
        self.CreateTradeTabMainCreateTradeSubTabRSIInfoTooltip.setMaximumWidth(21)
        rsi_layout.addWidget(self.CreateTradeTabMainCreateTradeSubTabRSIInfoTooltip)
        
        indicators_grid.addWidget(self.CreateTradeTabMainCreateTradeSubTabRSIFrame, 0, 0)
        
        # MACD Frame (row 0, col 1)
        self.CreateTradeTabMainCreateTradeSubTabMACDFrame = QFrame()
        self.CreateTradeTabMainCreateTradeSubTabMACDFrame.setObjectName(u"CreateTradeTabMainCreateTradeSubTabMACDFrame")
        self.CreateTradeTabMainCreateTradeSubTabMACDFrame.setFrameShape(QFrame.Shape.StyledPanel)
        self.CreateTradeTabMainCreateTradeSubTabMACDFrame.setMinimumHeight(32)
        self.CreateTradeTabMainCreateTradeSubTabMACDFrame.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        macd_layout = QHBoxLayout(self.CreateTradeTabMainCreateTradeSubTabMACDFrame)
        macd_layout.setContentsMargins(5, 0, 5, 0)
        
        self.CreateTradeTabMainCreateTradeSubTabMACDCheckbox = QCheckBox()
        self.CreateTradeTabMainCreateTradeSubTabMACDCheckbox.setObjectName(u"CreateTradeTabMainCreateTradeSubTabMACDCheckbox")
        self.CreateTradeTabMainCreateTradeSubTabMACDCheckbox.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.CreateTradeTabMainCreateTradeSubTabMACDCheckbox.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        macd_layout.addWidget(self.CreateTradeTabMainCreateTradeSubTabMACDCheckbox, 1)
        
        self.CreateTradeTabMainCreateTradeSubTabMACDInfoTooltip = QLabel()
        self.CreateTradeTabMainCreateTradeSubTabMACDInfoTooltip.setObjectName(u"CreateTradeTabMainCreateTradeSubTabMACDInfoTooltip")
        self.CreateTradeTabMainCreateTradeSubTabMACDInfoTooltip.setFont(font3)
        self.CreateTradeTabMainCreateTradeSubTabMACDInfoTooltip.setMaximumWidth(21)
        macd_layout.addWidget(self.CreateTradeTabMainCreateTradeSubTabMACDInfoTooltip)
        
        indicators_grid.addWidget(self.CreateTradeTabMainCreateTradeSubTabMACDFrame, 0, 1)
        
        # MAC Frame (row 1, col 0)
        self.CreateTradeTabMainCreateTradeSubTabMACFrame = QFrame()
        self.CreateTradeTabMainCreateTradeSubTabMACFrame.setObjectName(u"CreateTradeTabMainCreateTradeSubTabMACFrame")
        self.CreateTradeTabMainCreateTradeSubTabMACFrame.setFrameShape(QFrame.Shape.StyledPanel)
        self.CreateTradeTabMainCreateTradeSubTabMACFrame.setMinimumHeight(32)
        self.CreateTradeTabMainCreateTradeSubTabMACFrame.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        mac_layout = QHBoxLayout(self.CreateTradeTabMainCreateTradeSubTabMACFrame)
        mac_layout.setContentsMargins(5, 0, 5, 0)
        
        self.CreateTradeTabMainCreateTradeSubTabMACCheckbox = QCheckBox()
        self.CreateTradeTabMainCreateTradeSubTabMACCheckbox.setObjectName(u"CreateTradeTabMainCreateTradeSubTabMACCheckbox")
        self.CreateTradeTabMainCreateTradeSubTabMACCheckbox.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.CreateTradeTabMainCreateTradeSubTabMACCheckbox.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        mac_layout.addWidget(self.CreateTradeTabMainCreateTradeSubTabMACCheckbox, 1)
        
        self.CreateTradeTabMainCreateTradeSubTabMACInfoTooltip = QLabel()
        self.CreateTradeTabMainCreateTradeSubTabMACInfoTooltip.setObjectName(u"CreateTradeTabMainCreateTradeSubTabMACInfoTooltip")
        self.CreateTradeTabMainCreateTradeSubTabMACInfoTooltip.setFont(font3)
        self.CreateTradeTabMainCreateTradeSubTabMACInfoTooltip.setMaximumWidth(21)
        mac_layout.addWidget(self.CreateTradeTabMainCreateTradeSubTabMACInfoTooltip)
        
        indicators_grid.addWidget(self.CreateTradeTabMainCreateTradeSubTabMACFrame, 1, 0)
        
        # BB Frame (row 1, col 1)
        self.CreateTradeTabMainCreateTradeSubTabBBFrame = QFrame()
        self.CreateTradeTabMainCreateTradeSubTabBBFrame.setObjectName(u"CreateTradeTabMainCreateTradeSubTabBBFrame")
        self.CreateTradeTabMainCreateTradeSubTabBBFrame.setFrameShape(QFrame.Shape.StyledPanel)
        self.CreateTradeTabMainCreateTradeSubTabBBFrame.setMinimumHeight(32)
        self.CreateTradeTabMainCreateTradeSubTabBBFrame.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        bb_layout = QHBoxLayout(self.CreateTradeTabMainCreateTradeSubTabBBFrame)
        bb_layout.setContentsMargins(5, 0, 5, 0)
        
        self.CreateTradeTabMainCreateTradeSubTabBBCheckbox = QCheckBox()
        self.CreateTradeTabMainCreateTradeSubTabBBCheckbox.setObjectName(u"CreateTradeTabMainCreateTradeSubTabBBCheckbox")
        self.CreateTradeTabMainCreateTradeSubTabBBCheckbox.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.CreateTradeTabMainCreateTradeSubTabBBCheckbox.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        bb_layout.addWidget(self.CreateTradeTabMainCreateTradeSubTabBBCheckbox, 1)
        
        self.CreateTradeTabMainCreateTradeSubTabBBInfoTooltip = QLabel()
        self.CreateTradeTabMainCreateTradeSubTabBBInfoTooltip.setObjectName(u"CreateTradeTabMainCreateTradeSubTabBBInfoTooltip")
        self.CreateTradeTabMainCreateTradeSubTabBBInfoTooltip.setFont(font3)
        self.CreateTradeTabMainCreateTradeSubTabBBInfoTooltip.setMaximumWidth(21)
        bb_layout.addWidget(self.CreateTradeTabMainCreateTradeSubTabBBInfoTooltip)
        
        indicators_grid.addWidget(self.CreateTradeTabMainCreateTradeSubTabBBFrame, 1, 1)
        
        page2_layout.addLayout(indicators_grid)
        
        # Add expanding spacer between indicators and strategies section
        page2_layout.addItem(QSpacerItem(20, 20, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding))
        
        # ====== STRATEGY SECTION ======
        # Title row with label on the right
        strategy_title_row = QHBoxLayout()
        self.label_4 = QLabel()
        self.label_4.setObjectName(u"label_4")
        strategy_title_row.addWidget(self.label_4)
        
        self.label = QLabel()
        self.label.setObjectName(u"label")
        strategy_title_row.addWidget(self.label)
        strategy_title_row.addStretch()
        
        page2_layout.addLayout(strategy_title_row)
        
        self.label_2 = QLabel()
        self.label_2.setObjectName(u"label_2")
        self.label_2.setWordWrap(True)
        page2_layout.addWidget(self.label_2)
        
        # Strategy frames row (AI Strategy and Ping Pong in two columns)
        strategy_frames_row = QHBoxLayout()
        strategy_frames_row.setSpacing(10)
        
        # LEFT COLUMN: AI Strategy at top with spacer below
        left_column = QVBoxLayout()
        left_column.setSpacing(0)
        
        # AI Strategy Frame (fixed 32px height)
        self.CreateTradeTabMainCreateTradeSubTabAIStrategyFrame = QFrame()
        self.CreateTradeTabMainCreateTradeSubTabAIStrategyFrame.setObjectName(u"CreateTradeTabMainCreateTradeSubTabAIStrategyFrame")
        self.CreateTradeTabMainCreateTradeSubTabAIStrategyFrame.setFrameShape(QFrame.Shape.StyledPanel)
        self.CreateTradeTabMainCreateTradeSubTabAIStrategyFrame.setMinimumHeight(32)
        self.CreateTradeTabMainCreateTradeSubTabAIStrategyFrame.setMaximumHeight(32)
        self.CreateTradeTabMainCreateTradeSubTabAIStrategyFrame.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        ai_strategy_layout = QHBoxLayout(self.CreateTradeTabMainCreateTradeSubTabAIStrategyFrame)
        ai_strategy_layout.setContentsMargins(5, 0, 5, 0)
        
        self.CreateTradeTabMainCreateTradeSubTabAIStrategyCheckbox = QCheckBox()
        self.CreateTradeTabMainCreateTradeSubTabAIStrategyCheckbox.setObjectName(u"CreateTradeTabMainCreateTradeSubTabAIStrategyCheckbox")
        self.CreateTradeTabMainCreateTradeSubTabAIStrategyCheckbox.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        ai_strategy_layout.addWidget(self.CreateTradeTabMainCreateTradeSubTabAIStrategyCheckbox, 1)
        
        self.CreateTradeTabMainCreateTradeSubTabAIStrategyTooltip = QLabel()
        self.CreateTradeTabMainCreateTradeSubTabAIStrategyTooltip.setObjectName(u"CreateTradeTabMainCreateTradeSubTabAIStrategyTooltip")
        self.CreateTradeTabMainCreateTradeSubTabAIStrategyTooltip.setFont(font3)
        self.CreateTradeTabMainCreateTradeSubTabAIStrategyTooltip.setMaximumWidth(21)
        ai_strategy_layout.addWidget(self.CreateTradeTabMainCreateTradeSubTabAIStrategyTooltip)
        
        left_column.addWidget(self.CreateTradeTabMainCreateTradeSubTabAIStrategyFrame)
        
        # Add spacer below AI Strategy (38px expanding)
        left_column.addItem(QSpacerItem(20, 38, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding))
        
        strategy_frames_row.addLayout(left_column, 1)  # 50% width
        
        # Ping Pong Frame
        self.CreateTradeTabMainCreateTradeSubTabPingPongFrame = QFrame()
        self.CreateTradeTabMainCreateTradeSubTabPingPongFrame.setObjectName(u"CreateTradeTabMainCreateTradeSubTabPingPongFrame")
        self.CreateTradeTabMainCreateTradeSubTabPingPongFrame.setFrameShape(QFrame.Shape.StyledPanel)
        self.CreateTradeTabMainCreateTradeSubTabPingPongFrame.setMinimumHeight(70)
        self.CreateTradeTabMainCreateTradeSubTabPingPongFrame.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        pingpong_main_layout = QVBoxLayout(self.CreateTradeTabMainCreateTradeSubTabPingPongFrame)
        pingpong_main_layout.setContentsMargins(5, 5, 5, 5)
        pingpong_main_layout.setSpacing(5)
        
        # Top row: checkbox and tooltip
        pingpong_top_row = QHBoxLayout()
        pingpong_top_row.setContentsMargins(0, 0, 0, 0)
        
        self.CreateTradeTabMainCreateTradeSubTabPingPongCheckbox = QCheckBox()
        self.CreateTradeTabMainCreateTradeSubTabPingPongCheckbox.setObjectName(u"CreateTradeTabMainCreateTradeSubTabPingPongCheckbox")
        self.CreateTradeTabMainCreateTradeSubTabPingPongCheckbox.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        pingpong_top_row.addWidget(self.CreateTradeTabMainCreateTradeSubTabPingPongCheckbox, 1)
        
        self.CreateTradeTabMainCreateTradeSubTabPingPongInfoTooltip = QLabel()
        self.CreateTradeTabMainCreateTradeSubTabPingPongInfoTooltip.setObjectName(u"CreateTradeTabMainCreateTradeSubTabPingPongInfoTooltip")
        self.CreateTradeTabMainCreateTradeSubTabPingPongInfoTooltip.setFont(font3)
        self.CreateTradeTabMainCreateTradeSubTabPingPongInfoTooltip.setMaximumWidth(21)
        pingpong_top_row.addWidget(self.CreateTradeTabMainCreateTradeSubTabPingPongInfoTooltip)
        
        pingpong_main_layout.addLayout(pingpong_top_row)
        
        # Bottom row: price fields
        pingpong_price_row = QHBoxLayout()
        pingpong_price_row.setSpacing(10)
        
        self.CreateTradeTabMainCreateTradeSubTabPingPongBuyPriceTitle = QLabel()
        self.CreateTradeTabMainCreateTradeSubTabPingPongBuyPriceTitle.setObjectName(u"CreateTradeTabMainCreateTradeSubTabPingPongBuyPriceTitle")
        pingpong_price_row.addWidget(self.CreateTradeTabMainCreateTradeSubTabPingPongBuyPriceTitle)
        
        self.CreateTradeTabMainCreateTradeSubTabPingPongBuyPriceField = QLineEdit()
        self.CreateTradeTabMainCreateTradeSubTabPingPongBuyPriceField.setObjectName(u"CreateTradeTabMainCreateTradeSubTabPingPongBuyPriceField")
        self.CreateTradeTabMainCreateTradeSubTabPingPongBuyPriceField.setMaximumWidth(80)
        pingpong_price_row.addWidget(self.CreateTradeTabMainCreateTradeSubTabPingPongBuyPriceField)
        
        self.CreateTradeTabMainCreateTradeSubTabPingPongBuyPriceSymbol = QLabel()
        self.CreateTradeTabMainCreateTradeSubTabPingPongBuyPriceSymbol.setObjectName(u"CreateTradeTabMainCreateTradeSubTabPingPongBuyPriceSymbol")
        pingpong_price_row.addWidget(self.CreateTradeTabMainCreateTradeSubTabPingPongBuyPriceSymbol)
        
        pingpong_price_row.addSpacing(20)
        
        self.CreateTradeTabMainCreateTradeSubTabPingPongSellPriceTitle = QLabel()
        self.CreateTradeTabMainCreateTradeSubTabPingPongSellPriceTitle.setObjectName(u"CreateTradeTabMainCreateTradeSubTabPingPongSellPriceTitle")
        pingpong_price_row.addWidget(self.CreateTradeTabMainCreateTradeSubTabPingPongSellPriceTitle)
        
        self.CreateTradeTabMainCreateTradeSubTabPingPongSellPriceField = QLineEdit()
        self.CreateTradeTabMainCreateTradeSubTabPingPongSellPriceField.setObjectName(u"CreateTradeTabMainCreateTradeSubTabPingPongSellPriceField")
        self.CreateTradeTabMainCreateTradeSubTabPingPongSellPriceField.setMaximumWidth(80)
        pingpong_price_row.addWidget(self.CreateTradeTabMainCreateTradeSubTabPingPongSellPriceField)
        
        self.CreateTradeTabMainCreateTradeSubTabPingPongSellPriceSymbol = QLabel()
        self.CreateTradeTabMainCreateTradeSubTabPingPongSellPriceSymbol.setObjectName(u"CreateTradeTabMainCreateTradeSubTabPingPongSellPriceSymbol")
        pingpong_price_row.addWidget(self.CreateTradeTabMainCreateTradeSubTabPingPongSellPriceSymbol)
        
        pingpong_price_row.addStretch()
        pingpong_main_layout.addLayout(pingpong_price_row)
        
        # RIGHT COLUMN: Ping Pong takes full height (50% width)
        strategy_frames_row.addWidget(self.CreateTradeTabMainCreateTradeSubTabPingPongFrame, 1)
        
        page2_layout.addLayout(strategy_frames_row)
        
        # ====== FINAL SECTION ======
        # Compound Profit Toggle with label and tooltip
        compound_profit_row = QHBoxLayout()
        compound_profit_row.addStretch()
        
        # Compound Profit label
        compound_profit_label = QLabel()
        compound_profit_label.setObjectName(u"CompoundProfitLabel")
        compound_profit_label.setText("Compound profit?")
        compound_profit_row.addWidget(compound_profit_label)
        
        compound_profit_row.addSpacing(10)
        
        self.CreateTradeTabMainCreateTradeSubTabCompoundProfitToggle = ToggleSwitch(left_text="No", right_text="Yes")
        self.CreateTradeTabMainCreateTradeSubTabCompoundProfitToggle.setObjectName(u"CreateTradeTabMainCreateTradeSubTabCompoundProfitToggle")
        compound_profit_row.addWidget(self.CreateTradeTabMainCreateTradeSubTabCompoundProfitToggle)
        
        self.CreateTradeTabMainCreateTradeSubTabCompoundProfitTooltip = QLabel()
        self.CreateTradeTabMainCreateTradeSubTabCompoundProfitTooltip.setObjectName(u"CreateTradeTabMainCreateTradeSubTabCompoundProfitTooltip")
        self.CreateTradeTabMainCreateTradeSubTabCompoundProfitTooltip.setFont(font3)
        self.CreateTradeTabMainCreateTradeSubTabCompoundProfitTooltip.setMaximumWidth(21)
        compound_profit_row.addWidget(self.CreateTradeTabMainCreateTradeSubTabCompoundProfitTooltip)
        
        page2_layout.addLayout(compound_profit_row)
        
        # Spacer to push bottom row to bottom
        page2_layout.addStretch()
        
        # Edit feedback text area (for trade edit mode) - hidden by default
        self.CreateTradeTabMainCreateTradeSubTabEditFeedbackTextArea = QLabel()
        self.CreateTradeTabMainCreateTradeSubTabEditFeedbackTextArea.setObjectName(u"CreateTradeTabMainCreateTradeSubTabEditFeedbackTextArea")
        self.CreateTradeTabMainCreateTradeSubTabEditFeedbackTextArea.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.CreateTradeTabMainCreateTradeSubTabEditFeedbackTextArea.setMaximumHeight(0)  # No space when empty
        self.CreateTradeTabMainCreateTradeSubTabEditFeedbackTextArea.setVisible(False)  # Hidden by default
        page2_layout.addWidget(self.CreateTradeTabMainCreateTradeSubTabEditFeedbackTextArea)
        
        # Bottom row: Text (75%) and Button (25%)
        bottom_row = QHBoxLayout()
        
        # Additional explanatory text (75% of row)
        self.CreateTradeTabMainCreateTradeSubTabSelectTradeIndicatorsTextTwo = QLabel()
        self.CreateTradeTabMainCreateTradeSubTabSelectTradeIndicatorsTextTwo.setObjectName(u"CreateTradeTabMainCreateTradeSubTabSelectTradeIndicatorsTextTwo")
        self.CreateTradeTabMainCreateTradeSubTabSelectTradeIndicatorsTextTwo.setWordWrap(True)
        bottom_row.addWidget(self.CreateTradeTabMainCreateTradeSubTabSelectTradeIndicatorsTextTwo, 3)  # 75% stretch factor
        
        # Create Trade button (25% of row)
        self.CreateTradeTabMainCreateTradeSubTabCreateTradeButton = QPushButton()
        self.CreateTradeTabMainCreateTradeSubTabCreateTradeButton.setObjectName(u"CreateTradeTabMainCreateTradeSubTabCreateTradeButton")
        self.CreateTradeTabMainCreateTradeSubTabCreateTradeButton.setMinimumSize(176, 41)
        bottom_row.addWidget(self.CreateTradeTabMainCreateTradeSubTabCreateTradeButton, 1)  # 25% stretch factor
        
        page2_layout.addLayout(bottom_row)
        
        self.CreateTradeTabMenu.addWidget(self.CreateTradeSubTab)
    
    def _setupUi_legacy(self, CreateTradeTabMain):
        """Legacy fixed-size implementation"""
        CreateTradeTabMain.setObjectName(u"CreateTradeTabMain")
        self.CreateTradeTabMenu = QStackedWidget(CreateTradeTabMain)
        self.CreateTradeTabMenu.setObjectName(u"CreateTradeTabMenu")
        self.CreateTradeTabMenu.setGeometry(QRect(0, 0, 801, 551))
        font = QFont()
        font.setBold(True)
        font1 = QFont()
        font1.setPointSize(10)
        font1.setBold(True)
        font1.setWeight(QFont.Weight.Bold)
        font3 = QFont()
        font3.setFamilies([u"Segoe UI"])
        font3.setPointSize(14)
        self.ConfigTradePairsSubTab = QWidget()
        self.ConfigTradePairsSubTab.setObjectName(u"ConfigTradePairsSubTab")
        self.CreateTradeTabConfigureTradePairsFindPoolsTitleTab = QLabel(self.ConfigTradePairsSubTab)
        self.CreateTradeTabConfigureTradePairsFindPoolsTitleTab.setObjectName(u"CreateTradeTabConfigureTradePairsFindPoolsTitleTab")
        self.CreateTradeTabConfigureTradePairsFindPoolsTitleTab.setGeometry(QRect(20, 190, 131, 16))
        self.CreateTradeTabConfigureTradePairsFindPoolsScrollArea = QScrollArea(self.ConfigTradePairsSubTab)
        self.CreateTradeTabConfigureTradePairsFindPoolsScrollArea.setObjectName(u"CreateTradeTabConfigureTradePairsFindPoolsScrollArea")
        self.CreateTradeTabConfigureTradePairsFindPoolsScrollArea.setGeometry(QRect(20, 360, 240, 150))
        self.CreateTradeTabConfigureTradePairsFindPoolsScrollArea.setWidgetResizable(True)
        self.scrollAreaWidgetContents_11 = QWidget()
        self.scrollAreaWidgetContents_11.setObjectName(u"scrollAreaWidgetContents_11")
        self.scrollAreaWidgetContents_11.setGeometry(QRect(1, 370, 238, 148))
        self.CreateTradeTabConfigureTradePairsFindPoolsScrollArea.setWidget(self.scrollAreaWidgetContents_11)
        self.CreateTradeTabConfigureTradePairsSubTabRightArrowImage_2 = QLabel(self.ConfigTradePairsSubTab)
        self.CreateTradeTabConfigureTradePairsSubTabRightArrowImage_2.setObjectName(u"CreateTradeTabConfigureTradePairsSubTabRightArrowImage_2")
        self.CreateTradeTabConfigureTradePairsSubTabRightArrowImage_2.setGeometry(QRect(270, 350, 50, 50))
        self.CreateTradeTabConfigureTradePairsSubTabRightArrowImage_2.setPixmap(QPixmap(u":/images/images/right.png"))
        self.CreateTradeTabConfigureTradePairsSubTabRightArrowImage_2.setScaledContents(True)
        self.CreateTradeTabConfigureTradePairsFindPoolsTokenAButton = QPushButton(self.ConfigTradePairsSubTab)
        self.CreateTradeTabConfigureTradePairsFindPoolsTokenAButton.setObjectName(u"CreateTradeTabConfigureTradePairsFindPoolsTokenAButton")
        self.CreateTradeTabConfigureTradePairsFindPoolsTokenAButton.setGeometry(QRect(20, 210, 110, 30))
        self.CreateTradeTabConfigureTradePairsFindPoolsTokenBButton = QPushButton(self.ConfigTradePairsSubTab)
        self.CreateTradeTabConfigureTradePairsFindPoolsTokenBButton.setObjectName(u"CreateTradeTabConfigureTradePairsFindPoolsTokenBButton")
        self.CreateTradeTabConfigureTradePairsFindPoolsTokenBButton.setGeometry(QRect(140, 210, 110, 30))
        self.CreateTradeTabConfigureTradePairsFindPoolsTextArea = QLabel(self.ConfigTradePairsSubTab)
        self.CreateTradeTabConfigureTradePairsFindPoolsTextArea.setObjectName(u"CreateTradeTabConfigureTradePairsFindPoolsTextArea")
        self.CreateTradeTabConfigureTradePairsFindPoolsTextArea.setGeometry(QRect(25, 290, 231, 61))
        self.CreateTradeTabConfigureTradePairsFindPoolsTextArea.setWordWrap(True)
        self.CreateTradeTabConfigureTradePairsFindPoolsSearchButton = QPushButton(self.ConfigTradePairsSubTab)
        self.CreateTradeTabConfigureTradePairsFindPoolsSearchButton.setObjectName(u"CreateTradeTabConfigureTradePairsFindPoolsSearchButton")
        self.CreateTradeTabConfigureTradePairsFindPoolsSearchButton.setGeometry(QRect(60, 250, 151, 30))
        self.CreateTradeTabConfigureTradePairsSubTabAstrolescentScrollArea = QScrollArea(self.ConfigTradePairsSubTab)
        self.CreateTradeTabConfigureTradePairsSubTabAstrolescentScrollArea.setObjectName(u"CreateTradeTabConfigureTradePairsSubTabAstrolescentScrollArea")
        self.CreateTradeTabConfigureTradePairsSubTabAstrolescentScrollArea.setGeometry(QRect(330, 210, 180, 300))
        self.CreateTradeTabConfigureTradePairsSubTabAstrolescentScrollArea.setWidgetResizable(True)
        self.scrollAreaWidgetContents_8 = QWidget()
        self.scrollAreaWidgetContents_8.setObjectName(u"scrollAreaWidgetContents_8")
        self.scrollAreaWidgetContents_8.setGeometry(QRect(1, 1, 178, 298))
        self.CreateTradeTabConfigureTradePairsSubTabAstrolescentScrollArea.setWidget(self.scrollAreaWidgetContents_8)
        self.CreateTradeTabConfigureTradePairsSubTabAstrolescentTitleLabel = QLabel(self.ConfigTradePairsSubTab)
        self.CreateTradeTabConfigureTradePairsSubTabAstrolescentTitleLabel.setObjectName(u"CreateTradeTabConfigureTradePairsSubTabAstrolescentTitleLabel")
        self.CreateTradeTabConfigureTradePairsSubTabAstrolescentTitleLabel.setGeometry(QRect(340, 190, 151, 16))
        self.CreateTradeTabConfigureTradePairsSubTabTextLabel = QLabel(self.ConfigTradePairsSubTab)
        self.CreateTradeTabConfigureTradePairsSubTabTextLabel.setObjectName(u"CreateTradeTabConfigureTradePairsSubTabTextLabel")
        self.CreateTradeTabConfigureTradePairsSubTabTextLabel.setGeometry(QRect(20, 30, 240, 155))
        self.CreateTradeTabConfigureTradePairsSubTabTextLabel.setWordWrap(True)
        self.CreateTradeTabConfigureTradePairsSubTabTextLabel2 = QLabel(self.ConfigTradePairsSubTab)
        self.CreateTradeTabConfigureTradePairsSubTabTextLabel2.setObjectName(u"CreateTradeTabConfigureTradePairsSubTabTextLabel2")
        self.CreateTradeTabConfigureTradePairsSubTabTextLabel2.setGeometry(QRect(320, 30, 210, 155))
        self.CreateTradeTabConfigureTradePairsSubTabTextLabel2.setWordWrap(True)
        self.CreateTradeTabConfigureTradePairsSubTabTextLabel3 = QLabel(self.ConfigTradePairsSubTab)
        self.CreateTradeTabConfigureTradePairsSubTabTextLabel3.setObjectName(u"CreateTradeTabConfigureTradePairsSubTabTextLabel3")
        self.CreateTradeTabConfigureTradePairsSubTabTextLabel3.setGeometry(QRect(580, 30, 200, 155))
        self.CreateTradeTabConfigureTradePairsSubTabTextLabel3.setWordWrap(True)

        self.CreateTradeTabConfigureTradePairsSubTabRadBotTitleLabel = QLabel(self.ConfigTradePairsSubTab)
        self.CreateTradeTabConfigureTradePairsSubTabRadBotTitleLabel.setObjectName(u"CreateTradeTabConfigureTradePairsSubTabRadBotTitleLabel")
        self.CreateTradeTabConfigureTradePairsSubTabRadBotTitleLabel.setGeometry(QRect(600, 190, 151, 16))
        self.CreateTradeTabConfigureTradePairsSubTabRadBotScrollArea = QScrollArea(self.ConfigTradePairsSubTab)
        self.CreateTradeTabConfigureTradePairsSubTabRadBotScrollArea.setObjectName(u"CreateTradeTabConfigureTradePairsSubTabRadBotScrollArea")
        self.CreateTradeTabConfigureTradePairsSubTabRadBotScrollArea.setGeometry(QRect(590, 210, 180, 300))
        self.CreateTradeTabConfigureTradePairsSubTabRadBotScrollArea.setLineWidth(1)
        self.CreateTradeTabConfigureTradePairsSubTabRadBotScrollArea.setWidgetResizable(True)
        self.scrollAreaWidgetContents_9 = QWidget()
        self.scrollAreaWidgetContents_9.setObjectName(u"scrollAreaWidgetContents_9")
        self.scrollAreaWidgetContents_9.setGeometry(QRect(0, 0, 178, 298))
        self.CreateTradeTabConfigureTradePairsSubTabRadBotScrollArea.setWidget(self.scrollAreaWidgetContents_9)
        self.CreateTradeTabConfigureTradePairsSubTabRightArrowImage = QLabel(self.ConfigTradePairsSubTab)
        self.CreateTradeTabConfigureTradePairsSubTabRightArrowImage.setObjectName(u"CreateTradeTabConfigureTradePairsSubTabRightArrowImage")
        self.CreateTradeTabConfigureTradePairsSubTabRightArrowImage.setGeometry(QRect(525, 220, 50, 50))
        self.CreateTradeTabConfigureTradePairsSubTabRightArrowImage.setPixmap(QPixmap(u":/images/images/right.png"))
        self.CreateTradeTabConfigureTradePairsSubTabRightArrowImage.setScaledContents(True)
        self.CreateTradeTabConfigureTradePairsSubTabLeftArrowImage = QLabel(self.ConfigTradePairsSubTab)
        self.CreateTradeTabConfigureTradePairsSubTabLeftArrowImage.setObjectName(u"CreateTradeTabConfigureTradePairsSubTabLeftArrowImage")
        self.CreateTradeTabConfigureTradePairsSubTabLeftArrowImage.setGeometry(QRect(525, 350, 50, 50))
        self.CreateTradeTabConfigureTradePairsSubTabLeftArrowImage.setPixmap(QPixmap(u":/images/images/left.png"))
        self.CreateTradeTabConfigureTradePairsSubTabLeftArrowImage.setScaledContents(True)
        self.CreateTradeTabConfigureTradePairsBackButton = QPushButton(self.ConfigTradePairsSubTab)
        self.CreateTradeTabConfigureTradePairsBackButton.setObjectName(u"CreateTradeTabConfigureTradePairsBackButton")
        self.CreateTradeTabConfigureTradePairsBackButton.setGeometry(QRect(20, 5, 140, 30))
        self.CreateTradeTabMenu.addWidget(self.ConfigTradePairsSubTab)
        self.CreateTradeSubTab = QWidget()
        self.CreateTradeSubTab.setObjectName(u"CreateTradeSubTab")
        self.CreateTradeTabMainCreateTradeSubTabSelectTradePairTitle = QLabel(self.CreateTradeSubTab)
        self.CreateTradeTabMainCreateTradeSubTabSelectTradePairTitle.setObjectName(u"CreateTradeTabMainCreateTradeSubTabSelectTradePairTitle")
        self.CreateTradeTabMainCreateTradeSubTabSelectTradePairTitle.setGeometry(QRect(20, 20, 101, 16))
        self.CreateTradeTabMainCreateTradeSubTabSelectTradePairScrollArea = QScrollArea(self.CreateTradeSubTab)
        self.CreateTradeTabMainCreateTradeSubTabSelectTradePairScrollArea.setObjectName(u"CreateTradeTabMainCreateTradeSubTabSelectTradePairScrollArea")
        self.CreateTradeTabMainCreateTradeSubTabSelectTradePairScrollArea.setGeometry(QRect(20, 40, 200, 115))
        self.CreateTradeTabMainCreateTradeSubTabSelectTradePairScrollArea.setLineWidth(1)
        self.CreateTradeTabMainCreateTradeSubTabSelectTradePairScrollArea.setWidgetResizable(True)
        self.scrollAreaWidgetContents_10 = QWidget()
        self.scrollAreaWidgetContents_10.setObjectName(u"scrollAreaWidgetContents_10")
        self.scrollAreaWidgetContents_10.setGeometry(QRect(0, 0, 199, 79))
        self.CreateTradeTabMainCreateTradeSubTabSelectTradePairScrollArea.setWidget(self.scrollAreaWidgetContents_10)
        self.CreateTradeTabMainCreateTradeSubTabSelectTradeIndicatorsTitle = QLabel(self.CreateTradeSubTab)
        self.CreateTradeTabMainCreateTradeSubTabSelectTradeIndicatorsTitle.setObjectName(u"CreateTradeTabMainCreateTradeSubTabSelectTradeIndicatorsTitle")
        self.CreateTradeTabMainCreateTradeSubTabSelectTradeIndicatorsTitle.setGeometry(QRect(20, 170, 101, 21))
        self.CreateTradeTabMainCreateTradeSubTabSelectTradeIndicatorsTextOne = QLabel(self.CreateTradeSubTab)
        self.CreateTradeTabMainCreateTradeSubTabSelectTradeIndicatorsTextOne.setObjectName(u"CreateTradeTabMainCreateTradeSubTabSelectTradeIndicatorsTextOne")
        self.CreateTradeTabMainCreateTradeSubTabSelectTradeIndicatorsTextOne.setGeometry(QRect(20, 190, 761, 31))
        self.CreateTradeTabMainCreateTradeSubTabSelectTradeIndicatorsTextOne.setWordWrap(True)
        self.CreateTradeTabMainCreateTradeSubTabTradeTokenAmountTitle = QLabel(self.CreateTradeSubTab)
        self.CreateTradeTabMainCreateTradeSubTabTradeTokenAmountTitle.setObjectName(u"CreateTradeTabMainCreateTradeSubTabTradeTokenAmountTitle")
        self.CreateTradeTabMainCreateTradeSubTabTradeTokenAmountTitle.setGeometry(QRect(550, 20, 181, 16))
        self.CreateTradeTabMainCreateTradeSubTabTradeTokenAmountText = QLabel(self.CreateTradeSubTab)
        self.CreateTradeTabMainCreateTradeSubTabTradeTokenAmountText.setObjectName(u"CreateTradeTabMainCreateTradeSubTabTradeTokenAmountText")
        self.CreateTradeTabMainCreateTradeSubTabTradeTokenAmountText.setGeometry(QRect(550, 40, 225, 31))
        self.CreateTradeTabMainCreateTradeSubTabTradeTokenAmountText.setWordWrap(True)
        self.CreateTradeTabMainCreateTradeSubTabCreateTradeButton = QPushButton(self.CreateTradeSubTab)
        self.CreateTradeTabMainCreateTradeSubTabCreateTradeButton.setObjectName(u"CreateTradeTabMainCreateTradeSubTabCreateTradeButton")
        self.CreateTradeTabMainCreateTradeSubTabCreateTradeButton.setGeometry(QRect(610, 470, 176, 41))
        self.CreateTradeTabMainCreateTradeSubTabPingPongFrame = QFrame(self.CreateTradeSubTab)
        self.CreateTradeTabMainCreateTradeSubTabPingPongFrame.setObjectName(u"CreateTradeTabMainCreateTradeSubTabPingPongFrame")
        self.CreateTradeTabMainCreateTradeSubTabPingPongFrame.setGeometry(QRect(10, 385, 381, 66))
        self.CreateTradeTabMainCreateTradeSubTabPingPongFrame.setFrameShape(QFrame.Shape.StyledPanel)
        self.CreateTradeTabMainCreateTradeSubTabPingPongFrame.setFrameShadow(QFrame.Shadow.Raised)
        self.CreateTradeTabMainCreateTradeSubTabPingPongInfoTooltip = QLabel(self.CreateTradeTabMainCreateTradeSubTabPingPongFrame)
        self.CreateTradeTabMainCreateTradeSubTabPingPongInfoTooltip.setObjectName(u"CreateTradeTabMainCreateTradeSubTabPingPongInfoTooltip")
        self.CreateTradeTabMainCreateTradeSubTabPingPongInfoTooltip.setGeometry(QRect(330, 2, 21, 30))
        self.CreateTradeTabMainCreateTradeSubTabPingPongInfoTooltip.setFont(font3)
        self.CreateTradeTabMainCreateTradeSubTabPingPongCheckbox = QCheckBox(self.CreateTradeTabMainCreateTradeSubTabPingPongFrame)
        self.CreateTradeTabMainCreateTradeSubTabPingPongCheckbox.setObjectName(u"CreateTradeTabMainCreateTradeSubTabPingPongCheckbox")
        self.CreateTradeTabMainCreateTradeSubTabPingPongCheckbox.setGeometry(QRect(20, 7, 291, 21))
        self.CreateTradeTabMainCreateTradeSubTabPingPongCheckbox.setChecked(False)
        self.CreateTradeTabMainCreateTradeSubTabPingPongCheckbox.setLayoutDirection(Qt.RightToLeft)
        self.CreateTradeTabMainCreateTradeSubTabPingPongSellPriceField = QLineEdit(self.CreateTradeTabMainCreateTradeSubTabPingPongFrame)
        self.CreateTradeTabMainCreateTradeSubTabPingPongSellPriceField.setObjectName(u"CreateTradeTabMainCreateTradeSubTabPingPongSellPriceField")
        self.CreateTradeTabMainCreateTradeSubTabPingPongSellPriceField.setGeometry(QRect(265, 40, 60, 22))
        self.CreateTradeTabMainCreateTradeSubTabPingPongSellPriceTitle = QLabel(self.CreateTradeTabMainCreateTradeSubTabPingPongFrame)
        self.CreateTradeTabMainCreateTradeSubTabPingPongSellPriceTitle.setObjectName(u"CreateTradeTabMainCreateTradeSubTabPingPongSellPriceTitle")
        self.CreateTradeTabMainCreateTradeSubTabPingPongSellPriceTitle.setGeometry(QRect(210, 40, 51, 21))
        self.CreateTradeTabMainCreateTradeSubTabPingPongBuyPriceField = QLineEdit(self.CreateTradeTabMainCreateTradeSubTabPingPongFrame)
        self.CreateTradeTabMainCreateTradeSubTabPingPongBuyPriceField.setObjectName(u"CreateTradeTabMainCreateTradeSubTabPingPongBuyPriceField")
        self.CreateTradeTabMainCreateTradeSubTabPingPongBuyPriceField.setGeometry(QRect(85, 40, 60, 22))
        self.CreateTradeTabMainCreateTradeSubTabPingPongBuyPriceTitle = QLabel(self.CreateTradeTabMainCreateTradeSubTabPingPongFrame)
        self.CreateTradeTabMainCreateTradeSubTabPingPongBuyPriceTitle.setObjectName(u"CreateTradeTabMainCreateTradeSubTabPingPongBuyPriceTitle")
        self.CreateTradeTabMainCreateTradeSubTabPingPongBuyPriceTitle.setGeometry(QRect(26, 40, 51, 21))
        self.CreateTradeTabMainCreateTradeSubTabPingPongBuyPriceSymbol = QLabel(self.CreateTradeTabMainCreateTradeSubTabPingPongFrame)
        self.CreateTradeTabMainCreateTradeSubTabPingPongBuyPriceSymbol.setObjectName(u"CreateTradeTabMainCreateTradeSubTabPingPongBuyPriceSymbol")
        self.CreateTradeTabMainCreateTradeSubTabPingPongBuyPriceSymbol.setGeometry(QRect(150, 40, 46, 21))
        self.CreateTradeTabMainCreateTradeSubTabPingPongSellPriceSymbol = QLabel(self.CreateTradeTabMainCreateTradeSubTabPingPongFrame)
        self.CreateTradeTabMainCreateTradeSubTabPingPongSellPriceSymbol.setObjectName(u"CreateTradeTabMainCreateTradeSubTabPingPongSellPriceSymbol")
        self.CreateTradeTabMainCreateTradeSubTabPingPongSellPriceSymbol.setGeometry(QRect(330, 40, 46, 21))
        self.CreateTradeTabMainCreateTradeSubTabAIStrategyFrame = QFrame(self.CreateTradeSubTab)
        self.CreateTradeTabMainCreateTradeSubTabAIStrategyFrame.setObjectName(u"CreateTradeTabMainCreateTradeSubTabAIStrategyFrame")
        self.CreateTradeTabMainCreateTradeSubTabAIStrategyFrame.setGeometry(QRect(405, 385, 381, 32))
        self.CreateTradeTabMainCreateTradeSubTabAIStrategyFrame.setFrameShape(QFrame.Shape.StyledPanel)
        self.CreateTradeTabMainCreateTradeSubTabAIStrategyFrame.setFrameShadow(QFrame.Shadow.Raised)
        self.CreateTradeTabMainCreateTradeSubTabAIStrategyCheckbox = QCheckBox(self.CreateTradeTabMainCreateTradeSubTabAIStrategyFrame)
        self.CreateTradeTabMainCreateTradeSubTabAIStrategyCheckbox.setObjectName(u"CreateTradeTabMainCreateTradeSubTabAIStrategyCheckbox")
        self.CreateTradeTabMainCreateTradeSubTabAIStrategyCheckbox.setGeometry(QRect(20, 1, 291, 30))
        self.CreateTradeTabMainCreateTradeSubTabAIStrategyCheckbox.setChecked(False)
        self.CreateTradeTabMainCreateTradeSubTabAIStrategyCheckbox.setLayoutDirection(Qt.RightToLeft)
        self.CreateTradeTabMainCreateTradeSubTabAIStrategyTooltip = QLabel(self.CreateTradeTabMainCreateTradeSubTabAIStrategyFrame)
        self.CreateTradeTabMainCreateTradeSubTabAIStrategyTooltip.setObjectName(u"CreateTradeTabMainCreateTradeSubTabAIStrategyTooltip")
        self.CreateTradeTabMainCreateTradeSubTabAIStrategyTooltip.setGeometry(QRect(330, 1, 21, 30))
        self.CreateTradeTabMainCreateTradeSubTabAIStrategyTooltip.setFont(font3)
        self.CreateTradeTabMainCreateTradeSubTabBBFrame = QFrame(self.CreateTradeSubTab)
        self.CreateTradeTabMainCreateTradeSubTabBBFrame.setObjectName(u"CreateTradeTabMainCreateTradeSubTabBBFrame")
        self.CreateTradeTabMainCreateTradeSubTabBBFrame.setGeometry(QRect(405, 270, 381, 32))
        self.CreateTradeTabMainCreateTradeSubTabBBFrame.setFrameShape(QFrame.Shape.StyledPanel)
        self.CreateTradeTabMainCreateTradeSubTabBBFrame.setFrameShadow(QFrame.Shadow.Raised)
        self.CreateTradeTabMainCreateTradeSubTabBBCheckbox = QCheckBox(self.CreateTradeTabMainCreateTradeSubTabBBFrame)
        self.CreateTradeTabMainCreateTradeSubTabBBCheckbox.setObjectName(u"CreateTradeTabMainCreateTradeSubTabBBCheckbox")
        self.CreateTradeTabMainCreateTradeSubTabBBCheckbox.setGeometry(QRect(20, 1, 291, 30))
        self.CreateTradeTabMainCreateTradeSubTabBBCheckbox.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.CreateTradeTabMainCreateTradeSubTabBBCheckbox.setLayoutDirection(Qt.RightToLeft)
        self.CreateTradeTabMainCreateTradeSubTabBBInfoTooltip = QLabel(self.CreateTradeTabMainCreateTradeSubTabBBFrame)
        self.CreateTradeTabMainCreateTradeSubTabBBInfoTooltip.setObjectName(u"CreateTradeTabMainCreateTradeSubTabBBInfoTooltip")
        self.CreateTradeTabMainCreateTradeSubTabBBInfoTooltip.setGeometry(QRect(330, 1, 21, 30))
        self.CreateTradeTabMainCreateTradeSubTabBBInfoTooltip.setFont(font3)
        self.CreateTradeTabMainCreateTradeSubTabMACDFrame = QFrame(self.CreateTradeSubTab)
        self.CreateTradeTabMainCreateTradeSubTabMACDFrame.setObjectName(u"CreateTradeTabMainCreateTradeSubTabMACDFrame")
        self.CreateTradeTabMainCreateTradeSubTabMACDFrame.setGeometry(QRect(405, 230, 381, 32))
        self.CreateTradeTabMainCreateTradeSubTabMACDFrame.setFrameShape(QFrame.Shape.StyledPanel)
        self.CreateTradeTabMainCreateTradeSubTabMACDFrame.setFrameShadow(QFrame.Shadow.Raised)
        self.CreateTradeTabMainCreateTradeSubTabMACDInfoTooltip = QLabel(self.CreateTradeTabMainCreateTradeSubTabMACDFrame)
        self.CreateTradeTabMainCreateTradeSubTabMACDInfoTooltip.setObjectName(u"CreateTradeTabMainCreateTradeSubTabMACDInfoTooltip")
        self.CreateTradeTabMainCreateTradeSubTabMACDInfoTooltip.setGeometry(QRect(330, 1, 21, 30))
        self.CreateTradeTabMainCreateTradeSubTabMACDInfoTooltip.setFont(font3)
        self.CreateTradeTabMainCreateTradeSubTabMACDCheckbox = QCheckBox(self.CreateTradeTabMainCreateTradeSubTabMACDFrame)
        self.CreateTradeTabMainCreateTradeSubTabMACDCheckbox.setObjectName(u"CreateTradeTabMainCreateTradeSubTabMACDCheckbox")
        self.CreateTradeTabMainCreateTradeSubTabMACDCheckbox.setGeometry(QRect(20, 1, 291, 30))
        self.CreateTradeTabMainCreateTradeSubTabMACDCheckbox.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.CreateTradeTabMainCreateTradeSubTabMACDCheckbox.setLayoutDirection(Qt.RightToLeft)
        self.CreateTradeTabMainCreateTradeSubTabMACFrame = QFrame(self.CreateTradeSubTab)
        self.CreateTradeTabMainCreateTradeSubTabMACFrame.setObjectName(u"CreateTradeTabMainCreateTradeSubTabMACFrame")
        self.CreateTradeTabMainCreateTradeSubTabMACFrame.setGeometry(QRect(10, 270, 381, 32))
        self.CreateTradeTabMainCreateTradeSubTabMACFrame.setFrameShape(QFrame.Shape.StyledPanel)
        self.CreateTradeTabMainCreateTradeSubTabMACFrame.setFrameShadow(QFrame.Shadow.Raised)
        self.CreateTradeTabMainCreateTradeSubTabMACInfoTooltip = QLabel(self.CreateTradeTabMainCreateTradeSubTabMACFrame)
        self.CreateTradeTabMainCreateTradeSubTabMACInfoTooltip.setObjectName(u"CreateTradeTabMainCreateTradeSubTabMACInfoTooltip")
        self.CreateTradeTabMainCreateTradeSubTabMACInfoTooltip.setGeometry(QRect(330, 1, 21, 30))
        self.CreateTradeTabMainCreateTradeSubTabMACInfoTooltip.setFont(font3)
        self.CreateTradeTabMainCreateTradeSubTabMACCheckbox = QCheckBox(self.CreateTradeTabMainCreateTradeSubTabMACFrame)
        self.CreateTradeTabMainCreateTradeSubTabMACCheckbox.setObjectName(u"CreateTradeTabMainCreateTradeSubTabMACCheckbox")
        self.CreateTradeTabMainCreateTradeSubTabMACCheckbox.setGeometry(QRect(20, 1, 291, 30))
        self.CreateTradeTabMainCreateTradeSubTabMACCheckbox.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.CreateTradeTabMainCreateTradeSubTabMACCheckbox.setLayoutDirection(Qt.RightToLeft)
        self.CreateTradeTabMainCreateTradeSubTabRSIFrame = QFrame(self.CreateTradeSubTab)
        self.CreateTradeTabMainCreateTradeSubTabRSIFrame.setObjectName(u"CreateTradeTabMainCreateTradeSubTabRSIFrame")
        self.CreateTradeTabMainCreateTradeSubTabRSIFrame.setGeometry(QRect(10, 230, 381, 32))
        self.CreateTradeTabMainCreateTradeSubTabRSIFrame.setFrameShape(QFrame.Shape.StyledPanel)
        self.CreateTradeTabMainCreateTradeSubTabRSIFrame.setFrameShadow(QFrame.Shadow.Raised)
        self.CreateTradeTabMainCreateTradeSubTabRSIInfoTooltip = QLabel(self.CreateTradeTabMainCreateTradeSubTabRSIFrame)
        self.CreateTradeTabMainCreateTradeSubTabRSIInfoTooltip.setObjectName(u"CreateTradeTabMainCreateTradeSubTabRSIInfoTooltip")
        self.CreateTradeTabMainCreateTradeSubTabRSIInfoTooltip.setGeometry(QRect(330, 1, 21, 30))
        self.CreateTradeTabMainCreateTradeSubTabRSIInfoTooltip.setFont(font3)
        self.CreateTradeTabMainCreateTradeSubTabRSICheckbox = QCheckBox(self.CreateTradeTabMainCreateTradeSubTabRSIFrame)
        self.CreateTradeTabMainCreateTradeSubTabRSICheckbox.setObjectName(u"CreateTradeTabMainCreateTradeSubTabRSICheckbox")
        self.CreateTradeTabMainCreateTradeSubTabRSICheckbox.setGeometry(QRect(20, 1, 291, 30))
        self.CreateTradeTabMainCreateTradeSubTabRSICheckbox.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.CreateTradeTabMainCreateTradeSubTabRSICheckbox.setLayoutDirection(Qt.RightToLeft)
        self.CreateTradeTabMainCreateTradeSubTabSelectTradeIndicatorsTextTwo = QLabel(self.CreateTradeSubTab)
        self.CreateTradeTabMainCreateTradeSubTabSelectTradeIndicatorsTextTwo.setObjectName(u"CreateTradeTabMainCreateTradeSubTabSelectTradeIndicatorsTextTwo")
        self.CreateTradeTabMainCreateTradeSubTabSelectTradeIndicatorsTextTwo.setGeometry(QRect(20, 460, 551, 61))
        self.CreateTradeTabMainCreateTradeSubTabSelectTradeIndicatorsTextTwo.setWordWrap(True)
        self.CreateTradeTabMainCreateTradeSubTabFrameOne = QFrame(self.CreateTradeSubTab)
        self.CreateTradeTabMainCreateTradeSubTabFrameOne.setObjectName(u"CreateTradeTabMainCreateTradeSubTabFrameOne")
        self.CreateTradeTabMainCreateTradeSubTabFrameOne.setGeometry(QRect(10, 10, 776, 155))
        self.CreateTradeTabMainCreateTradeSubTabFrameOne.setFrameShape(QFrame.Shape.StyledPanel)
        self.CreateTradeTabMainCreateTradeSubTabFrameOne.setFrameShadow(QFrame.Shadow.Raised)
        self.CreateTradeTabMainCreateTradeSubTabFrameOne.setLineWidth(2)
        self.CreateTradeTabMainCreateTradeSubTabTradeTokenAmountField = QLineEdit(self.CreateTradeTabMainCreateTradeSubTabFrameOne)
        self.CreateTradeTabMainCreateTradeSubTabTradeTokenAmountField.setObjectName(u"CreateTradeTabMainCreateTradeSubTabTradeTokenAmountField")
        self.CreateTradeTabMainCreateTradeSubTabTradeTokenAmountField.setGeometry(QRect(540, 70, 225, 22))
        self.CreateTradeTabMainCreateTradeSubTabConfigureTradePairsButton = QPushButton(self.CreateTradeTabMainCreateTradeSubTabFrameOne)
        self.CreateTradeTabMainCreateTradeSubTabConfigureTradePairsButton.setObjectName(u"CreateTradeTabMainCreateTradeSubTabConfigureTradePairsButton")
        self.CreateTradeTabMainCreateTradeSubTabConfigureTradePairsButton.setGeometry(QRect(245, 115, 255, 30))
        self.CreateTradeTabMainCreateTradeSubTabStartTokenRadioButtonTwo = QRadioButton(self.CreateTradeTabMainCreateTradeSubTabFrameOne)
        self.CreateTradeTabMainCreateTradeSubTabStartTokenRadioButtonTwo.setObjectName(u"CreateTradeTabMainCreateTradeSubTabStartTokenRadioButtonTwo")
        self.CreateTradeTabMainCreateTradeSubTabStartTokenRadioButtonTwo.setGeometry(QRect(250, 80, 81, 20))
        self.CreateTradeTabMainCreateTradeSubTabStartTokenTitle = QLabel(self.CreateTradeTabMainCreateTradeSubTabFrameOne)
        self.CreateTradeTabMainCreateTradeSubTabStartTokenTitle.setObjectName(u"CreateTradeTabMainCreateTradeSubTabStartTokenTitle")
        self.CreateTradeTabMainCreateTradeSubTabStartTokenTitle.setGeometry(QRect(245, 70, 101, 16))
        self.CreateTradeTabMainCreateTradeSubTabStartTokenRadioButtonOne = QRadioButton(self.CreateTradeTabMainCreateTradeSubTabFrameOne)
        self.CreateTradeTabMainCreateTradeSubTabStartTokenRadioButtonOne.setObjectName(u"CreateTradeTabMainCreateTradeSubTabStartTokenRadioButtonOne")
        self.CreateTradeTabMainCreateTradeSubTabStartTokenRadioButtonOne.setGeometry(QRect(249, 40, 81, 20))
        self.CreateTradeTabMainCreateTradeSubTabAccumulateTokenTitle = QLabel(self.CreateTradeTabMainCreateTradeSubTabFrameOne)
        self.CreateTradeTabMainCreateTradeSubTabAccumulateTokenTitle.setObjectName(u"CreateTradeTabMainCreateTradeSubTabAccumulateTokenTitle")
        self.CreateTradeTabMainCreateTradeSubTabAccumulateTokenTitle.setGeometry(QRect(390, 70, 121, 16))
        self.CreateTradeTabMainCreateTradeSubTabAccumulateTokenRadioButtonOne = QRadioButton(self.CreateTradeTabMainCreateTradeSubTabFrameOne)
        self.CreateTradeTabMainCreateTradeSubTabAccumulateTokenRadioButtonOne.setObjectName(u"CreateTradeTabMainCreateTradeSubTabAccumulateTokenRadioButtonOne")
        self.CreateTradeTabMainCreateTradeSubTabAccumulateTokenRadioButtonOne.setGeometry(QRect(370, 40, 81, 20))
        self.CreateTradeTabMainCreateTradeSubTabAccumulateTokenRadioButtonOne.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        self.CreateTradeTabMainCreateTradeSubTabAccumulateTokenRadioButtonTwo = QRadioButton(self.CreateTradeTabMainCreateTradeSubTabFrameOne)
        self.CreateTradeTabMainCreateTradeSubTabAccumulateTokenRadioButtonTwo.setObjectName(u"CreateTradeTabMainCreateTradeSubTabAccumulateTokenRadioButtonTwo")
        self.CreateTradeTabMainCreateTradeSubTabAccumulateTokenRadioButtonTwo.setGeometry(QRect(370, 80, 81, 20))
        self.CreateTradeTabMainCreateTradeSubTabCurrentPricesTitle = QLabel(self.CreateTradeTabMainCreateTradeSubTabFrameOne)
        self.CreateTradeTabMainCreateTradeSubTabCurrentPricesTitle.setObjectName(u"CreateTradeTabMainCreateTradeSubTabCurrentPricesTitle")
        self.CreateTradeTabMainCreateTradeSubTabCurrentPricesTitle.setGeometry(QRect(240, 10, 141, 20))
        self.CreateTradeTabMainCreateTradeSubTabCurrentPricesTitle.setFont(font)
        self.CreateTradeTabMainCreateTradeSubTabCurrentPricesTextOne = QLabel(self.CreateTradeTabMainCreateTradeSubTabFrameOne)
        self.CreateTradeTabMainCreateTradeSubTabCurrentPricesTextOne.setObjectName(u"CreateTradeTabMainCreateTradeSubTabCurrentPricesTextOne")
        self.CreateTradeTabMainCreateTradeSubTabCurrentPricesTextOne.setGeometry(QRect(320, 27, 211, 20))
        self.CreateTradeTabMainCreateTradeSubTabCurrentPricesTextOne.setAlignment(Qt.AlignmentFlag.AlignLeading|Qt.AlignmentFlag.AlignLeft|Qt.AlignmentFlag.AlignVCenter)
        self.CreateTradeTabMainCreateTradeSubTabCurrentPricesTextTwo = QLabel(self.CreateTradeTabMainCreateTradeSubTabFrameOne)
        self.CreateTradeTabMainCreateTradeSubTabCurrentPricesTextTwo.setObjectName(u"CreateTradeTabMainCreateTradeSubTabCurrentPricesTextTwo")
        self.CreateTradeTabMainCreateTradeSubTabCurrentPricesTextTwo.setGeometry(QRect(320, 44, 211, 20))
        self.CreateTradeTabMainCreateTradeSubTabCurrentPricesTextTwo.setAlignment(Qt.AlignmentFlag.AlignLeading|Qt.AlignmentFlag.AlignLeft|Qt.AlignmentFlag.AlignVCenter)
        self.CreateTradeTabMainCreateTradeSubTabCompoundProfitCheckbox = QCheckBox(self.CreateTradeSubTab)
        self.CreateTradeTabMainCreateTradeSubTabCompoundProfitCheckbox.setObjectName(u"CreateTradeTabMainCreateTradeSubTabCompoundProfitCheckbox")
        self.CreateTradeTabMainCreateTradeSubTabCompoundProfitCheckbox.setGeometry(QRect(575, 425, 141, 30))
        self.CreateTradeTabMainCreateTradeSubTabCompoundProfitCheckbox.setLayoutDirection(Qt.RightToLeft)
        self.CreateTradeTabMainCreateTradeSubTabCompoundProfitTooltip = QLabel(self.CreateTradeSubTab)
        self.CreateTradeTabMainCreateTradeSubTabCompoundProfitTooltip.setObjectName(u"CreateTradeTabMainCreateTradeSubTabCompoundProfitTooltip")
        self.CreateTradeTabMainCreateTradeSubTabCompoundProfitTooltip.setGeometry(QRect(735, 425, 21, 30))
        self.CreateTradeTabMainCreateTradeSubTabCompoundProfitTooltip.setFont(font3)
        self.CreateTradeTabMainCreateTradeSubTabEditFeedbackTextArea = QLabel(self.CreateTradeSubTab)
        self.CreateTradeTabMainCreateTradeSubTabEditFeedbackTextArea.setObjectName(u"CreateTradeTabMainCreateTradeSubTabEditFeedbackTextArea")
        self.CreateTradeTabMainCreateTradeSubTabEditFeedbackTextArea.setGeometry(QRect(400, 400, 141, 20))
        self.CreateTradeTabMainCreateTradeSubTabEditFeedbackTextArea.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.CreateTradeTabMainCreateTradeSubTabStopLossTitle = QLabel(self.CreateTradeTabMainCreateTradeSubTabFrameOne)
        self.CreateTradeTabMainCreateTradeSubTabStopLossTitle.setObjectName(u"CreateTradeTabMainCreateTradeSubTabStopLossTitle")
        self.CreateTradeTabMainCreateTradeSubTabStopLossTitle.setGeometry(QRect(540, 102, 61, 16))
        self.CreateTradeTabMainCreateTradeSubTabTrailingStopTitle = QLabel(self.CreateTradeTabMainCreateTradeSubTabFrameOne)
        self.CreateTradeTabMainCreateTradeSubTabTrailingStopTitle.setObjectName(u"CreateTradeTabMainCreateTradeSubTabTrailingStopTitle")
        self.CreateTradeTabMainCreateTradeSubTabTrailingStopTitle.setGeometry(QRect(540, 127, 71, 16))
        self.CreateTradeTabMainCreateTradeSubTabStopLossInput = QLineEdit(self.CreateTradeTabMainCreateTradeSubTabFrameOne)
        self.CreateTradeTabMainCreateTradeSubTabStopLossInput.setObjectName(u"CreateTradeTabMainCreateTradeSubTabStopLossInput")
        self.CreateTradeTabMainCreateTradeSubTabStopLossInput.setGeometry(QRect(620, 100, 21, 22))
        self.CreateTradeTabMainCreateTradeSubTabStopLossInput.setAlignment(Qt.AlignmentFlag.AlignRight|Qt.AlignmentFlag.AlignTrailing|Qt.AlignmentFlag.AlignVCenter)
        self.CreateTradeTabMainCreateTradeSubTabTrailingStopInput = QLineEdit(self.CreateTradeTabMainCreateTradeSubTabFrameOne)
        self.CreateTradeTabMainCreateTradeSubTabTrailingStopInput.setObjectName(u"CreateTradeTabMainCreateTradeSubTabTrailingStopInput")
        self.CreateTradeTabMainCreateTradeSubTabTrailingStopInput.setGeometry(QRect(620, 125, 21, 22))
        self.CreateTradeTabMainCreateTradeSubTabTrailingStopInput.setAlignment(Qt.AlignmentFlag.AlignRight|Qt.AlignmentFlag.AlignTrailing|Qt.AlignmentFlag.AlignVCenter)
        self.CreateTradeTabMainCreateTradeSubTabStopLossText = QLabel(self.CreateTradeTabMainCreateTradeSubTabFrameOne)
        self.CreateTradeTabMainCreateTradeSubTabStopLossText.setObjectName(u"CreateTradeTabMainCreateTradeSubTabStopLossText")
        self.CreateTradeTabMainCreateTradeSubTabStopLossText.setGeometry(QRect(645, 102, 21, 20))
        self.CreateTradeTabMainCreateTradeSubTabTrailingStopText = QLabel(self.CreateTradeTabMainCreateTradeSubTabFrameOne)
        self.CreateTradeTabMainCreateTradeSubTabTrailingStopText.setObjectName(u"CreateTradeTabMainCreateTradeSubTabTrailingStopText")
        self.CreateTradeTabMainCreateTradeSubTabTrailingStopText.setGeometry(QRect(645, 127, 21, 20))
        self.CreateTradeTabMainCreateTradeSubTabStopsText = QLabel(self.CreateTradeTabMainCreateTradeSubTabFrameOne)
        self.CreateTradeTabMainCreateTradeSubTabStopsText.setObjectName(u"CreateTradeTabMainCreateTradeSubTabStopsText")
        self.CreateTradeTabMainCreateTradeSubTabStopsText.setGeometry(QRect(690, 115, 81, 16))
        self.CreateTradeTabMainCreateTradeSubTabStopsTooltip = QLabel(self.CreateTradeTabMainCreateTradeSubTabFrameOne)
        self.CreateTradeTabMainCreateTradeSubTabStopsTooltip.setObjectName(u"CreateTradeTabMainCreateTradeSubTabStopsTooltip")
        self.CreateTradeTabMainCreateTradeSubTabStopsTooltip.setGeometry(QRect(663, 110, 21, 30))
        self.CreateTradeTabMainCreateTradeSubTabStopsTooltip.setFont(font3)

        self.label_4 = QLabel(self.CreateTradeSubTab)
        self.label_4.setObjectName(u"label_4")
        self.label_4.setGeometry(QRect(20, 315, 101, 21))
        self.label_7 = QLabel(self.CreateTradeSubTab)
        self.label_7.setObjectName(u"label_7")
        self.label_7.setGeometry(QRect(120, 170, 161, 20))
        self.label = QLabel(self.CreateTradeSubTab)
        self.label.setObjectName(u"label")
        self.label.setGeometry(QRect(120, 315, 221, 21))
        self.label_2 = QLabel(self.CreateTradeSubTab)
        self.label_2.setObjectName(u"label_2")
        self.label_2.setGeometry(QRect(20, 335, 761, 41))
        self.label_2.setWordWrap(True)
        self.CreateTradeTabMenu.addWidget(self.CreateTradeSubTab)
        # Set Create Trade page as the default page
        self.CreateTradeTabMenu.setCurrentIndex(1)
        self.CreateTradeTabMainCreateTradeSubTabFrameOne.raise_()
        self.CreateTradeTabMainCreateTradeSubTabRSIFrame.raise_()
        self.CreateTradeTabMainCreateTradeSubTabMACFrame.raise_()
        self.CreateTradeTabMainCreateTradeSubTabMACDFrame.raise_()
        self.CreateTradeTabMainCreateTradeSubTabBBFrame.raise_()
        self.CreateTradeTabMainCreateTradeSubTabPingPongFrame.raise_()
        self.CreateTradeTabMainCreateTradeSubTabAIStrategyFrame.raise_()
        self.CreateTradeTabMainCreateTradeSubTabSelectTradePairTitle.raise_()
        self.CreateTradeTabMainCreateTradeSubTabSelectTradePairScrollArea.raise_()
        self.CreateTradeTabMainCreateTradeSubTabSelectTradeIndicatorsTitle.raise_()
        self.CreateTradeTabMainCreateTradeSubTabSelectTradeIndicatorsTextOne.raise_()
        self.CreateTradeTabMainCreateTradeSubTabTradeTokenAmountTitle.raise_()
        self.CreateTradeTabMainCreateTradeSubTabTradeTokenAmountText.raise_()
        self.CreateTradeTabMainCreateTradeSubTabCreateTradeButton.raise_()
        self.CreateTradeTabMainCreateTradeSubTabSelectTradeIndicatorsTextTwo.raise_()
        self.CreateTradeTabMainCreateTradeSubTabCompoundProfitCheckbox.raise_()
        self.CreateTradeTabMainCreateTradeSubTabCompoundProfitTooltip.raise_()
        self.label_4.raise_()
        self.label_7.raise_()
        self.label.raise_()
        self.label_2.raise_()

        self.CreateTradeTabMenu.setCurrentIndex(1)


    def retranslateUi(self, CreateTradeTabMain):
        self.CreateTradeTabConfigureTradePairsFindPoolsTitleTab.setText(QCoreApplication.translate("AkondRadBotMainWindow", u"<html><head/><body><p><span style=\" font-weight:700;\">Trade Route Finder</span></p></body></html>", None))
        self.CreateTradeTabConfigureTradePairsSubTabRightArrowImage_2.setText("")
        self.CreateTradeTabConfigureTradePairsFindPoolsTokenAButton.setText(QCoreApplication.translate("AkondRadBotMainWindow", u"Token 1", None))
        self.CreateTradeTabConfigureTradePairsFindPoolsTokenBButton.setText(QCoreApplication.translate("AkondRadBotMainWindow", u"Token 2", None))
        self.CreateTradeTabConfigureTradePairsFindPoolsTextArea.setText(QCoreApplication.translate("AkondRadBotMainWindow", u"Discovery of trade pools and routes displayed below. Trade profitability is dependent on the impact. The lower the impact the better.", None))
        self.CreateTradeTabConfigureTradePairsFindPoolsSearchButton.setText(QCoreApplication.translate("AkondRadBotMainWindow", u"Search For Trade Pairs", None))
        self.CreateTradeTabConfigureTradePairsSubTabAstrolescentScrollArea.setWhatsThis("")
        self.CreateTradeTabConfigureTradePairsSubTabAstrolescentTitleLabel.setText(QCoreApplication.translate("AkondRadBotMainWindow", u"<html><head/><body><p><span style=\" font-weight:700;\">Trading Pairs of Interest</span></p></body></html>", None))
        self.CreateTradeTabConfigureTradePairsSubTabTextLabel.setText(QCoreApplication.translate("AkondRadBotMainWindow", u"<html><head/><body><p>The Radix network has hundreds of trading pairs available to choose from. Most trade pairs will likely not be of any interest to you. You can search for any trade pair below, however please be cautious of low liquidity pairs. Low liquidy will result in high slippage, less trades and a probable loss. Radbot works best with high volume pairs.</p></body></html>", None))
        self.CreateTradeTabConfigureTradePairsSubTabTextLabel2.setText(QCoreApplication.translate("AkondRadBotMainWindow", u"<html><head/><body><p>The trade pairs listed here you have discovered with the trade route finder. When adding your trade pairs to the list, please make sure they have good trade volume with someone like Ociswap, DefiPlaze, Astrolescent or CaviarNine. Click a pair to add it to the Radbot trading pairs list.</p></body></html>", None))
        self.CreateTradeTabConfigureTradePairsSubTabTextLabel3.setText(QCoreApplication.translate("AkondRadBotMainWindow", u"<html><head/><body><p>The trade pairs added to the Radbot Trading Pairs list are polled regularly to build price history data, even if you are not actively trading the pair. These are the trade pairs that are made available in the scrollable list back on the 'Create Trade' page you came here from.</p></body></html>", None))

        self.CreateTradeTabConfigureTradePairsSubTabRadBotTitleLabel.setText(QCoreApplication.translate("AkondRadBotMainWindow", u"<html><head/><body><p><span style=\" font-weight:700;\">Radbot Trading Pairs</span></p></body></html>", None))
        self.CreateTradeTabConfigureTradePairsSubTabRadBotScrollArea.setWhatsThis("")
        self.CreateTradeTabConfigureTradePairsSubTabRightArrowImage.setText("")
        self.CreateTradeTabConfigureTradePairsSubTabLeftArrowImage.setText("")
        self.CreateTradeTabConfigureTradePairsBackButton.setText(QCoreApplication.translate("AkondRadBotMainWindow", u"< Back to Create Trade", None))
        self.CreateTradeTabMainCreateTradeSubTabEditFeedbackTextArea.setText("")        
        self.CreateTradeTabMainCreateTradeSubTabSelectTradePairTitle.setText(QCoreApplication.translate("AkondRadBotMainWindow", u"<html><head/><body><p><span style=\" font-weight:700;\">Select Trade Pair</span></p></body></html>", None))
        self.CreateTradeTabMainCreateTradeSubTabSelectTradeIndicatorsTitle.setText(QCoreApplication.translate("AkondRadBotMainWindow", u"<html><head/><body><p><span style=\" font-weight:700;\">Trade Indicators</span></p></body></html>", None))
        self.CreateTradeTabMainCreateTradeSubTabSelectTradeIndicatorsTextOne.setText(QCoreApplication.translate("AkondRadBotMainWindow", u"<html><head/><body><p>Select which market indicators you would like to use for this trade. You may use multiple indicators, their default settings can be set in the &quot;Indicators&quot; tab. You can edit the indicator settings on a per trade basis from the Active Trades list.</p></body></html>", None))
        self.CreateTradeTabMainCreateTradeSubTabTradeTokenAmountTitle.setText(QCoreApplication.translate("AkondRadBotMainWindow", u"<html><head/><body><p><span style=\" font-weight:700;\">Trade Token Amount</span></p></body></html>", None))
        self.CreateTradeTabMainCreateTradeSubTabTradeTokenAmountText.setText(QCoreApplication.translate("AkondRadBotMainWindow", u"How many tokens would you like to start the trade with?", None))
        self.CreateTradeTabMainCreateTradeSubTabCreateTradeButton.setText(QCoreApplication.translate("AkondRadBotMainWindow", u"Create Trade", None))
        self.CreateTradeTabMainCreateTradeSubTabPingPongInfoTooltip.setToolTip(QCoreApplication.translate("AkondRadBotMainWindow", u"<html><head/><body><p><span style=\" color:#000000;\">The default Ping Pong Indicator settings found in the &quot;Indicator&quot; tab are simply an example, they are never used to create a trade. Set the values you would like to use here.</span></p><p><span style=\" color:#000000;\">Ping Pong works best in sideways markets and particularly well in stablecoin markets.</span></p><p><span style=\" color:#000000;\">Two stablecoins that are pegged to the same base asset will differ in price at times, this can be profited from. For example, Buy USDT for 0.98 USDC each, and sell USDC for 1.02 USDT each, indefinately.<br/><br/>You can also use Ping Pong to simply sell at a desired price, just set the buy price to 0.00000001 to prevent it buying back in before you return to cancel the trade.</span></p><p>Inversly it can also be used to set a buy order lower than current prices, just set the sell price to 1000000.00 to prevent it selling before you return to cancel the trade, or at least not mind if it does reach your s"
                        "ell price.<br/><br/>Finally, Ping Pong will ignore any other chosen indicator as it is not compatible with them. </p></body></html>", None))
        self.CreateTradeTabMainCreateTradeSubTabPingPongInfoTooltip.setText(QCoreApplication.translate("AkondRadBotMainWindow", u"🛈", None))
        self.CreateTradeTabMainCreateTradeSubTabPingPongCheckbox.setText(QCoreApplication.translate("AkondRadBotMainWindow", u"Ping Pong :                                                                     ", None))
        self.CreateTradeTabMainCreateTradeSubTabPingPongSellPriceField.setPlaceholderText(QCoreApplication.translate("AkondRadBotMainWindow", u"1.02", None))
        self.CreateTradeTabMainCreateTradeSubTabPingPongSellPriceTitle.setText(QCoreApplication.translate("AkondRadBotMainWindow", u"Sell Price:", None))
        self.CreateTradeTabMainCreateTradeSubTabPingPongBuyPriceField.setPlaceholderText(QCoreApplication.translate("AkondRadBotMainWindow", u"0.98", None))
        self.CreateTradeTabMainCreateTradeSubTabPingPongBuyPriceTitle.setText(QCoreApplication.translate("AkondRadBotMainWindow", u"Buy Price:", None))
        self.CreateTradeTabMainCreateTradeSubTabPingPongBuyPriceSymbol.setText(QCoreApplication.translate("AkondRadBotMainWindow", u"XRD", None))
        self.CreateTradeTabMainCreateTradeSubTabPingPongSellPriceSymbol.setText(QCoreApplication.translate("AkondRadBotMainWindow", u"XRD", None))
        self.CreateTradeTabMainCreateTradeSubTabAIStrategyCheckbox.setText(QCoreApplication.translate("AkondRadBotMainWindow", u"AI Strategy :                                                                     ", None))
        self.CreateTradeTabMainCreateTradeSubTabAIStrategyTooltip.setToolTip(QCoreApplication.translate("AkondRadBotMainWindow", u"<html><head/><body><p>The AI Strategy uses 8 indicators in all. It smooths the data to hopefully get a more reliable indicator of the market. </p><p>The default settings can be changed in the &quot;Indicators&quot; tab. Once you have created a trade you can edit it, enabling you to have multiple same indicator trades with different settings.</p><p>Rad Bot uses machine learning to try and make the AI Strategy perform better than a human and also exercises some risk management. It should be noted that a little extra compute will be used by the bot to periodically process new data for the AI Strategy trades, entailing backtesting 27 parameter combinations for each trade. This takes ~10 - ~30 seconds per trade, weekly. </p></body></html>", None))
        self.CreateTradeTabMainCreateTradeSubTabAIStrategyTooltip.setText(QCoreApplication.translate("AkondRadBotMainWindow", u"🛈", None))
        self.CreateTradeTabMainCreateTradeSubTabBBCheckbox.setText(QCoreApplication.translate("AkondRadBotMainWindow", u"Bollinger Bands, (BB) :                                                    ", None))
        self.CreateTradeTabMainCreateTradeSubTabBBInfoTooltip.setToolTip(QCoreApplication.translate("AkondRadBotMainWindow", u"<html><head/><body><p>The default BB Indicator settings can be changed in the &quot;Indicators&quot; tab. Once you have created a trade you can edit it, enabling you to have multiple BB trades with different settings</p></body></html>", None))
        self.CreateTradeTabMainCreateTradeSubTabBBInfoTooltip.setText(QCoreApplication.translate("AkondRadBotMainWindow", u"🛈", None))
        self.CreateTradeTabMainCreateTradeSubTabMACDInfoTooltip.setToolTip(QCoreApplication.translate("AkondRadBotMainWindow", u"<html><head/><body><p>The default MACD Indicator settings can be changed in the &quot;Indicators&quot; tab. Once you have created a trade you can edit it, enabling you to have multiple MACD trades with different settings.</p></body></html>", None))
        self.CreateTradeTabMainCreateTradeSubTabMACDInfoTooltip.setText(QCoreApplication.translate("AkondRadBotMainWindow", u"🛈", None))
        self.CreateTradeTabMainCreateTradeSubTabMACDCheckbox.setText(QCoreApplication.translate("AkondRadBotMainWindow", u"Moving Average Convergence Divergence (MACD):", None))
        self.CreateTradeTabMainCreateTradeSubTabMACInfoTooltip.setToolTip(QCoreApplication.translate("AkondRadBotMainWindow", u"<html><head/><body><p>The default MAC Indicator settings can be changed in the &quot;Indicators&quot; tab. Once you have created a trade you can edit it, enabling you to have multiple MAC trades with different settings.</p></body></html>", None))
        self.CreateTradeTabMainCreateTradeSubTabMACInfoTooltip.setText(QCoreApplication.translate("AkondRadBotMainWindow", u"🛈", None))
        self.CreateTradeTabMainCreateTradeSubTabMACCheckbox.setText(QCoreApplication.translate("AkondRadBotMainWindow", u"Moving Average Crossover, (MAC) :                           ", None))
        self.CreateTradeTabMainCreateTradeSubTabRSIInfoTooltip.setToolTip(QCoreApplication.translate("AkondRadBotMainWindow", u"<html><head/><body><p>The default RSI Indicator settings can be changed in the &quot;Indicators&quot; tab. Once you have created a trade you can edit it, enabling you to have multiple RSI trades with different settings</p></body></html>", None))
        self.CreateTradeTabMainCreateTradeSubTabRSIInfoTooltip.setText(QCoreApplication.translate("AkondRadBotMainWindow", u"🛈", None))
        self.CreateTradeTabMainCreateTradeSubTabRSICheckbox.setText(QCoreApplication.translate("AkondRadBotMainWindow", u"Relative Strength Index, (RSI) :                                     ", None))
        self.CreateTradeTabMainCreateTradeSubTabSelectTradeIndicatorsTextTwo.setText(QCoreApplication.translate("AkondRadBotMainWindow", u"<html><head/><body><p>Radbot is not a high frequency trading bot. It executes trades for you over the days, weeks, months and years with the potential to learn as it goes thanks to machine learning. Trades can be viewed, edited, paused and cancelled from the Active Trades list.</p></body></html>", None))
        self.CreateTradeTabMainCreateTradeSubTabTradeTokenAmountField.setPlaceholderText(QCoreApplication.translate("AkondRadBotMainWindow", u"1000", None))
        self.CreateTradeTabMainCreateTradeSubTabConfigureTradePairsButton.setText(QCoreApplication.translate("AkondRadBotMainWindow", u"Configure Trade Pairs", None))
        
        # Legacy mode widgets (radio buttons and checkbox)
        if not USE_RESPONSIVE_LAYOUTS:
            self.CreateTradeTabMainCreateTradeSubTabStartTokenRadioButtonTwo.setText(QCoreApplication.translate("AkondRadBotMainWindow", u"Token two", None))
            self.CreateTradeTabMainCreateTradeSubTabStartTokenRadioButtonOne.setText(QCoreApplication.translate("AkondRadBotMainWindow", u"Token one", None))
            self.CreateTradeTabMainCreateTradeSubTabAccumulateTokenRadioButtonOne.setText(QCoreApplication.translate("AkondRadBotMainWindow", u"Token one", None))
            self.CreateTradeTabMainCreateTradeSubTabAccumulateTokenRadioButtonTwo.setText(QCoreApplication.translate("AkondRadBotMainWindow", u"Token two", None))
            self.CreateTradeTabMainCreateTradeSubTabCompoundProfitCheckbox.setText(QCoreApplication.translate("AkondRadBotMainWindow", u"Compound profit?     ", None))
        
        self.CreateTradeTabMainCreateTradeSubTabStartTokenTitle.setText(QCoreApplication.translate("AkondRadBotMainWindow", u"<html><head/><body><p><span style=\" font-weight:700;\">Start Token</span></p></body></html>", None))
        self.CreateTradeTabMainCreateTradeSubTabAccumulateTokenTitle.setText(QCoreApplication.translate("AkondRadBotMainWindow", u"<html><head/><body><p><span style=\" font-weight:700;\">Accumulate Token</span></p></body></html>", None))
        self.CreateTradeTabMainCreateTradeSubTabCurrentPricesTitle.setText(QCoreApplication.translate("AkondRadBotMainWindow", u"Current Prices", None))
        self.CreateTradeTabMainCreateTradeSubTabCurrentPricesTextOne.setText(QCoreApplication.translate("AkondRadBotMainWindow", u"No Trade Pair Selected", None))
        self.CreateTradeTabMainCreateTradeSubTabCurrentPricesTextTwo.setText(QCoreApplication.translate("AkondRadBotMainWindow", u"", None))
        self.CreateTradeTabMainCreateTradeSubTabCompoundProfitTooltip.setToolTip(QCoreApplication.translate("AkondRadBotMainWindow", u"Compounding profits into a trade makes the trade grow larger over time", None))
        self.CreateTradeTabMainCreateTradeSubTabCompoundProfitTooltip.setText(QCoreApplication.translate("AkondRadBotMainWindow", u"🛈", None))
        self.CreateTradeTabMainCreateTradeSubTabStopLossTitle.setText(QCoreApplication.translate("AkondRadBotMainWindow", u"Stop Loss:", None))
        self.CreateTradeTabMainCreateTradeSubTabTrailingStopTitle.setText(QCoreApplication.translate("AkondRadBotMainWindow", u"Trailing Stop:", None))
        self.CreateTradeTabMainCreateTradeSubTabStopLossInput.setPlaceholderText(QCoreApplication.translate("AkondRadBotMainWindow", u"0", None))
        self.CreateTradeTabMainCreateTradeSubTabTrailingStopInput.setPlaceholderText(QCoreApplication.translate("AkondRadBotMainWindow", u"0", None))
        self.CreateTradeTabMainCreateTradeSubTabStopLossText.setText(QCoreApplication.translate("AkondRadBotMainWindow", u"%", None))
        self.CreateTradeTabMainCreateTradeSubTabTrailingStopText.setText(QCoreApplication.translate("AkondRadBotMainWindow", u"%", None))
        self.CreateTradeTabMainCreateTradeSubTabStopsText.setText(QCoreApplication.translate("AkondRadBotMainWindow", u"(0 = Disabled)", None))
        self.CreateTradeTabMainCreateTradeSubTabStopsTooltip.setToolTip(QCoreApplication.translate("AkondRadBotMainWindow", u"<html><head/><body><p>Stop losses are triggered if a trade pairs price drops this value below your initial start price. There is no guarantee that the exact stop loss price will be realised. In volitile markets stop losses can trigger way below your intended level and should be used with caution.</p><p>Trailing stops are triggered when a profitable trade loses the set amount of value from the trades peak price. For example, you have a trade you bought at 100, it hit 110 but dropped back to 105. A trailing stop of 5% would trigger a sell to try and lock in the potential 5% profit that is still on the table. Similar to stop losses, in volitile markets a trailing stop has no guarantee to execute at your set price.</p><p>Both stop losses and trailing stops are a best effort defence to try and protect your capital. Radbot also uses ADX and Kelly criterion functions to help protect your capital. Read more about it in the 'Help' tab.</p></body></html>", None))
        self.CreateTradeTabMainCreateTradeSubTabStopsTooltip.setText(QCoreApplication.translate("AkondRadBotMainWindow", u"🛈", None))
        self.label_4.setText(QCoreApplication.translate("AkondRadBotMainWindow", u"<html><head/><body><p><span style=\" font-weight:700;\">Trade Strategies</span></p></body></html>", None))
        self.label_7.setText(QCoreApplication.translate("AkondRadBotMainWindow", u"(Or select a strategy below)", None))
        self.label.setText(QCoreApplication.translate("AkondRadBotMainWindow", u"(Makes the above indicators redundent)", None))
        self.label_2.setText(QCoreApplication.translate("AkondRadBotMainWindow", u"<html><head/><body><p>The AI Strategy uses 8 indicators and smooths the results to provide a measured response to the trade environment. If you choose to use the Ping Pong indicator, you will need to set the &quot;Buy&quot; and &quot;Sell&quot; values below.</p></body></html>", None))
