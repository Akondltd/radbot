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
    QTextEdit, QTreeView, QWidget, QVBoxLayout, QHBoxLayout)
from gui import resources_rc

# Toggle between layout-based (True) and legacy setGeometry (False)
USE_RESPONSIVE_LAYOUTS = True

class Ui_TradeHistoryTabMain(object):
    def setupUi(self, TradeHistoryTabMain):
        if USE_RESPONSIVE_LAYOUTS:
            self.setupUi_layouts(TradeHistoryTabMain)
        else:
            self.setupUi_legacy(TradeHistoryTabMain)
    
    def setupUi_layouts(self, TradeHistoryTabMain):
        """Layout-based responsive UI setup"""
        TradeHistoryTabMain.setObjectName(u"TradeHistoryTabMain")
        
        # Main vertical layout
        main_layout = QVBoxLayout(TradeHistoryTabMain)
        main_layout.setContentsMargins(0, 0, 0, 10)
        main_layout.setSpacing(10)
        
        # Tab widget with duration tabs
        self.TradeHistoryTabMainDurationTabs = QTabWidget()
        self.TradeHistoryTabMainDurationTabs.setObjectName(u"TradeHistoryTabMainDurationTabs")
        self.TradeHistoryTabMainDurationTabs.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        
        # Create 4 tabs: Yearly, Monthly, Weekly, Daily
        tab_configs = [
            ("Yearly", "TradeHistoryTabMainYearlySubTab", "TradeHistoryTabMainDurationSubTabYearlyScrollArea",
             "scrollAreaWidgetContents_6", "TradeHistoryTabMainDurationSubTabYearlyNavigationArea"),
            ("Monthly", "TradeHistoryTabMainMonthlySubTab", "TradeHistoryTabMainDurationSubTabMonthlyScrollArea",
             "scrollAreaWidgetContents_5", "TradeHistoryTabDurationSubTabMonthlyNavigationArea"),
            ("Weekly", "TradeHistoryTabMainWeeklySubTab", "TradeHistoryTabMainDurationSubTabWeeklyScrollArea",
             "scrollAreaWidgetContents_4", "TradeHistoryTabMainDurationSubTabWeeklyNavigationArea"),
            ("Daily", "TradeHistoryTabMainDailySubTab", "TradeHistoryTabMainDurationSubTabDailyScrollArea",
             "scrollAreaWidgetContents_3", "TradeHistoryTabMainDurationSubTabDailyNavigationArea")
        ]
        
        # Dictionary to store navigation labels for each tab
        nav_labels = {}
        
        for tab_name, tab_obj, scroll_obj, contents_obj, nav_obj in tab_configs:
            # Create tab widget
            tab = QWidget()
            tab.setObjectName(tab_obj)
            tab_layout = QVBoxLayout(tab)
            tab_layout.setContentsMargins(0, 0, 0, 0)
            tab_layout.setSpacing(0)
            
            # Scroll area for table content (no navigation label here anymore)
            scroll_area = QScrollArea()
            scroll_area.setObjectName(scroll_obj)
            scroll_area.setWidgetResizable(True)
            scroll_contents = QWidget()
            scroll_contents.setObjectName(contents_obj)
            scroll_area.setWidget(scroll_contents)
            tab_layout.addWidget(scroll_area)
            
            # Create navigation label but don't add to tab layout
            # Will be shown/hidden based on active tab
            nav_label = QLabel(f"{tab_name} Back Forth Navigation Area")
            nav_label.setObjectName(nav_obj)
            nav_label.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
            if tab_name == "Daily":
                nav_label.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
            
            # Store references
            setattr(self, scroll_obj, scroll_area)
            setattr(self, contents_obj, scroll_contents)
            setattr(self, nav_obj, nav_label)
            setattr(self, tab_obj, tab)
            nav_labels[self.TradeHistoryTabMainDurationTabs.count()] = nav_label
            
            # Add tab to tab widget
            self.TradeHistoryTabMainDurationTabs.addTab(tab, tab_name)
        
        # Set up corner widget for navigation (left side of tab bar)
        # Create container widget for navigation that switches based on active tab
        self.nav_container = QWidget()
        nav_container_layout = QHBoxLayout(self.nav_container)
        nav_container_layout.setContentsMargins(10, 0, 10, 0)
        nav_container_layout.setSpacing(0)
        
        # Add all navigation labels to container (only one visible at a time)
        for nav_label in nav_labels.values():
            nav_container_layout.addWidget(nav_label)
            nav_label.hide()  # Hide all initially
        
        # Show the navigation label for the default tab (Daily = index 3)
        nav_labels[3].show()
        
        # Set corner widget - use TopRightCorner because tab widget has RightToLeft layout
        # This makes it appear on the visual LEFT side (where empty space is)
        self.TradeHistoryTabMainDurationTabs.setCornerWidget(self.nav_container, Qt.Corner.TopRightCorner)
        
        # Connect tab change to update visible navigation label
        def update_nav_display(index):
            for i, label in nav_labels.items():
                label.setVisible(i == index)
        
        self.TradeHistoryTabMainDurationTabs.currentChanged.connect(update_nav_display)
        
        # Store nav_labels for reference
        self._nav_labels = nav_labels
        
        # Add tab widget to main layout
        main_layout.addWidget(self.TradeHistoryTabMainDurationTabs)
        
        # Export section at bottom
        export_layout = QHBoxLayout()
        export_layout.setSpacing(10)
        
        # Export History Title
        self.TradeHistoryTabMainExportHistoryTitle = QLabel("Export History:")
        self.TradeHistoryTabMainExportHistoryTitle.setObjectName(u"TradeHistoryTabMainExportHistoryTitle")
        export_layout.addWidget(self.TradeHistoryTabMainExportHistoryTitle)
        
        # Start Date label
        self.TradeHistoryTabMainExportHistoryStartDateTitle = QLabel("Start Date and Time")
        self.TradeHistoryTabMainExportHistoryStartDateTitle.setObjectName(u"TradeHistoryTabMainExportHistoryStartDateTitle")
        export_layout.addWidget(self.TradeHistoryTabMainExportHistoryStartDateTitle)
        
        # Start Date input
        self.TradeHistoryTabMainExportHistoryStartDateTimeDateInput = QDateTimeEdit()
        self.TradeHistoryTabMainExportHistoryStartDateTimeDateInput.setObjectName(u"TradeHistoryTabMainExportHistoryStartDateTimeDateInput")
        self.TradeHistoryTabMainExportHistoryStartDateTimeDateInput.setMaximumWidth(194)
        export_layout.addWidget(self.TradeHistoryTabMainExportHistoryStartDateTimeDateInput)
        
        # End Date label
        self.TradeHistoryTabMainExportHistoryEndDateTitle = QLabel(" End Date and Time")
        self.TradeHistoryTabMainExportHistoryEndDateTitle.setObjectName(u"TradeHistoryTabMainExportHistoryEndDateTitle")
        export_layout.addWidget(self.TradeHistoryTabMainExportHistoryEndDateTitle)
        
        # End Date input
        self.TradeHistoryTabMainExportHistoryEndDateTimeDateInput = QDateTimeEdit()
        self.TradeHistoryTabMainExportHistoryEndDateTimeDateInput.setObjectName(u"TradeHistoryTabMainExportHistoryEndDateTimeDateInput")
        self.TradeHistoryTabMainExportHistoryEndDateTimeDateInput.setMaximumWidth(194)
        export_layout.addWidget(self.TradeHistoryTabMainExportHistoryEndDateTimeDateInput)
        
        # Export button
        self.TradeHistoryTabMainExportTradeHistoryButton = QPushButton("Export Trade History")
        self.TradeHistoryTabMainExportTradeHistoryButton.setObjectName(u"TradeHistoryTabMainExportTradeHistoryButton")
        self.TradeHistoryTabMainExportTradeHistoryButton.setMaximumWidth(121)
        export_layout.addWidget(self.TradeHistoryTabMainExportTradeHistoryButton)
        
        # Add stretch to push button to the right
        export_layout.addStretch()
        
        # Add export layout to main layout
        main_layout.addLayout(export_layout)
        
        # Set default tab
        self.TradeHistoryTabMainDurationTabs.setCurrentIndex(3)  # Daily tab
        
        # Call retranslateUi
        self.retranslateUi(TradeHistoryTabMain)
    
    def setupUi_legacy(self, TradeHistoryTabMain):
        """Legacy setGeometry-based UI setup"""
        TradeHistoryTabMain.setObjectName(u"TradeHistoryTabMain")
        self.TradeHistoryTabMainDurationTabs = QTabWidget(TradeHistoryTabMain)
        self.TradeHistoryTabMainDurationTabs.setObjectName(u"TradeHistoryTabMainDurationTabs")
        self.TradeHistoryTabMainDurationTabs.setGeometry(QRect(0, 0, 801, 481))
        self.TradeHistoryTabMainDurationTabs.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        self.TradeHistoryTabMainYearlySubTab = QWidget()
        self.TradeHistoryTabMainYearlySubTab.setObjectName(u"TradeHistoryTabMainYearlySubTab")
        self.TradeHistoryTabMainDurationSubTabYearlyScrollArea = QScrollArea(self.TradeHistoryTabMainYearlySubTab)
        self.TradeHistoryTabMainDurationSubTabYearlyScrollArea.setObjectName(u"TradeHistoryTabMainDurationSubTabYearlyScrollArea")
        self.TradeHistoryTabMainDurationSubTabYearlyScrollArea.setGeometry(QRect(1, 30, 791, 421))
        self.TradeHistoryTabMainDurationSubTabYearlyScrollArea.setWidgetResizable(True)
        self.scrollAreaWidgetContents_6 = QWidget()
        self.scrollAreaWidgetContents_6.setObjectName(u"scrollAreaWidgetContents_6")
        self.scrollAreaWidgetContents_6.setGeometry(QRect(0, 0, 789, 419))
        self.TradeHistoryTabMainDurationSubTabYearlyScrollArea.setWidget(self.scrollAreaWidgetContents_6)
        self.TradeHistoryTabMainDurationSubTabYearlyNavigationArea = QLabel(self.TradeHistoryTabMainYearlySubTab)
        self.TradeHistoryTabMainDurationSubTabYearlyNavigationArea.setObjectName(u"TradeHistoryTabMainDurationSubTabYearlyNavigationArea")
        self.TradeHistoryTabMainDurationSubTabYearlyNavigationArea.setGeometry(QRect(590, 10, 201, 16))
        self.TradeHistoryTabMainDurationTabs.addTab(self.TradeHistoryTabMainYearlySubTab, "")
        self.TradeHistoryTabMainMonthlySubTab = QWidget()
        self.TradeHistoryTabMainMonthlySubTab.setObjectName(u"TradeHistoryTabMainMonthlySubTab")
        self.TradeHistoryTabMainDurationSubTabMonthlyScrollArea = QScrollArea(self.TradeHistoryTabMainMonthlySubTab)
        self.TradeHistoryTabMainDurationSubTabMonthlyScrollArea.setObjectName(u"TradeHistoryTabMainDurationSubTabMonthlyScrollArea")
        self.TradeHistoryTabMainDurationSubTabMonthlyScrollArea.setGeometry(QRect(1, 30, 791, 421))
        self.TradeHistoryTabMainDurationSubTabMonthlyScrollArea.setWidgetResizable(True)
        self.scrollAreaWidgetContents_5 = QWidget()
        self.scrollAreaWidgetContents_5.setObjectName(u"scrollAreaWidgetContents_5")
        self.scrollAreaWidgetContents_5.setGeometry(QRect(0, 0, 789, 419))
        self.TradeHistoryTabMainDurationSubTabMonthlyScrollArea.setWidget(self.scrollAreaWidgetContents_5)
        self.TradeHistoryTabDurationSubTabMonthlyNavigationArea = QLabel(self.TradeHistoryTabMainMonthlySubTab)
        self.TradeHistoryTabDurationSubTabMonthlyNavigationArea.setObjectName(u"TradeHistoryTabDurationSubTabMonthlyNavigationArea")
        self.TradeHistoryTabDurationSubTabMonthlyNavigationArea.setGeometry(QRect(590, 10, 201, 16))
        self.TradeHistoryTabMainDurationTabs.addTab(self.TradeHistoryTabMainMonthlySubTab, "")
        self.TradeHistoryTabMainWeeklySubTab = QWidget()
        self.TradeHistoryTabMainWeeklySubTab.setObjectName(u"TradeHistoryTabMainWeeklySubTab")
        self.TradeHistoryTabMainDurationSubTabWeeklyScrollArea = QScrollArea(self.TradeHistoryTabMainWeeklySubTab)
        self.TradeHistoryTabMainDurationSubTabWeeklyScrollArea.setObjectName(u"TradeHistoryTabMainDurationSubTabWeeklyScrollArea")
        self.TradeHistoryTabMainDurationSubTabWeeklyScrollArea.setGeometry(QRect(1, 30, 791, 421))
        self.TradeHistoryTabMainDurationSubTabWeeklyScrollArea.setWidgetResizable(True)
        self.scrollAreaWidgetContents_4 = QWidget()
        self.scrollAreaWidgetContents_4.setObjectName(u"scrollAreaWidgetContents_4")
        self.scrollAreaWidgetContents_4.setGeometry(QRect(0, 0, 789, 419))
        self.TradeHistoryTabMainDurationSubTabWeeklyScrollArea.setWidget(self.scrollAreaWidgetContents_4)
        self.TradeHistoryTabMainDurationSubTabWeeklyNavigationArea = QLabel(self.TradeHistoryTabMainWeeklySubTab)
        self.TradeHistoryTabMainDurationSubTabWeeklyNavigationArea.setObjectName(u"TradeHistoryTabMainDurationSubTabWeeklyNavigationArea")
        self.TradeHistoryTabMainDurationSubTabWeeklyNavigationArea.setGeometry(QRect(590, 10, 201, 16))
        self.TradeHistoryTabMainDurationTabs.addTab(self.TradeHistoryTabMainWeeklySubTab, "")
        self.TradeHistoryTabMainDailySubTab = QWidget()
        self.TradeHistoryTabMainDailySubTab.setObjectName(u"TradeHistoryTabMainDailySubTab")
        self.TradeHistoryTabMainDurationSubTabDailyScrollArea = QScrollArea(self.TradeHistoryTabMainDailySubTab)
        self.TradeHistoryTabMainDurationSubTabDailyScrollArea.setObjectName(u"TradeHistoryTabMainDurationSubTabDailyScrollArea")
        self.TradeHistoryTabMainDurationSubTabDailyScrollArea.setGeometry(QRect(1, 30, 791, 421))
        self.TradeHistoryTabMainDurationSubTabDailyScrollArea.setWidgetResizable(True)
        self.scrollAreaWidgetContents_3 = QWidget()
        self.scrollAreaWidgetContents_3.setObjectName(u"scrollAreaWidgetContents_3")
        self.scrollAreaWidgetContents_3.setGeometry(QRect(0, 0, 789, 419))
        self.TradeHistoryTabMainDurationSubTabDailyScrollArea.setWidget(self.scrollAreaWidgetContents_3)
        self.TradeHistoryTabMainDurationSubTabDailyNavigationArea = QLabel(self.TradeHistoryTabMainDailySubTab)
        self.TradeHistoryTabMainDurationSubTabDailyNavigationArea.setObjectName(u"TradeHistoryTabMainDurationSubTabDailyNavigationArea")
        self.TradeHistoryTabMainDurationSubTabDailyNavigationArea.setGeometry(QRect(590, 10, 201, 16))
        self.TradeHistoryTabMainDurationSubTabDailyNavigationArea.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        self.TradeHistoryTabMainDurationTabs.addTab(self.TradeHistoryTabMainDailySubTab, "")
        self.TradeHistoryTabMainExportHistoryTitle = QLabel(TradeHistoryTabMain)
        self.TradeHistoryTabMainExportHistoryTitle.setObjectName(u"TradeHistoryTabMainExportHistoryTitle")
        self.TradeHistoryTabMainExportHistoryTitle.setGeometry(QRect(10, 480, 81, 16))
        self.TradeHistoryTabMainExportHistoryStartDateTimeDateInput = QDateTimeEdit(TradeHistoryTabMain)
        self.TradeHistoryTabMainExportHistoryStartDateTimeDateInput.setObjectName(u"TradeHistoryTabMainExportHistoryStartDateTimeDateInput")
        self.TradeHistoryTabMainExportHistoryStartDateTimeDateInput.setGeometry(QRect(120, 500, 194, 22))
        self.TradeHistoryTabMainExportHistoryEndDateTimeDateInput = QDateTimeEdit(TradeHistoryTabMain)
        self.TradeHistoryTabMainExportHistoryEndDateTimeDateInput.setObjectName(u"TradeHistoryTabMainExportHistoryEndDateTimeDateInput")
        self.TradeHistoryTabMainExportHistoryEndDateTimeDateInput.setGeometry(QRect(460, 500, 194, 22))
        self.TradeHistoryTabMainExportHistoryStartDateTitle = QLabel(TradeHistoryTabMain)
        self.TradeHistoryTabMainExportHistoryStartDateTitle.setObjectName(u"TradeHistoryTabMainExportHistoryStartDateTitle")
        self.TradeHistoryTabMainExportHistoryStartDateTitle.setGeometry(QRect(10, 502, 111, 16))
        self.TradeHistoryTabMainExportHistoryEndDateTitle = QLabel(TradeHistoryTabMain)
        self.TradeHistoryTabMainExportHistoryEndDateTitle.setObjectName(u"TradeHistoryTabMainExportHistoryEndDateTitle")
        self.TradeHistoryTabMainExportHistoryEndDateTitle.setGeometry(QRect(350, 502, 111, 16))
        self.TradeHistoryTabMainExportTradeHistoryButton = QPushButton(TradeHistoryTabMain)
        self.TradeHistoryTabMainExportTradeHistoryButton.setObjectName(u"TradeHistoryTabMainExportTradeHistoryButton")
        self.TradeHistoryTabMainExportTradeHistoryButton.setGeometry(QRect(670, 498, 121, 24))
        
        self.TradeHistoryTabMainDurationTabs.setCurrentIndex(3)
        
        self.retranslateUi(TradeHistoryTabMain)

    def retranslateUi(self, TradeHistoryTabMain):
        self.TradeHistoryTabMainDurationSubTabYearlyNavigationArea.setText(QCoreApplication.translate("TradeHistoryTabMain", u"Yearly Back Forth Navigation Area", None))
        self.TradeHistoryTabMainDurationTabs.setTabText(self.TradeHistoryTabMainDurationTabs.indexOf(self.TradeHistoryTabMainYearlySubTab), QCoreApplication.translate("TradeHistoryTabMain", u"Yearly", None))
        self.TradeHistoryTabDurationSubTabMonthlyNavigationArea.setText(QCoreApplication.translate("TradeHistoryTabMain", u"Monthly Back Forth Navigation Area", None))
        self.TradeHistoryTabMainDurationTabs.setTabText(self.TradeHistoryTabMainDurationTabs.indexOf(self.TradeHistoryTabMainMonthlySubTab), QCoreApplication.translate("TradeHistoryTabMain", u"Monthly", None))
        self.TradeHistoryTabMainDurationSubTabWeeklyNavigationArea.setText(QCoreApplication.translate("TradeHistoryTabMain", u"Weekly Back Forth Navigation Area", None))
        self.TradeHistoryTabMainDurationTabs.setTabText(self.TradeHistoryTabMainDurationTabs.indexOf(self.TradeHistoryTabMainWeeklySubTab), QCoreApplication.translate("TradeHistoryTabMain", u"Weekly", None))
        self.TradeHistoryTabMainDurationSubTabDailyNavigationArea.setText(QCoreApplication.translate("TradeHistoryTabMain", u"Daily Back Forth Navigation Area", None))
        self.TradeHistoryTabMainDurationTabs.setTabText(self.TradeHistoryTabMainDurationTabs.indexOf(self.TradeHistoryTabMainDailySubTab), QCoreApplication.translate("TradeHistoryTabMain", u"Daily", None))
        self.TradeHistoryTabMainExportHistoryTitle.setText(QCoreApplication.translate("TradeHistoryTabMain", u"Export History:", None))
        self.TradeHistoryTabMainExportHistoryStartDateTitle.setText(QCoreApplication.translate("TradeHistoryTabMain", u"Start Date and Time", None))
        self.TradeHistoryTabMainExportHistoryEndDateTitle.setText(QCoreApplication.translate("TradeHistoryTabMain", u" End Date and Time", None))
        self.TradeHistoryTabMainExportTradeHistoryButton.setText(QCoreApplication.translate("TradeHistoryTabMain", u"Export Trade History", None))
