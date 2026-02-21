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
    QTextEdit, QTreeView, QWidget, QHBoxLayout, QVBoxLayout,
    QFormLayout, QSpacerItem)
from gui import resources_rc

# Toggle between layout-based (True) and legacy setGeometry (False)
USE_RESPONSIVE_LAYOUTS = True

class Ui_DashboardTabMain(object):   
    def setupUi(self, DashboardTabMain):
        if USE_RESPONSIVE_LAYOUTS:
            self.setupUi_layouts(DashboardTabMain)
        else:
            self.setupUi_legacy(DashboardTabMain)
    
    def setupUi_layouts(self, DashboardTabMain):
        """Layout-based responsive UI setup"""
        DashboardTabMain.setObjectName(u"DashboardTabMain")
        
        # Main horizontal layout: [Stats Panel | Logs Panel]
        main_layout = QHBoxLayout(DashboardTabMain)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(20)
        
        # LEFT PANEL: Stats in form layout
        stats_layout = QFormLayout()
        stats_layout.setHorizontalSpacing(50)
        stats_layout.setVerticalSpacing(20)
        
        # Create font for titles
        font = QFont()
        font.setBold(True)
        
        # Bot Wallet Value
        self.DashboardTabMainBotWalletValueTitle = QLabel("Bot Wallet Value:")
        self.DashboardTabMainBotWalletValueTitle.setFont(font)
        self.DashboardTabMainBotWalletValueTextArea = QLabel("248,391.679251 XRD")
        stats_layout.addRow(self.DashboardTabMainBotWalletValueTitle, self.DashboardTabMainBotWalletValueTextArea)
        
        # Total Profit
        self.DashboardTabMainTotalProfitTitle = QLabel("Total Profit:")
        self.DashboardTabMainTotalProfitTitle.setFont(font)
        self.DashboardTabMainTotalProfitTextArea = QLabel("448,391.679251 XRD")
        stats_layout.addRow(self.DashboardTabMainTotalProfitTitle, self.DashboardTabMainTotalProfitTextArea)
        
        # Add spacer
        stats_layout.addItem(QSpacerItem(0, 10))
        
        # Active Trades
        self.DashboardTabMainActiveTradesTitle = QLabel("Active Trades:")
        self.DashboardTabMainActiveTradesTitle.setFont(font)
        self.DashboardTabMainActiveTradesTextArea = QLabel("51")
        stats_layout.addRow(self.DashboardTabMainActiveTradesTitle, self.DashboardTabMainActiveTradesTextArea)
        
        # Trades Created
        self.DashboardTabMainTradesCreatedTitle = QLabel("Trades Created:")
        self.DashboardTabMainTradesCreatedTitle.setFont(font)
        self.DashboardTabMainTradesCreatedTextArea = QLabel("93")
        stats_layout.addRow(self.DashboardTabMainTradesCreatedTitle, self.DashboardTabMainTradesCreatedTextArea)
        
        # Trades Cancelled
        self.DashboardTabMainTradesCancelledTitle = QLabel("Trades Cancelled:")
        self.DashboardTabMainTradesCancelledTitle.setFont(font)
        self.DashboardTabMainTradesCancelledTextArea = QLabel("42")
        stats_layout.addRow(self.DashboardTabMainTradesCancelledTitle, self.DashboardTabMainTradesCancelledTextArea)
        
        # Add spacer
        stats_layout.addItem(QSpacerItem(0, 10))
        
        # Profitable Trades
        self.DashboardTabMainProfitableTradesTitle = QLabel("Profitable Trades:")
        self.DashboardTabMainProfitableTradesTitle.setFont(font)
        self.DashboardTabMainProfitableTradesTextArea = QLabel("1827")
        stats_layout.addRow(self.DashboardTabMainProfitableTradesTitle, self.DashboardTabMainProfitableTradesTextArea)
        
        # Unprofitable Trades
        self.DashboardTabMainUnprofitableTradesTitle = QLabel("Unprofitable trades:")
        self.DashboardTabMainUnprofitableTradesTitle.setFont(font)
        self.DashboardTabMainUnprofitableTradesTextArea = QLabel("703")
        stats_layout.addRow(self.DashboardTabMainUnprofitableTradesTitle, self.DashboardTabMainUnprofitableTradesTextArea)
        
        # Win Ratio
        self.DashboardTabMainWinRatioTitle = QLabel("Win Ratio:")
        self.DashboardTabMainWinRatioTitle.setFont(font)
        self.DashboardTabMainWinRatioTextArea = QLabel("72.21 %")
        stats_layout.addRow(self.DashboardTabMainWinRatioTitle, self.DashboardTabMainWinRatioTextArea)
        
        # Add spacer
        stats_layout.addItem(QSpacerItem(0, 20))
        
        # Different Tokens Traded
        self.DashboardTabMainDifferentTokensTradedTitle = QLabel("Different Tokens Traded:")
        self.DashboardTabMainDifferentTokensTradedTitle.setFont(font)
        self.DashboardTabMainDifferentTokensTradedTextArea = QLabel("14")
        stats_layout.addRow(self.DashboardTabMainDifferentTokensTradedTitle, self.DashboardTabMainDifferentTokensTradedTextArea)
        
        # Trade Pairs Available
        self.DashboardTabMainTradePairsAvailableTitle = QLabel("Trade Pairs Available:")
        self.DashboardTabMainTradePairsAvailableTitle.setFont(font)
        self.DashboardTabMainTradePairsAvailableTextArea = QLabel("8")
        stats_layout.addRow(self.DashboardTabMainTradePairsAvailableTitle, self.DashboardTabMainTradePairsAvailableTextArea)
        
        # Most Profitable Indicator
        self.DashboardTabMainMostProfitableIndicatorTitle = QLabel("Most Profitable Indicator:")
        self.DashboardTabMainMostProfitableIndicatorTitle.setFont(font)
        self.DashboardTabMainMostProfitableIndicatorTextArea = QLabel("AI Strategy")
        stats_layout.addRow(self.DashboardTabMainMostProfitableIndicatorTitle, self.DashboardTabMainMostProfitableIndicatorTextArea)
        
        # Add spacer
        stats_layout.addItem(QSpacerItem(0, 20))
        
        # Total Trade Volume
        self.DashboardTabMainTotalTradeVolumeTitle = QLabel("Total Trade Volume:")
        self.DashboardTabMainTotalTradeVolumeTitle.setFont(font)
        self.DashboardTabMainTotalTradeVolumeTextArea = QLabel("37,264,827.348691 XRD")
        stats_layout.addRow(self.DashboardTabMainTotalTradeVolumeTitle, self.DashboardTabMainTotalTradeVolumeTextArea)
        
        # Hidden fields (kept for compatibility but not displayed)
        self.DashboardTabMainTotalDepositValueTextArea = QLabel("100,000 XRD")
        self.DashboardTabMainTotalDepositValueTextArea.setVisible(False)
        self.DashboardTabMainTotalWithdrawValueTextArea = QLabel("300,000 XRD")
        self.DashboardTabMainTotalWithdrawValueTextArea.setVisible(False)
        
        # Add vertical spacer to push stats to top
        stats_layout.addItem(QSpacerItem(0, 0, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding))
        
        # Add stats layout to main layout
        main_layout.addLayout(stats_layout, stretch=2)
        
        # RIGHT PANEL: Recent Logs GroupBox
        self.DashboardTabMainRecentLogsGroup = QGroupBox(" Recent Logs ")
        self.DashboardTabMainRecentLogsGroup.setObjectName(u"DashboardTabMainRecentLogsGroup")
        
        # Create vertical layout for logs group
        logs_layout = QVBoxLayout(self.DashboardTabMainRecentLogsGroup)
        logs_layout.setContentsMargins(0, 0, 0, 0)
        
        # ScrollArea inside logs group
        self.DashboardTabMainRecentLogsScrollArea = QScrollArea()
        self.DashboardTabMainRecentLogsScrollArea.setObjectName(u"DashboardTabMainRecentLogsScrollArea")
        self.DashboardTabMainRecentLogsScrollArea.setWidgetResizable(True)
        self.scrollAreaWidgetContents_12 = QWidget()
        self.scrollAreaWidgetContents_12.setObjectName(u"scrollAreaWidgetContents_12")
        self.DashboardTabMainRecentLogsScrollArea.setWidget(self.scrollAreaWidgetContents_12)
        
        logs_layout.addWidget(self.DashboardTabMainRecentLogsScrollArea)
        
        # Add logs panel to main layout
        main_layout.addWidget(self.DashboardTabMainRecentLogsGroup, stretch=3)
        
        # Set object names for compatibility
        self.DashboardTabMainBotWalletValueTitle.setObjectName(u"DashboardTabMainBotWalletValueTitle")
        self.DashboardTabMainActiveTradesTitle.setObjectName(u"DashboardTabMainActiveTradesTitle")
        self.DashboardTabMainTradesCreatedTitle.setObjectName(u"DashboardTabMainTradesCreatedTitle")
        self.DashboardTabMainTradesCancelledTitle.setObjectName(u"DashboardTabMainTradesCancelledTitle")
        self.DashboardTabMainProfitableTradesTitle.setObjectName(u"DashboardTabMainProfitableTradesTitle")
        self.DashboardTabMainUnprofitableTradesTitle.setObjectName(u"DashboardTabMainUnprofitableTradesTitle")
        self.DashboardTabMainTotalTradeVolumeTitle.setObjectName(u"DashboardTabMainTotalTradeVolumeTitle")
        self.DashboardTabMainTotalProfitTitle.setObjectName(u"DashboardTabMainTotalProfitTitle")
        self.DashboardTabMainDifferentTokensTradedTitle.setObjectName(u"DashboardTabMainDifferentTokensTradedTitle")
        self.DashboardTabMainTradePairsAvailableTitle.setObjectName(u"DashboardTabMainTradePairsAvailableTitle")
        self.DashboardTabMainBotWalletValueTextArea.setObjectName(u"DashboardTabMainBotWalletValueTextArea")
        self.DashboardTabMainTotalProfitTextArea.setObjectName(u"DashboardTabMainTotalProfitTextArea")
        self.DashboardTabMainActiveTradesTextArea.setObjectName(u"DashboardTabMainActiveTradesTextArea")
        self.DashboardTabMainTradesCreatedTextArea.setObjectName(u"DashboardTabMainTradesCreatedTextArea")
        self.DashboardTabMainTradesCancelledTextArea.setObjectName(u"DashboardTabMainTradesCancelledTextArea")
        self.DashboardTabMainMostProfitableIndicatorTitle.setObjectName(u"DashboardTabMainMostProfitableIndicatorTitle")
        self.DashboardTabMainProfitableTradesTextArea.setObjectName(u"DashboardTabMainProfitableTradesTextArea")
        self.DashboardTabMainUnprofitableTradesTextArea.setObjectName(u"DashboardTabMainUnprofitableTradesTextArea")
        self.DashboardTabMainTotalDepositValueTextArea.setObjectName(u"DashboardTabMainTotalDepositValueTextArea")
        self.DashboardTabMainTotalWithdrawValueTextArea.setObjectName(u"DashboardTabMainTotalWithdrawValueTextArea")
        self.DashboardTabMainDifferentTokensTradedTextArea.setObjectName(u"DashboardTabMainDifferentTokensTradedTextArea")
        self.DashboardTabMainTradePairsAvailableTextArea.setObjectName(u"DashboardTabMainTradePairsAvailableTextArea")
        self.DashboardTabMainMostProfitableIndicatorTextArea.setObjectName(u"DashboardTabMainMostProfitableIndicatorTextArea")
        self.DashboardTabMainTotalTradeVolumeTextArea.setObjectName(u"DashboardTabMainTotalTradeVolumeTextArea")
        self.DashboardTabMainWinRatioTitle.setObjectName(u"DashboardTabMainWinRatioTitle")
        self.DashboardTabMainWinRatioTextArea.setObjectName(u"DashboardTabMainWinRatioTextArea")
        
        # Call retranslateUi
        self.retranslateUi(DashboardTabMain)
    
    def setupUi_legacy(self, DashboardTabMain):
        """Legacy setGeometry-based UI setup""" 
        DashboardTabMain.setObjectName(u"DashboardTabMain")
        self.DashboardTabMainBotWalletValueTitle = QLabel(DashboardTabMain)
        self.DashboardTabMainBotWalletValueTitle.setObjectName(u"DashboardTabMainBotWalletValueTitle")
        self.DashboardTabMainBotWalletValueTitle.setGeometry(QRect(50, 40, 101, 16))
        font = QFont()
        font.setBold(True)
        self.DashboardTabMainBotWalletValueTitle.setFont(font)
        self.DashboardTabMainActiveTradesTitle = QLabel(DashboardTabMain)
        self.DashboardTabMainActiveTradesTitle.setObjectName(u"DashboardTabMainActiveTradesTitle")
        self.DashboardTabMainActiveTradesTitle.setGeometry(QRect(50, 120, 91, 16))
        self.DashboardTabMainActiveTradesTitle.setFont(font)
        self.DashboardTabMainTradesCreatedTitle = QLabel(DashboardTabMain)
        self.DashboardTabMainTradesCreatedTitle.setObjectName(u"DashboardTabMainTradesCreatedTitle")
        self.DashboardTabMainTradesCreatedTitle.setGeometry(QRect(50, 160, 101, 16))
        self.DashboardTabMainTradesCreatedTitle.setFont(font)
        self.DashboardTabMainTradesCancelledTitle = QLabel(DashboardTabMain)
        self.DashboardTabMainTradesCancelledTitle.setObjectName(u"DashboardTabMainTradesCancelledTitle")
        self.DashboardTabMainTradesCancelledTitle.setGeometry(QRect(50, 180, 111, 16))
        self.DashboardTabMainTradesCancelledTitle.setFont(font)
        self.DashboardTabMainProfitableTradesTitle = QLabel(DashboardTabMain)
        self.DashboardTabMainProfitableTradesTitle.setObjectName(u"DashboardTabMainProfitableTradesTitle")
        self.DashboardTabMainProfitableTradesTitle.setGeometry(QRect(50, 220, 111, 16))
        self.DashboardTabMainProfitableTradesTitle.setFont(font)
        self.DashboardTabMainUnprofitableTradesTitle = QLabel(DashboardTabMain)
        self.DashboardTabMainUnprofitableTradesTitle.setObjectName(u"DashboardTabMainUnprofitableTradesTitle")
        self.DashboardTabMainUnprofitableTradesTitle.setGeometry(QRect(50, 240, 141, 16))
        self.DashboardTabMainUnprofitableTradesTitle.setFont(font)
        self.DashboardTabMainTotalTradeVolumeTitle = QLabel(DashboardTabMain)
        self.DashboardTabMainTotalTradeVolumeTitle.setObjectName(u"DashboardTabMainTotalTradeVolumeTitle")
        self.DashboardTabMainTotalTradeVolumeTitle.setGeometry(QRect(50, 470, 121, 16))
        self.DashboardTabMainTotalTradeVolumeTitle.setFont(font)
        self.DashboardTabMainTotalProfitTitle = QLabel(DashboardTabMain)
        self.DashboardTabMainTotalProfitTitle.setObjectName(u"DashboardTabMainTotalProfitTitle")
        self.DashboardTabMainTotalProfitTitle.setGeometry(QRect(50, 80, 111, 16))
        self.DashboardTabMainTotalProfitTitle.setFont(font)
        # self.DashboardTabMainTotalDepositValueTitle = QLabel(DashboardTabMain)
        # self.DashboardTabMainTotalDepositValueTitle.setObjectName(u"DashboardTabMainTotalDepositValueTitle")
        # self.DashboardTabMainTotalDepositValueTitle.setGeometry(QRect(50, 300, 131, 16))
        # self.DashboardTabMainTotalDepositValueTitle.setFont(font)
        # self.DashboardTabMainTotalWithdrawValueTitle = QLabel(DashboardTabMain)
        # self.DashboardTabMainTotalWithdrawValueTitle.setObjectName(u"DashboardTabMainTotalWithdrawValueTitle")
        # self.DashboardTabMainTotalWithdrawValueTitle.setGeometry(QRect(50, 320, 141, 16))
        # self.DashboardTabMainTotalWithdrawValueTitle.setFont(font)
        self.DashboardTabMainDifferentTokensTradedTitle = QLabel(DashboardTabMain)
        self.DashboardTabMainDifferentTokensTradedTitle.setObjectName(u"DashboardTabMainDifferentTokensTradedTitle")
        self.DashboardTabMainDifferentTokensTradedTitle.setGeometry(QRect(50, 360, 151, 16))
        self.DashboardTabMainDifferentTokensTradedTitle.setFont(font)
        self.DashboardTabMainTradePairsAvailableTitle = QLabel(DashboardTabMain)
        self.DashboardTabMainTradePairsAvailableTitle.setObjectName(u"DashboardTabMainTradePairsAvailableTitle")
        self.DashboardTabMainTradePairsAvailableTitle.setGeometry(QRect(50, 390, 131, 16))
        self.DashboardTabMainTradePairsAvailableTitle.setFont(font)
        self.DashboardTabMainBotWalletValueTextArea = QLabel(DashboardTabMain)
        self.DashboardTabMainBotWalletValueTextArea.setObjectName(u"DashboardTabMainBotWalletValueTextArea")
        self.DashboardTabMainBotWalletValueTextArea.setGeometry(QRect(250, 40, 151, 16))
        self.DashboardTabMainTotalProfitTextArea = QLabel(DashboardTabMain)
        self.DashboardTabMainTotalProfitTextArea.setObjectName(u"DashboardTabMainTotalProfitTextArea")
        self.DashboardTabMainTotalProfitTextArea.setGeometry(QRect(250, 80, 151, 16))
        self.DashboardTabMainActiveTradesTextArea = QLabel(DashboardTabMain)
        self.DashboardTabMainActiveTradesTextArea.setObjectName(u"DashboardTabMainActiveTradesTextArea")
        self.DashboardTabMainActiveTradesTextArea.setGeometry(QRect(250, 120, 151, 16))
        self.DashboardTabMainTradesCreatedTextArea = QLabel(DashboardTabMain)
        self.DashboardTabMainTradesCreatedTextArea.setObjectName(u"DashboardTabMainTradesCreatedTextArea")
        self.DashboardTabMainTradesCreatedTextArea.setGeometry(QRect(250, 160, 151, 16))
        self.DashboardTabMainTradesCancelledTextArea = QLabel(DashboardTabMain)
        self.DashboardTabMainTradesCancelledTextArea.setObjectName(u"DashboardTabMainTradesCancelledTextArea")
        self.DashboardTabMainTradesCancelledTextArea.setGeometry(QRect(250, 180, 151, 16))
        self.DashboardTabMainMostProfitableIndicatorTitle = QLabel(DashboardTabMain)
        self.DashboardTabMainMostProfitableIndicatorTitle.setObjectName(u"DashboardTabMainMostProfitableIndicatorTitle")
        self.DashboardTabMainMostProfitableIndicatorTitle.setGeometry(QRect(50, 420, 151, 16))
        self.DashboardTabMainMostProfitableIndicatorTitle.setFont(font)
        self.DashboardTabMainProfitableTradesTextArea = QLabel(DashboardTabMain)
        self.DashboardTabMainProfitableTradesTextArea.setObjectName(u"DashboardTabMainProfitableTradesTextArea")
        self.DashboardTabMainProfitableTradesTextArea.setGeometry(QRect(250, 220, 151, 16))
        self.DashboardTabMainUnprofitableTradesTextArea = QLabel(DashboardTabMain)
        self.DashboardTabMainUnprofitableTradesTextArea.setObjectName(u"DashboardTabMainUnprofitableTradesTextArea")
        self.DashboardTabMainUnprofitableTradesTextArea.setGeometry(QRect(250, 240, 151, 16))
        self.DashboardTabMainTotalDepositValueTextArea = QLabel(DashboardTabMain)
        self.DashboardTabMainTotalDepositValueTextArea.setObjectName(u"DashboardTabMainTotalDepositValueTextArea")
        self.DashboardTabMainTotalDepositValueTextArea.setGeometry(QRect(250, 300, 151, 16))
        self.DashboardTabMainTotalWithdrawValueTextArea = QLabel(DashboardTabMain)
        self.DashboardTabMainTotalWithdrawValueTextArea.setObjectName(u"DashboardTabMainTotalWithdrawValueTextArea")
        self.DashboardTabMainTotalWithdrawValueTextArea.setGeometry(QRect(250, 320, 151, 16))
        self.DashboardTabMainDifferentTokensTradedTextArea = QLabel(DashboardTabMain)
        self.DashboardTabMainDifferentTokensTradedTextArea.setObjectName(u"DashboardTabMainDifferentTokensTradedTextArea")
        self.DashboardTabMainDifferentTokensTradedTextArea.setGeometry(QRect(250, 360, 151, 16))
        self.DashboardTabMainTradePairsAvailableTextArea = QLabel(DashboardTabMain)
        self.DashboardTabMainTradePairsAvailableTextArea.setObjectName(u"DashboardTabMainTradePairsAvailableTextArea")
        self.DashboardTabMainTradePairsAvailableTextArea.setGeometry(QRect(250, 390, 151, 16))
        self.DashboardTabMainMostProfitableIndicatorTextArea = QLabel(DashboardTabMain)
        self.DashboardTabMainMostProfitableIndicatorTextArea.setObjectName(u"DashboardTabMainMostProfitableIndicatorTextArea")
        self.DashboardTabMainMostProfitableIndicatorTextArea.setGeometry(QRect(250, 420, 151, 16))
        self.DashboardTabMainTotalTradeVolumeTextArea = QLabel(DashboardTabMain)
        self.DashboardTabMainTotalTradeVolumeTextArea.setObjectName(u"DashboardTabMainTotalTradeVolumeTextArea")
        self.DashboardTabMainTotalTradeVolumeTextArea.setGeometry(QRect(250, 470, 151, 16))
        self.DashboardTabMainRecentLogsGroup = QGroupBox(DashboardTabMain)
        self.DashboardTabMainRecentLogsGroup.setObjectName(u"DashboardTabMainRecentLogsGroup")
        self.DashboardTabMainRecentLogsGroup.setGeometry(QRect(420, 20, 361, 471))
        self.DashboardTabMainRecentLogsScrollArea = QScrollArea(self.DashboardTabMainRecentLogsGroup)
        self.DashboardTabMainRecentLogsScrollArea.setObjectName(u"DashboardTabMainRecentLogsScrollArea")
        self.DashboardTabMainRecentLogsScrollArea.setGeometry(QRect(0, 20, 361, 451))
        self.DashboardTabMainRecentLogsScrollArea.setWidgetResizable(True)
        self.scrollAreaWidgetContents_12 = QWidget()
        self.scrollAreaWidgetContents_12.setObjectName(u"scrollAreaWidgetContents_12")
        self.scrollAreaWidgetContents_12.setGeometry(QRect(0, 0, 359, 449))
        self.DashboardTabMainRecentLogsScrollArea.setWidget(self.scrollAreaWidgetContents_12)
        self.DashboardTabMainWinRatioTitle = QLabel(DashboardTabMain)
        self.DashboardTabMainWinRatioTitle.setObjectName(u"DashboardTabMainWinRatioTitle")
        self.DashboardTabMainWinRatioTitle.setGeometry(QRect(50, 260, 141, 16))
        self.DashboardTabMainWinRatioTitle.setFont(font)
        self.DashboardTabMainWinRatioTextArea = QLabel(DashboardTabMain)
        self.DashboardTabMainWinRatioTextArea.setObjectName(u"DashboardTabMainWinRatioTextArea")
        self.DashboardTabMainWinRatioTextArea.setGeometry(QRect(250, 260, 151, 16))
        


    
    def retranslateUi(self, DashboardTabMain):
        # Only update text, not create widgets (already done in setupUi)
        self.DashboardTabMainBotWalletValueTitle.setText(QCoreApplication.translate("DashboardTabMain", u"Bot Wallet Value:", None))
        self.DashboardTabMainActiveTradesTitle.setText(QCoreApplication.translate("DashboardTabMain", u"Active Trades:", None))
        self.DashboardTabMainTradesCreatedTitle.setText(QCoreApplication.translate("DashboardTabMain", u"Trades Created:", None))
        self.DashboardTabMainTradesCancelledTitle.setText(QCoreApplication.translate("DashboardTabMain", u"Trades Cancelled:", None))
        self.DashboardTabMainProfitableTradesTitle.setText(QCoreApplication.translate("DashboardTabMain", u"Profitable Trades:", None))
        self.DashboardTabMainUnprofitableTradesTitle.setText(QCoreApplication.translate("DashboardTabMain", u"Unprofitable trades:", None))
        self.DashboardTabMainTotalTradeVolumeTitle.setText(QCoreApplication.translate("DashboardTabMain", u"Total Trade Volume:", None))
        self.DashboardTabMainTotalProfitTitle.setText(QCoreApplication.translate("DashboardTabMain", u"Total Profit:", None))
        #self.DashboardTabMainTotalDepositValueTitle.setText(QCoreApplication.translate("DashboardTabMain", u"Total Deposit Value:", None))
        # self.DashboardTabMainTotalWithdrawValueTitle.setText(QCoreApplication.translate("DashboardTabMain", u"Total Withdraw Value:", None))
        self.DashboardTabMainDifferentTokensTradedTitle.setText(QCoreApplication.translate("DashboardTabMain", u"Different Tokens Traded:", None))
        self.DashboardTabMainTradePairsAvailableTitle.setText(QCoreApplication.translate("DashboardTabMain", u"Trade Pairs Available:", None))
        self.DashboardTabMainBotWalletValueTextArea.setText(QCoreApplication.translate("DashboardTabMain", u"248,391.679251 XRD", None))
        self.DashboardTabMainTotalProfitTextArea.setText(QCoreApplication.translate("DashboardTabMain", u"448,391.679251 XRD", None))
        self.DashboardTabMainActiveTradesTextArea.setText(QCoreApplication.translate("DashboardTabMain", u"51", None))
        self.DashboardTabMainTradesCreatedTextArea.setText(QCoreApplication.translate("DashboardTabMain", u"93", None))
        self.DashboardTabMainTradesCancelledTextArea.setText(QCoreApplication.translate("DashboardTabMain", u"42", None))
        self.DashboardTabMainMostProfitableIndicatorTitle.setText(QCoreApplication.translate("DashboardTabMain", u"Most Profitable Indicator:", None))
        self.DashboardTabMainProfitableTradesTextArea.setText(QCoreApplication.translate("DashboardTabMain", u"1827", None))
        self.DashboardTabMainUnprofitableTradesTextArea.setText(QCoreApplication.translate("DashboardTabMain", u"703", None))
        self.DashboardTabMainTotalDepositValueTextArea.setText(QCoreApplication.translate("DashboardTabMain", u"100,000 XRD", None))
        self.DashboardTabMainTotalWithdrawValueTextArea.setText(QCoreApplication.translate("DashboardTabMain", u"300,000 XRD", None))
        self.DashboardTabMainDifferentTokensTradedTextArea.setText(QCoreApplication.translate("DashboardTabMain", u"14", None))
        self.DashboardTabMainTradePairsAvailableTextArea.setText(QCoreApplication.translate("DashboardTabMain", u"8", None))
        self.DashboardTabMainMostProfitableIndicatorTextArea.setText(QCoreApplication.translate("DashboardTabMain", u"AI Strategy", None))
        self.DashboardTabMainTotalTradeVolumeTextArea.setText(QCoreApplication.translate("DashboardTabMain", u"37,264,827.348691 XRD", None))
        self.DashboardTabMainRecentLogsGroup.setTitle(QCoreApplication.translate("DashboardTabMain", u" Recent Logs ", None))
        self.DashboardTabMainWinRatioTitle.setText(QCoreApplication.translate("DashboardTabMain", u"Win Ratio:", None))
        self.DashboardTabMainWinRatioTextArea.setText(QCoreApplication.translate("DashboardTabMain", u"72.21 %", None))
