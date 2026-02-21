from PySide6.QtCore import QCoreApplication, QRect, Qt
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QCheckBox, QGroupBox, QLabel, QLineEdit,
    QPushButton, QScrollArea, QStackedWidget, QWidget, QDial, QRadioButton,
    QVBoxLayout, QHBoxLayout, QGridLayout, QFormLayout, QSpacerItem, QSizePolicy
)

from gui import resources_rc
from gui.components.toggle_switch import ToggleSwitch

# Toggle between responsive layouts and legacy setGeometry positioning  
USE_RESPONSIVE_LAYOUTS = True  # Phases 1-5 COMPLETE: All pages converted! (List, Delete, Information, Edit)

class Ui_ActiveTradesTabMain(object):
    def setupUi(self, ActiveTradesTabMain):
        if USE_RESPONSIVE_LAYOUTS:
            self._setupUi_responsive(ActiveTradesTabMain)
        else:
            self._setupUi_legacy(ActiveTradesTabMain)
    
    def _setupUi_responsive(self, ActiveTradesTabMain):
        """Responsive layout implementation using QLayouts"""
        ActiveTradesTabMain.setObjectName("ActiveTradesTabMain")
        
        # Main container layout
        main_layout = QVBoxLayout(ActiveTradesTabMain)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # Stacked widget for pages
        self.ActiveTradesTabMainListTradesStackedWidget = QStackedWidget()
        self.ActiveTradesTabMainListTradesStackedWidget.setObjectName("ActiveTradesTabMainListTradesStackedWidget")
        main_layout.addWidget(self.ActiveTradesTabMainListTradesStackedWidget)
        
        # ====== LIST PAGE (Responsive) ======
        self.List = QWidget()
        self.List.setObjectName("List")
        
        list_layout = QVBoxLayout(self.List)
        list_layout.setContentsMargins(10, 10, 10, 10)
        list_layout.setSpacing(0)
        
        self.ActiveTradesTabMainListTradesStackedWidgetListScrollArea = QScrollArea()
        self.ActiveTradesTabMainListTradesStackedWidgetListScrollArea.setObjectName("ActiveTradesTabMainListTradesStackedWidgetListScrollArea")
        self.ActiveTradesTabMainListTradesStackedWidgetListScrollArea.setWidgetResizable(True)
        
        self.scrollAreaWidgetContents_7 = QWidget()
        self.scrollAreaWidgetContents_7.setObjectName("scrollAreaWidgetContents_7")
        self.ActiveTradesTabMainListTradesStackedWidgetListScrollArea.setWidget(self.scrollAreaWidgetContents_7)
        
        list_layout.addWidget(self.ActiveTradesTabMainListTradesStackedWidgetListScrollArea)
        
        self.ActiveTradesTabMainListTradesStackedWidget.addWidget(self.List)
        
        # ====== DELETE PAGE (Responsive) ======
        self.Delete = QWidget()
        self.Delete.setObjectName("Delete")
        
        delete_main_layout = QVBoxLayout(self.Delete)
        delete_main_layout.setContentsMargins(20, 20, 20, 20)
        
        # Vertical spacer to center content
        delete_main_layout.addStretch(1)
        
        # Title
        font_delete = QFont()
        font_delete.setPointSize(24)
        font_delete.setBold(True)
        
        self.ActiveTradesTabMainListTradesStackedWidgetDeleteTitle = QLabel()
        self.ActiveTradesTabMainListTradesStackedWidgetDeleteTitle.setObjectName("ActiveTradesTabMainListTradesStackedWidgetDeleteTitle")
        self.ActiveTradesTabMainListTradesStackedWidgetDeleteTitle.setFont(font_delete)
        self.ActiveTradesTabMainListTradesStackedWidgetDeleteTitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        delete_main_layout.addWidget(self.ActiveTradesTabMainListTradesStackedWidgetDeleteTitle)
        
        delete_main_layout.addSpacing(20)
        
        # Description text
        self.ActiveTradesTabMainListTradesStackedWidgetDeleteText = QLabel()
        self.ActiveTradesTabMainListTradesStackedWidgetDeleteText.setObjectName("ActiveTradesTabMainListTradesStackedWidgetDeleteText")
        self.ActiveTradesTabMainListTradesStackedWidgetDeleteText.setWordWrap(True)
        self.ActiveTradesTabMainListTradesStackedWidgetDeleteText.setAlignment(Qt.AlignmentFlag.AlignCenter)
        # self.ActiveTradesTabMainListTradesStackedWidgetDeleteText.setMaximumWidth(600)
        self.ActiveTradesTabMainListTradesStackedWidgetDeleteText.setMinimumSize(350, 71)
        delete_main_layout.addWidget(self.ActiveTradesTabMainListTradesStackedWidgetDeleteText, 0, Qt.AlignmentFlag.AlignCenter)
        
        delete_main_layout.addSpacing(40)
        
        # Buttons row
        button_row = QHBoxLayout()
        button_row.addStretch()
        
        self.ActiveTradesTabMainListTradesStackedWidgetDeleteBackButton = QPushButton()
        self.ActiveTradesTabMainListTradesStackedWidgetDeleteBackButton.setObjectName("ActiveTradesTabMainListTradesStackedWidgetDeleteBackButton")
        self.ActiveTradesTabMainListTradesStackedWidgetDeleteBackButton.setMinimumSize(120, 31)
        button_row.addWidget(self.ActiveTradesTabMainListTradesStackedWidgetDeleteBackButton)
        
        button_row.addSpacing(40)
        
        self.ActiveTradesTabMainListTradesStackedWidgetDeleteDeletButton = QPushButton()
        self.ActiveTradesTabMainListTradesStackedWidgetDeleteDeletButton.setObjectName("ActiveTradesTabMainListTradesStackedWidgetDeleteDeletButton")
        self.ActiveTradesTabMainListTradesStackedWidgetDeleteDeletButton.setMinimumSize(180, 31)
        button_row.addWidget(self.ActiveTradesTabMainListTradesStackedWidgetDeleteDeletButton)
        
        button_row.addStretch()
        delete_main_layout.addLayout(button_row)
        
        # Bottom spacer
        delete_main_layout.addStretch(2)
        
        self.ActiveTradesTabMainListTradesStackedWidget.addWidget(self.Delete)
        
        # ====== INFORMATION PAGE (Responsive) ======
        self.Information = QWidget()
        self.Information.setObjectName("Information")
        
        info_main_layout = QHBoxLayout(self.Information)
        info_main_layout.setContentsMargins(20, 20, 20, 20)
        info_main_layout.setSpacing(20)
        
        # LEFT: Trade Information Group
        font_bold = QFont()
        font_bold.setBold(True)
        
        self.ActiveTradesTabMainListTradesStackedWidgetInformationTradeInformationGroup = QGroupBox(" Trade Information ")
        self.ActiveTradesTabMainListTradesStackedWidgetInformationTradeInformationGroup.setObjectName("ActiveTradesTabMainListTradesStackedWidgetInformationTradeInformationGroup")
        self.ActiveTradesTabMainListTradesStackedWidgetInformationTradeInformationGroup.setMaximumWidth(350)
        
        # Use QFormLayout for label-value pairs
        info_form = QFormLayout(self.ActiveTradesTabMainListTradesStackedWidgetInformationTradeInformationGroup)
        info_form.setContentsMargins(15, 20, 15, 20)
        info_form.setVerticalSpacing(15)
        info_form.setHorizontalSpacing(20)
        
        # Trade ID
        self.ActiveTradesTabMainListTradesStackedWidgetInformationTradeInformationGroupTradeIdTitle = QLabel("Trade ID:")
        self.ActiveTradesTabMainListTradesStackedWidgetInformationTradeInformationGroupTradeIdTitle.setObjectName("ActiveTradesTabMainListTradesStackedWidgetInformationTradeInformationGroupTradeIdTitle")
        self.ActiveTradesTabMainListTradesStackedWidgetInformationTradeInformationGroupTradeIdTitle.setFont(font_bold)
        
        self.ActiveTradesTabMainListTradesStackedWidgetInformationTradeInformationGroupTradeIdTextArea = QLabel("23")
        self.ActiveTradesTabMainListTradesStackedWidgetInformationTradeInformationGroupTradeIdTextArea.setObjectName("ActiveTradesTabMainListTradesStackedWidgetInformationTradeInformationGroupTradeIdTextArea")
        
        info_form.addRow(self.ActiveTradesTabMainListTradesStackedWidgetInformationTradeInformationGroupTradeIdTitle, 
                        self.ActiveTradesTabMainListTradesStackedWidgetInformationTradeInformationGroupTradeIdTextArea)
        
        # Creation Date
        self.ActiveTradesTabMainListTradesStackedWidgetInformationTradeInformationGroupCreationDateTitle = QLabel("Creation Date:")
        self.ActiveTradesTabMainListTradesStackedWidgetInformationTradeInformationGroupCreationDateTitle.setObjectName("ActiveTradesTabMainListTradesStackedWidgetInformationTradeInformationGroupCreationDateTitle")
        self.ActiveTradesTabMainListTradesStackedWidgetInformationTradeInformationGroupCreationDateTitle.setFont(font_bold)
        
        self.ActiveTradesTabMainListTradesStackedWidgetInformationTradeInformationGroupCreationDateTextArea = QLabel()
        self.ActiveTradesTabMainListTradesStackedWidgetInformationTradeInformationGroupCreationDateTextArea.setObjectName("ActiveTradesTabMainListTradesStackedWidgetInformationTradeInformationGroupCreationDateTextArea")
        
        info_form.addRow(self.ActiveTradesTabMainListTradesStackedWidgetInformationTradeInformationGroupCreationDateTitle,
                        self.ActiveTradesTabMainListTradesStackedWidgetInformationTradeInformationGroupCreationDateTextArea)
        
        # Creation Value
        self.ActiveTradesTabMainListTradesStackedWidgetInformationTradeInformationGroupCreationValueTitle = QLabel("Creation Value:")
        self.ActiveTradesTabMainListTradesStackedWidgetInformationTradeInformationGroupCreationValueTitle.setObjectName("ActiveTradesTabMainListTradesStackedWidgetInformationTradeInformationGroupCreationValueTitle")
        self.ActiveTradesTabMainListTradesStackedWidgetInformationTradeInformationGroupCreationValueTitle.setFont(font_bold)
        
        self.ActiveTradesTabMainListTradesStackedWidgetInformationTradeInformationGroupCreationValueTextArea = QLabel()
        self.ActiveTradesTabMainListTradesStackedWidgetInformationTradeInformationGroupCreationValueTextArea.setObjectName("ActiveTradesTabMainListTradesStackedWidgetInformationTradeInformationGroupCreationValueTextArea")
        
        info_form.addRow(self.ActiveTradesTabMainListTradesStackedWidgetInformationTradeInformationGroupCreationValueTitle,
                        self.ActiveTradesTabMainListTradesStackedWidgetInformationTradeInformationGroupCreationValueTextArea)
        
        # Times Flipped
        self.ActiveTradesTabMainListTradesStackedWidgetInformationTradeInformationGroupTimesFlippedTitle = QLabel("Times Flipped:")
        self.ActiveTradesTabMainListTradesStackedWidgetInformationTradeInformationGroupTimesFlippedTitle.setObjectName("ActiveTradesTabMainListTradesStackedWidgetInformationTradeInformationGroupTimesFlippedTitle")
        self.ActiveTradesTabMainListTradesStackedWidgetInformationTradeInformationGroupTimesFlippedTitle.setFont(font_bold)
        
        self.ActiveTradesTabMainListTradesStackedWidgetInformationTradeInformationGroupTimesFlippedTextArea = QLabel()
        self.ActiveTradesTabMainListTradesStackedWidgetInformationTradeInformationGroupTimesFlippedTextArea.setObjectName("ActiveTradesTabMainListTradesStackedWidgetInformationTradeInformationGroupTimesFlippedTextArea")
        
        info_form.addRow(self.ActiveTradesTabMainListTradesStackedWidgetInformationTradeInformationGroupTimesFlippedTitle,
                        self.ActiveTradesTabMainListTradesStackedWidgetInformationTradeInformationGroupTimesFlippedTextArea)
        
        # Profitable Flips
        self.ActiveTradesTabMainListTradesStackedWidgetInformationTradeInformationGroupProfitableFlipsTitle = QLabel("Profitable Flips:")
        self.ActiveTradesTabMainListTradesStackedWidgetInformationTradeInformationGroupProfitableFlipsTitle.setObjectName("ActiveTradesTabMainListTradesStackedWidgetInformationTradeInformationGroupProfitableFlipsTitle")
        self.ActiveTradesTabMainListTradesStackedWidgetInformationTradeInformationGroupProfitableFlipsTitle.setFont(font_bold)
        
        self.ActiveTradesTabMainListTradesStackedWidgetInformationTradeInformationGroupProfitableFlipsTextArea = QLabel()
        self.ActiveTradesTabMainListTradesStackedWidgetInformationTradeInformationGroupProfitableFlipsTextArea.setObjectName("ActiveTradesTabMainListTradesStackedWidgetInformationTradeInformationGroupProfitableFlipsTextArea")
        
        info_form.addRow(self.ActiveTradesTabMainListTradesStackedWidgetInformationTradeInformationGroupProfitableFlipsTitle,
                        self.ActiveTradesTabMainListTradesStackedWidgetInformationTradeInformationGroupProfitableFlipsTextArea)
        
        # Unprofitable Flips
        self.ActiveTradesTabMainListTradesStackedWidgetInformationTradeInformationGroupUnprofitablFlipsTitle = QLabel("Unprofitable Flips:")
        self.ActiveTradesTabMainListTradesStackedWidgetInformationTradeInformationGroupUnprofitablFlipsTitle.setObjectName("ActiveTradesTabMainListTradesStackedWidgetInformationTradeInformationGroupUnprofitablFlipsTitle")
        self.ActiveTradesTabMainListTradesStackedWidgetInformationTradeInformationGroupUnprofitablFlipsTitle.setFont(font_bold)
        
        self.ActiveTradesTabMainListTradesStackedWidgetInformationTradeInformationGroupUnprofitablFlipsTextArea = QLabel()
        self.ActiveTradesTabMainListTradesStackedWidgetInformationTradeInformationGroupUnprofitablFlipsTextArea.setObjectName("ActiveTradesTabMainListTradesStackedWidgetInformationTradeInformationGroupUnprofitablFlipsTextArea")
        
        info_form.addRow(self.ActiveTradesTabMainListTradesStackedWidgetInformationTradeInformationGroupUnprofitablFlipsTitle,
                        self.ActiveTradesTabMainListTradesStackedWidgetInformationTradeInformationGroupUnprofitablFlipsTextArea)
        
        # Win Ratio
        self.ActiveTradesTabMainListTradesStackedWidgetInformationTradeInformationGroupWinRatioTitle = QLabel("Win Ratio:")
        self.ActiveTradesTabMainListTradesStackedWidgetInformationTradeInformationGroupWinRatioTitle.setObjectName("ActiveTradesTabMainListTradesStackedWidgetInformationTradeInformationGroupWinRatioTitle")
        self.ActiveTradesTabMainListTradesStackedWidgetInformationTradeInformationGroupWinRatioTitle.setFont(font_bold)
        
        self.ActiveTradesTabMainListTradesStackedWidgetInformationTradeInformationGroupWinRatioTextArea = QLabel()
        self.ActiveTradesTabMainListTradesStackedWidgetInformationTradeInformationGroupWinRatioTextArea.setObjectName("ActiveTradesTabMainListTradesStackedWidgetInformationTradeInformationGroupWinRatioTextArea")
        
        info_form.addRow(self.ActiveTradesTabMainListTradesStackedWidgetInformationTradeInformationGroupWinRatioTitle,
                        self.ActiveTradesTabMainListTradesStackedWidgetInformationTradeInformationGroupWinRatioTextArea)
        
        # Total Profit
        self.ActiveTradesTabMainListTradesStackedWidgetInformationTradeInformationGroupTotalProfitTitle = QLabel("Total Profit:")
        self.ActiveTradesTabMainListTradesStackedWidgetInformationTradeInformationGroupTotalProfitTitle.setObjectName("ActiveTradesTabMainListTradesStackedWidgetInformationTradeInformationGroupTotalProfitTitle")
        self.ActiveTradesTabMainListTradesStackedWidgetInformationTradeInformationGroupTotalProfitTitle.setFont(font_bold)
        
        self.ActiveTradesTabMainListTradesStackedWidgetInformationTradeInformationGroupTotalProfitTextArea = QLabel()
        self.ActiveTradesTabMainListTradesStackedWidgetInformationTradeInformationGroupTotalProfitTextArea.setObjectName("ActiveTradesTabMainListTradesStackedWidgetInformationTradeInformationGroupTotalProfitTextArea")
        
        info_form.addRow(self.ActiveTradesTabMainListTradesStackedWidgetInformationTradeInformationGroupTotalProfitTitle,
                        self.ActiveTradesTabMainListTradesStackedWidgetInformationTradeInformationGroupTotalProfitTextArea)
        
        # Trade Volume
        self.ActiveTradesTabMainListTradesStackedWidgetInformationTradeInformationGroupTradeVolumeTitle = QLabel("Trade Volume:")
        self.ActiveTradesTabMainListTradesStackedWidgetInformationTradeInformationGroupTradeVolumeTitle.setObjectName("ActiveTradesTabMainListTradesStackedWidgetInformationTradeInformationGroupTradeVolumeTitle")
        self.ActiveTradesTabMainListTradesStackedWidgetInformationTradeInformationGroupTradeVolumeTitle.setFont(font_bold)
        
        self.ActiveTradesTabMainListTradesStackedWidgetInformationTradeInformationGroupTradeVolumeTextArea = QLabel()
        self.ActiveTradesTabMainListTradesStackedWidgetInformationTradeInformationGroupTradeVolumeTextArea.setObjectName("ActiveTradesTabMainListTradesStackedWidgetInformationTradeInformationGroupTradeVolumeTextArea")
        
        info_form.addRow(self.ActiveTradesTabMainListTradesStackedWidgetInformationTradeInformationGroupTradeVolumeTitle,
                        self.ActiveTradesTabMainListTradesStackedWidgetInformationTradeInformationGroupTradeVolumeTextArea)
        
        # Indicator Used
        self.ActiveTradesTabMainListTradesStackedWidgetInformationTradeInformationGroupIndicatorUsedTitle = QLabel("Indicator Used:")
        self.ActiveTradesTabMainListTradesStackedWidgetInformationTradeInformationGroupIndicatorUsedTitle.setObjectName("ActiveTradesTabMainListTradesStackedWidgetInformationTradeInformationGroupIndicatorUsedTitle")
        self.ActiveTradesTabMainListTradesStackedWidgetInformationTradeInformationGroupIndicatorUsedTitle.setFont(font_bold)
        
        self.ActiveTradesTabMainListTradesStackedWidgetInformationTradeInformationGroupIndicatorUsedTextArea = QLabel()
        self.ActiveTradesTabMainListTradesStackedWidgetInformationTradeInformationGroupIndicatorUsedTextArea.setObjectName("ActiveTradesTabMainListTradesStackedWidgetInformationTradeInformationGroupIndicatorUsedTextArea")
        
        info_form.addRow(self.ActiveTradesTabMainListTradesStackedWidgetInformationTradeInformationGroupIndicatorUsedTitle,
                        self.ActiveTradesTabMainListTradesStackedWidgetInformationTradeInformationGroupIndicatorUsedTextArea)
        
        # Small fixed spacer before current value
        info_form.addItem(QSpacerItem(20, 10, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Fixed))
        
        # Current Trade Value Title
        self.ActiveTradesTabMainListTradesStackedWidgetInformationTradeInformationGroupCurrentTradeValueTitle = QLabel("Current Trade Value:")
        self.ActiveTradesTabMainListTradesStackedWidgetInformationTradeInformationGroupCurrentTradeValueTitle.setObjectName("ActiveTradesTabMainListTradesStackedWidgetInformationTradeInformationGroupCurrentTradeValueTitle")
        self.ActiveTradesTabMainListTradesStackedWidgetInformationTradeInformationGroupCurrentTradeValueTitle.setFont(font_bold)
        info_form.addRow(self.ActiveTradesTabMainListTradesStackedWidgetInformationTradeInformationGroupCurrentTradeValueTitle)
        
        # Current Trade Value (large display)
        current_value_row = QHBoxLayout()
        font_large = QFont()
        font_large.setPointSize(14)
        
        self.ActiveTradesTabMainListTradesStackedWidgetInformationTradeInformationGroupCurrentTradeValueTextArea = QLabel()
        self.ActiveTradesTabMainListTradesStackedWidgetInformationTradeInformationGroupCurrentTradeValueTextArea.setObjectName("ActiveTradesTabMainListTradesStackedWidgetInformationTradeInformationGroupCurrentTradeValueTextArea")
        self.ActiveTradesTabMainListTradesStackedWidgetInformationTradeInformationGroupCurrentTradeValueTextArea.setFont(font_large)
        self.ActiveTradesTabMainListTradesStackedWidgetInformationTradeInformationGroupCurrentTradeValueTextArea.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        
        self.ActiveTradesTabMainListTradesStackedWidgetInformationTradeInformationGroupCurrentTradeValueTickerTextArea = QLabel()
        self.ActiveTradesTabMainListTradesStackedWidgetInformationTradeInformationGroupCurrentTradeValueTickerTextArea.setObjectName("ActiveTradesTabMainListTradesStackedWidgetInformationTradeInformationGroupCurrentTradeValueTickerTextArea")
        self.ActiveTradesTabMainListTradesStackedWidgetInformationTradeInformationGroupCurrentTradeValueTickerTextArea.setFont(font_large)
        
        current_value_row.addWidget(self.ActiveTradesTabMainListTradesStackedWidgetInformationTradeInformationGroupCurrentTradeValueTextArea)
        current_value_row.addWidget(self.ActiveTradesTabMainListTradesStackedWidgetInformationTradeInformationGroupCurrentTradeValueTickerTextArea)
        current_value_row.addStretch()
        
        info_form.addRow(current_value_row)
        
        # Add stats group to left side (30% width)
        info_main_layout.addWidget(self.ActiveTradesTabMainListTradesStackedWidgetInformationTradeInformationGroup, 30)
        
        # RIGHT COLUMN: Chart + Button (70% width)
        right_column = QVBoxLayout()
        right_column.setSpacing(10)
        
        # Chart area (takes most of the space)
        chart_container = QVBoxLayout()
        chart_container.setSpacing(5)
        
        # Chart placeholder (will be replaced by logic file)
        self.ActiveTradesTabMainListTradesStackedWidgetInformationChartPlaceholder = QWidget()
        self.ActiveTradesTabMainListTradesStackedWidgetInformationChartPlaceholder.setObjectName("ActiveTradesTabMainListTradesStackedWidgetInformationChartPlaceholder")
        self.ActiveTradesTabMainListTradesStackedWidgetInformationChartPlaceholder.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        chart_container.addWidget(self.ActiveTradesTabMainListTradesStackedWidgetInformationChartPlaceholder)
        
        # Chart description text below chart
        self.ActiveTradesTabMainListTradesStackedWidgetInformationChartText = QLabel()
        self.ActiveTradesTabMainListTradesStackedWidgetInformationChartText.setObjectName("ActiveTradesTabMainListTradesStackedWidgetInformationChartText")
        self.ActiveTradesTabMainListTradesStackedWidgetInformationChartText.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.ActiveTradesTabMainListTradesStackedWidgetInformationChartText.setWordWrap(True)
        chart_container.addWidget(self.ActiveTradesTabMainListTradesStackedWidgetInformationChartText)
        
        right_column.addLayout(chart_container, 1)  # Chart takes most space
        
        # Button row at bottom of right column
        button_row = QHBoxLayout()
        
        # Placeholder for icon widget (will be replaced by logic file)
        self.ActiveTradesTabMainListTradesStackedWidgetInformationIconPlaceholder = QWidget()
        self.ActiveTradesTabMainListTradesStackedWidgetInformationIconPlaceholder.setObjectName("ActiveTradesTabMainListTradesStackedWidgetInformationIconPlaceholder")
        button_row.addWidget(self.ActiveTradesTabMainListTradesStackedWidgetInformationIconPlaceholder)
        
        button_row.addStretch()
        
        self.ActiveTradesTabMainListTradesStackedWidgetInformationBackToTradesListButton = QPushButton()
        self.ActiveTradesTabMainListTradesStackedWidgetInformationBackToTradesListButton.setObjectName("ActiveTradesTabMainListTradesStackedWidgetInformationBackToTradesListButton")
        self.ActiveTradesTabMainListTradesStackedWidgetInformationBackToTradesListButton.setMinimumSize(150, 40)
        button_row.addWidget(self.ActiveTradesTabMainListTradesStackedWidgetInformationBackToTradesListButton)
        
        right_column.addLayout(button_row, 0)  # Button row minimal space
        
        info_main_layout.addLayout(right_column, 70)
        
        self.ActiveTradesTabMainListTradesStackedWidget.addWidget(self.Information)
        
        # ====== EDIT PAGE (Responsive) ======
        self.Edit = QWidget()
        self.Edit.setObjectName("Edit")
        
        edit_main_layout = QVBoxLayout(self.Edit)
        edit_main_layout.setContentsMargins(10, 10, 10, 10)
        edit_main_layout.setSpacing(10)
        
        # --- TOP SECTION (~43% height) ---
        top_section = QHBoxLayout()
        top_section.setSpacing(15)
        
        # LEFT: Edit Trade Information Group (30% width)
        font_bold = QFont()
        font_bold.setBold(True)
        
        self.ActiveTradesTabMainListTradesStackedWidgetEditEditTradeInformationGroup = QGroupBox(" Edit Trade Information")
        self.ActiveTradesTabMainListTradesStackedWidgetEditEditTradeInformationGroup.setObjectName("ActiveTradesTabMainListTradesStackedWidgetEditEditTradeInformationGroup")
        self.ActiveTradesTabMainListTradesStackedWidgetEditEditTradeInformationGroup.setMaximumWidth(250)
        
        edit_info_layout = QVBoxLayout(self.ActiveTradesTabMainListTradesStackedWidgetEditEditTradeInformationGroup)
        edit_info_layout.setContentsMargins(10, 15, 10, 10)
        edit_info_layout.setSpacing(10)
        
        # Trade ID (read-only)
        trade_id_row = QHBoxLayout()
        self.ActiveTradesTabMainListTradesStackedWidgetEditEditTradeInformationGroupTradeIDTitle = QLabel("Trade ID:")
        self.ActiveTradesTabMainListTradesStackedWidgetEditEditTradeInformationGroupTradeIDTitle.setFont(font_bold)
        self.ActiveTradesTabMainListTradesStackedWidgetEditEditTradeInformationGroupTradeIDTextArea = QLabel("23")
        trade_id_row.addWidget(self.ActiveTradesTabMainListTradesStackedWidgetEditEditTradeInformationGroupTradeIDTitle)
        trade_id_row.addWidget(self.ActiveTradesTabMainListTradesStackedWidgetEditEditTradeInformationGroupTradeIDTextArea)
        trade_id_row.addStretch()
        edit_info_layout.addLayout(trade_id_row)
        
        # Trade Pair (read-only)
        trade_pair_row = QHBoxLayout()
        self.ActiveTradesTabMainListTradesStackedWidgetEditEditTradeInformationGroupTradePairTitle = QLabel("Trade Pair:")
        self.ActiveTradesTabMainListTradesStackedWidgetEditEditTradeInformationGroupTradePairTitle.setFont(font_bold)
        self.ActiveTradesTabMainListTradesStackedWidgetEditEditTradeInformationGroupTradePairTextArea = QLabel("XRD-xUSDC")
        trade_pair_row.addWidget(self.ActiveTradesTabMainListTradesStackedWidgetEditEditTradeInformationGroupTradePairTitle)
        trade_pair_row.addWidget(self.ActiveTradesTabMainListTradesStackedWidgetEditEditTradeInformationGroupTradePairTextArea)
        trade_pair_row.addStretch()
        edit_info_layout.addLayout(trade_pair_row)
        
        # Tokens (read-only)
        tokens_row = QHBoxLayout()
        self.ActiveTradesTabMainListTradesStackedWidgetEditEditTradeInformationGroupTokensTitle = QLabel("Tokens:")
        self.ActiveTradesTabMainListTradesStackedWidgetEditEditTradeInformationGroupTokensTitle.setFont(font_bold)
        self.ActiveTradesTabMainListTradesStackedWidgetEditEditTradeInformationGroupTokensField = QLabel("123,456")
        self.ActiveTradesTabMainListTradesStackedWidgetEditEditTradeInformationGroupTokensTicker = QLabel("XRD")
        tokens_row.addWidget(self.ActiveTradesTabMainListTradesStackedWidgetEditEditTradeInformationGroupTokensTitle)
        tokens_row.addWidget(self.ActiveTradesTabMainListTradesStackedWidgetEditEditTradeInformationGroupTokensField)
        tokens_row.addWidget(self.ActiveTradesTabMainListTradesStackedWidgetEditEditTradeInformationGroupTokensTicker)
        tokens_row.addStretch()
        edit_info_layout.addLayout(tokens_row)
        
        # Stop Loss (editable)
        stop_loss_row = QHBoxLayout()
        self.ActiveTradesTabMainListTradesStackedWidgetEditEditTradeInformationGroupStopLossTitle = QLabel("Stop Loss:")
        self.ActiveTradesTabMainListTradesStackedWidgetEditEditTradeInformationGroupStopLossTitle.setFont(font_bold)
        self.ActiveTradesTabMainListTradesStackedWidgetEditEditTradeInformationGroupStopLossField = QLineEdit()
        self.ActiveTradesTabMainListTradesStackedWidgetEditEditTradeInformationGroupStopLossField.setObjectName("ActiveTradesTabMainListTradesStackedWidgetEditEditTradeInformationGroupStopLossField")
        self.ActiveTradesTabMainListTradesStackedWidgetEditEditTradeInformationGroupStopLossField.setMaximumWidth(40)
        self.ActiveTradesTabMainListTradesStackedWidgetEditEditTradeInformationGroupStopLossField.setStyleSheet("QLineEdit { border: 1px solid #555; }")
        self.ActiveTradesTabMainListTradesStackedWidgetEditEditTradeInformationGroupStopLossText = QLabel(" %")
        stop_loss_row.addWidget(self.ActiveTradesTabMainListTradesStackedWidgetEditEditTradeInformationGroupStopLossTitle)
        stop_loss_row.addWidget(self.ActiveTradesTabMainListTradesStackedWidgetEditEditTradeInformationGroupStopLossField)
        stop_loss_row.addWidget(self.ActiveTradesTabMainListTradesStackedWidgetEditEditTradeInformationGroupStopLossText)
        stop_loss_row.addStretch()
        edit_info_layout.addLayout(stop_loss_row)
        
        # Trailing Stop (editable)
        trailing_stop_row = QHBoxLayout()
        self.ActiveTradesTabMainListTradesStackedWidgetEditEditTradeInformationGroupTrailingStopTitle = QLabel("Trailing Stop:")
        self.ActiveTradesTabMainListTradesStackedWidgetEditEditTradeInformationGroupTrailingStopTitle.setFont(font_bold)
        self.ActiveTradesTabMainListTradesStackedWidgetEditEditTradeInformationGroupTrailingStopField = QLineEdit()
        self.ActiveTradesTabMainListTradesStackedWidgetEditEditTradeInformationGroupTrailingStopField.setObjectName("ActiveTradesTabMainListTradesStackedWidgetEditEditTradeInformationGroupTrailingStopField")
        self.ActiveTradesTabMainListTradesStackedWidgetEditEditTradeInformationGroupTrailingStopField.setMaximumWidth(40)
        self.ActiveTradesTabMainListTradesStackedWidgetEditEditTradeInformationGroupTrailingStopField.setStyleSheet("QLineEdit { border: 1px solid #555; }")
        self.ActiveTradesTabMainListTradesStackedWidgetEditEditTradeInformationGroupTrailingStopText = QLabel(" %")
        trailing_stop_row.addWidget(self.ActiveTradesTabMainListTradesStackedWidgetEditEditTradeInformationGroupTrailingStopTitle)
        trailing_stop_row.addWidget(self.ActiveTradesTabMainListTradesStackedWidgetEditEditTradeInformationGroupTrailingStopField)
        trailing_stop_row.addWidget(self.ActiveTradesTabMainListTradesStackedWidgetEditEditTradeInformationGroupTrailingStopText)
        trailing_stop_row.addStretch()
        edit_info_layout.addLayout(trailing_stop_row)
        
        # Accumulate Token Title
        self.ActiveTradesTabMainListTradesStackedWidgetEditAccumulateTokenTitle = QLabel("Accumulate: Token:")
        self.ActiveTradesTabMainListTradesStackedWidgetEditAccumulateTokenTitle.setObjectName("ActiveTradesTabMainListTradesStackedWidgetEditAccumulateTokenTitle")
        self.ActiveTradesTabMainListTradesStackedWidgetEditAccumulateTokenTitle.setFont(font_bold)
        edit_info_layout.addWidget(self.ActiveTradesTabMainListTradesStackedWidgetEditAccumulateTokenTitle)
        
        # Accumulate Token Toggle Switch (replaces radio buttons)
        self.ActiveTradesTabMainListTradesStackedWidgetEditAccumulateTokenToggle = ToggleSwitch("Token 1", "Token 2")
        self.ActiveTradesTabMainListTradesStackedWidgetEditAccumulateTokenToggle.setObjectName("ActiveTradesTabMainListTradesStackedWidgetEditAccumulateTokenToggle")
        edit_info_layout.addWidget(self.ActiveTradesTabMainListTradesStackedWidgetEditAccumulateTokenToggle)
        
        # Legacy radio buttons (hidden, kept for compatibility)
        self.ActiveTradesTabMainListTradesStackedWidgetEditAccumulateTokenRadioButtonOne = QRadioButton()
        self.ActiveTradesTabMainListTradesStackedWidgetEditAccumulateTokenRadioButtonOne.setObjectName("ActiveTradesTabMainListTradesStackedWidgetEditAccumulateTokenRadioButtonOne")
        self.ActiveTradesTabMainListTradesStackedWidgetEditAccumulateTokenRadioButtonOne.hide()
        
        self.ActiveTradesTabMainListTradesStackedWidgetEditAccumulateTokenRadioButtonTwo = QRadioButton()
        self.ActiveTradesTabMainListTradesStackedWidgetEditAccumulateTokenRadioButtonTwo.setObjectName("ActiveTradesTabMainListTradesStackedWidgetEditAccumulateTokenRadioButtonTwo")
        self.ActiveTradesTabMainListTradesStackedWidgetEditAccumulateTokenRadioButtonTwo.hide()
        
        # Spacer
        edit_info_layout.addStretch()
        
        # Compound Profit Checkbox
        self.ActiveTradesTabMainListTradesStackedWidgetEditCompoundProfitCheckbox = QCheckBox("Compound Profit?")
        self.ActiveTradesTabMainListTradesStackedWidgetEditCompoundProfitCheckbox.setObjectName("ActiveTradesTabMainListTradesStackedWidgetEditCompoundProfitCheckbox")
        self.ActiveTradesTabMainListTradesStackedWidgetEditCompoundProfitCheckbox.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        edit_info_layout.addWidget(self.ActiveTradesTabMainListTradesStackedWidgetEditCompoundProfitCheckbox)
        
        top_section.addWidget(self.ActiveTradesTabMainListTradesStackedWidgetEditEditTradeInformationGroup, 30)
        
        # RIGHT: Feedback area (70% width) - split into 2 rows
        right_column = QVBoxLayout()
        right_column.setSpacing(10)
        
        # Top row (40%): Instruction text
        self.ActiveTradesTabMainListTradesStackedWidgetEditText = QLabel()
        self.ActiveTradesTabMainListTradesStackedWidgetEditText.setObjectName("ActiveTradesTabMainListTradesStackedWidgetEditText")
        self.ActiveTradesTabMainListTradesStackedWidgetEditText.setWordWrap(True)
        self.ActiveTradesTabMainListTradesStackedWidgetEditText.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)
        self.ActiveTradesTabMainListTradesStackedWidgetEditText.setMinimumHeight(60)
        self.ActiveTradesTabMainListTradesStackedWidgetEditText.setStyleSheet("QLabel { padding: 10px; }")
        right_column.addWidget(self.ActiveTradesTabMainListTradesStackedWidgetEditText, 40)
        
        # Bottom row (60%): AI Strategy group
        self.ActiveTradesTabMainListTradesStackedWidgetEditAIStrategyIndicatorsGroup = QGroupBox(" AI Strategy Indicators")
        self.ActiveTradesTabMainListTradesStackedWidgetEditAIStrategyIndicatorsGroup.setObjectName("ActiveTradesTabMainListTradesStackedWidgetEditAIStrategyIndicatorsGroup")
        
        ai_strategy_layout = QVBoxLayout(self.ActiveTradesTabMainListTradesStackedWidgetEditAIStrategyIndicatorsGroup)
        ai_strategy_layout.setContentsMargins(10, 15, 10, 10)
        
        self.ActiveTradesTabMainListTradesStackedWidgetEditAIStrategyIndicatorsGroupRSILowTitle = QLabel()
        self.ActiveTradesTabMainListTradesStackedWidgetEditAIStrategyIndicatorsGroupRSILowTitle.setObjectName("ActiveTradesTabMainListTradesStackedWidgetEditAIStrategyIndicatorsGroupRSILowTitle")
        self.ActiveTradesTabMainListTradesStackedWidgetEditAIStrategyIndicatorsGroupRSILowTitle.setWordWrap(True)
        ai_strategy_layout.addWidget(self.ActiveTradesTabMainListTradesStackedWidgetEditAIStrategyIndicatorsGroupRSILowTitle)
        
        ai_strategy_layout.addStretch()
        
        self.ActiveTradesTabMainListTradesStackedWidgetEditAIStrategyIndicatorsGroupSelectedCheckbox = QCheckBox("Indicator Selected?")
        self.ActiveTradesTabMainListTradesStackedWidgetEditAIStrategyIndicatorsGroupSelectedCheckbox.setObjectName("ActiveTradesTabMainListTradesStackedWidgetEditAIStrategyIndicatorsGroupSelectedCheckbox")
        self.ActiveTradesTabMainListTradesStackedWidgetEditAIStrategyIndicatorsGroupSelectedCheckbox.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        ai_strategy_layout.addWidget(self.ActiveTradesTabMainListTradesStackedWidgetEditAIStrategyIndicatorsGroupSelectedCheckbox)
        
        right_column.addWidget(self.ActiveTradesTabMainListTradesStackedWidgetEditAIStrategyIndicatorsGroup, 60)
        
        top_section.addLayout(right_column, 70)
        
        edit_main_layout.addLayout(top_section, 43)
        
        # --- MIDDLE SECTION (~28.5% height) - 4 Indicator Groups ---
        middle_section = QHBoxLayout()
        middle_section.setSpacing(10)
        
        # Helper function to create indicator group with 3 fields + checkbox
        def create_indicator_group(title, field_labels, field_names_prefix):
            group = QGroupBox(f" {title} ")
            group.setObjectName(f"ActiveTradesTabMainListTradesStackedWidgetEdit{field_names_prefix}IndicatorGroup")
            
            layout = QVBoxLayout(group)
            layout.setContentsMargins(10, 15, 10, 10)
            layout.setSpacing(8)
            
            fields = []
            for label_text, field_suffix in field_labels:
                row = QHBoxLayout()
                label = QLabel(label_text)
                label.setObjectName(f"ActiveTradesTabMainListTradesStackedWidgetEdit{field_names_prefix}IndicatorGroup{field_suffix}Title")
                field = QLineEdit()
                field.setObjectName(f"ActiveTradesTabMainListTradesStackedWidgetEdit{field_names_prefix}IndicatorGroup{field_suffix}Field")
                field.setMaximumWidth(50)
                field.setStyleSheet("QLineEdit { border: 1px solid #555; }")
                row.addWidget(label)
                row.addStretch()
                row.addWidget(field)
                layout.addLayout(row)
                
                # Store references
                setattr(self, f"ActiveTradesTabMainListTradesStackedWidgetEdit{field_names_prefix}IndicatorGroup{field_suffix}Title", label)
                setattr(self, f"ActiveTradesTabMainListTradesStackedWidgetEdit{field_names_prefix}IndicatorGroup{field_suffix}Field", field)
                fields.append(field)
            
            layout.addStretch()
            
            checkbox = QCheckBox("Indicator Selected?")
            checkbox.setObjectName(f"ActiveTradesTabMainListTradesStackedWidgetEdit{field_names_prefix}IndicatorGroupIndicatorSelectedCheckbox")
            checkbox.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
            layout.addWidget(checkbox)
            
            setattr(self, f"ActiveTradesTabMainListTradesStackedWidgetEdit{field_names_prefix}IndicatorGroupIndicatorSelectedCheckbox", checkbox)
            
            return group, fields
        
        # BB Indicator (25%)
        self.ActiveTradesTabMainListTradesStackedWidgetEditBBIndicatorGroup, bb_fields = create_indicator_group(
            "BB Indicator",
            [("BB Period:", "BBPeriod"), ("BB Std Dev Multiplier:", "BBStdDevMultiplier")],
            "BB"
        )
        middle_section.addWidget(self.ActiveTradesTabMainListTradesStackedWidgetEditBBIndicatorGroup)
        
        # MA Crossover Indicator (25%)
        self.ActiveTradesTabMainListTradesStackedWidgetEditMACrossoverIndicatorGroup, ma_fields = create_indicator_group(
            "MA Crossover",
            [("MA Cross Short:", "MACrossShort"), ("MA Cross Long:", "MACrossLong")],
            "MACrossover"
        )
        middle_section.addWidget(self.ActiveTradesTabMainListTradesStackedWidgetEditMACrossoverIndicatorGroup)
        
        # RSI Indicator (25%)
        self.ActiveTradesTabMainListTradesStackedWidgetEditRSIIndicatorGroup, rsi_fields = create_indicator_group(
            "RSI Indicator",
            [("RSI Low Value:", "RSILowValue"), ("RSI High Value:", "RSIHighValue"), ("RSI Period", "RSIPeriod")],
            "RSI"
        )
        middle_section.addWidget(self.ActiveTradesTabMainListTradesStackedWidgetEditRSIIndicatorGroup)
        
        # MACD Indicator (25%)
        self.ActiveTradesTabMainListTradesStackedWidgetEditMACDIndicatorGroup, macd_fields = create_indicator_group(
            "MACD Indicator",
            [("MACD Low Timeframe:", "MACDLowTimeframe"), ("MACD High Timeframe:", "MACDHighTimeframe"), ("MACD Signal Period:", "MACDSignalPeriod")],
            "MACD"
        )
        middle_section.addWidget(self.ActiveTradesTabMainListTradesStackedWidgetEditMACDIndicatorGroup)
        
        edit_main_layout.addLayout(middle_section, 28)
        
        # --- BOTTOM SECTION (~28.5% height) - 3 Columns ---
        bottom_section = QHBoxLayout()
        bottom_section.setSpacing(10)
        
        # Column 1: Ping Pong Indicator Group
        self.ActiveTradesTabMainListTradesStackedWidgetEditPingPongIndicatorGroup = QGroupBox(" Ping Pong Strategy")
        self.ActiveTradesTabMainListTradesStackedWidgetEditPingPongIndicatorGroup.setObjectName("ActiveTradesTabMainListTradesStackedWidgetEditPingPongIndicatorGroup")
        
        pp_layout = QVBoxLayout(self.ActiveTradesTabMainListTradesStackedWidgetEditPingPongIndicatorGroup)
        pp_layout.setContentsMargins(10, 15, 10, 10)
        pp_layout.setSpacing(8)
        
        # Buy Price
        pp_buy_row = QHBoxLayout()
        self.ActiveTradesTabMainListTradesStackedWidgetEditPingPongIndicatorGroupBuyPriceTitle = QLabel("Buy Price:")
        self.ActiveTradesTabMainListTradesStackedWidgetEditPingPongIndicatorGroupBuyPriceField = QLineEdit()
        self.ActiveTradesTabMainListTradesStackedWidgetEditPingPongIndicatorGroupBuyPriceField.setObjectName("ActiveTradesTabMainListTradesStackedWidgetEditPingPongIndicatorGroupBuyPriceField")
        self.ActiveTradesTabMainListTradesStackedWidgetEditPingPongIndicatorGroupBuyPriceField.setMaximumWidth(80)
        self.ActiveTradesTabMainListTradesStackedWidgetEditPingPongIndicatorGroupBuyPriceField.setStyleSheet("QLineEdit { border: 1px solid #555; }")
        self.ActiveTradesTabMainListTradesStackedWidgetEditPingPongIndicatorGroupBuyPriceSymbol = QLabel()
        self.ActiveTradesTabMainListTradesStackedWidgetEditPingPongIndicatorGroupBuyPriceSymbol.setObjectName("ActiveTradesTabMainListTradesStackedWidgetEditPingPongIndicatorGroupBuyPriceSymbol")
        pp_buy_row.addWidget(self.ActiveTradesTabMainListTradesStackedWidgetEditPingPongIndicatorGroupBuyPriceTitle)
        pp_buy_row.addStretch()
        pp_buy_row.addWidget(self.ActiveTradesTabMainListTradesStackedWidgetEditPingPongIndicatorGroupBuyPriceField)
        pp_buy_row.addWidget(self.ActiveTradesTabMainListTradesStackedWidgetEditPingPongIndicatorGroupBuyPriceSymbol)
        pp_layout.addLayout(pp_buy_row)
        
        # Sell Price
        pp_sell_row = QHBoxLayout()
        self.ActiveTradesTabMainListTradesStackedWidgetEditPingPongIndicatorGroupSellPriceTitle = QLabel("Sell Price:")
        self.ActiveTradesTabMainListTradesStackedWidgetEditPingPongIndicatorGroupSellPriceField = QLineEdit()
        self.ActiveTradesTabMainListTradesStackedWidgetEditPingPongIndicatorGroupSellPriceField.setObjectName("ActiveTradesTabMainListTradesStackedWidgetEditPingPongIndicatorGroupSellPriceField")
        self.ActiveTradesTabMainListTradesStackedWidgetEditPingPongIndicatorGroupSellPriceField.setMaximumWidth(80)
        self.ActiveTradesTabMainListTradesStackedWidgetEditPingPongIndicatorGroupSellPriceField.setStyleSheet("QLineEdit { border: 1px solid #555; }")
        self.ActiveTradesTabMainListTradesStackedWidgetEditPingPongIndicatorGroupSellPriceSymbol = QLabel()
        self.ActiveTradesTabMainListTradesStackedWidgetEditPingPongIndicatorGroupSellPriceSymbol.setObjectName("ActiveTradesTabMainListTradesStackedWidgetEditPingPongIndicatorGroupSellPriceSymbol")
        pp_sell_row.addWidget(self.ActiveTradesTabMainListTradesStackedWidgetEditPingPongIndicatorGroupSellPriceTitle)
        pp_sell_row.addStretch()
        pp_sell_row.addWidget(self.ActiveTradesTabMainListTradesStackedWidgetEditPingPongIndicatorGroupSellPriceField)
        pp_sell_row.addWidget(self.ActiveTradesTabMainListTradesStackedWidgetEditPingPongIndicatorGroupSellPriceSymbol)
        pp_layout.addLayout(pp_sell_row)
        
        pp_layout.addStretch()
        
        self.ActiveTradesTabMainListTradesStackedWidgetEditPingPongIndicatorGroupIndicatorSelectedCheckbox = QCheckBox("Indicator Selected?")
        self.ActiveTradesTabMainListTradesStackedWidgetEditPingPongIndicatorGroupIndicatorSelectedCheckbox.setObjectName("ActiveTradesTabMainListTradesStackedWidgetEditPingPongIndicatorGroupIndicatorSelectedCheckbox")
        self.ActiveTradesTabMainListTradesStackedWidgetEditPingPongIndicatorGroupIndicatorSelectedCheckbox.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        pp_layout.addWidget(self.ActiveTradesTabMainListTradesStackedWidgetEditPingPongIndicatorGroupIndicatorSelectedCheckbox)
        
        bottom_section.addWidget(self.ActiveTradesTabMainListTradesStackedWidgetEditPingPongIndicatorGroup, 33)
        
        # Column 2: Current Prices Group
        self.ActiveTradesTabMainListTradesStackedWidgetEditCurrentPricesGroup = QGroupBox(" Current Prices")
        self.ActiveTradesTabMainListTradesStackedWidgetEditCurrentPricesGroup.setObjectName("ActiveTradesTabMainListTradesStackedWidgetEditCurrentPricesGroup")
        
        current_prices_layout = QVBoxLayout(self.ActiveTradesTabMainListTradesStackedWidgetEditCurrentPricesGroup)
        current_prices_layout.setContentsMargins(10, 15, 10, 10)
        
        self.ActiveTradesTabMainListTradesStackedWidgetEditCurrentPricesGroupPriceOne = QLabel()
        self.ActiveTradesTabMainListTradesStackedWidgetEditCurrentPricesGroupPriceOne.setObjectName("ActiveTradesTabMainListTradesStackedWidgetEditCurrentPricesGroupPriceOne")
        self.ActiveTradesTabMainListTradesStackedWidgetEditCurrentPricesGroupPriceOne.setAlignment(Qt.AlignmentFlag.AlignCenter)
        current_prices_layout.addWidget(self.ActiveTradesTabMainListTradesStackedWidgetEditCurrentPricesGroupPriceOne)
        
        self.ActiveTradesTabMainListTradesStackedWidgetEditCurrentPricesGroupPriceTwo = QLabel()
        self.ActiveTradesTabMainListTradesStackedWidgetEditCurrentPricesGroupPriceTwo.setObjectName("ActiveTradesTabMainListTradesStackedWidgetEditCurrentPricesGroupPriceTwo")
        self.ActiveTradesTabMainListTradesStackedWidgetEditCurrentPricesGroupPriceTwo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        current_prices_layout.addWidget(self.ActiveTradesTabMainListTradesStackedWidgetEditCurrentPricesGroupPriceTwo)
        
        # Spacer to push icons below text
        current_prices_layout.addSpacing(10)
        
        # Placeholder for overlapping icons (created dynamically by logic file)
        # Create container for centered icons
        icon_container = QHBoxLayout()
        icon_container.addStretch()
        self.ActiveTradesTabMainListTradesStackedWidgetEditCurrentPricesGroupIconsPlaceholder = QLabel()
        self.ActiveTradesTabMainListTradesStackedWidgetEditCurrentPricesGroupIconsPlaceholder.setObjectName("ActiveTradesTabMainListTradesStackedWidgetEditCurrentPricesGroupIconsPlaceholder")
        self.ActiveTradesTabMainListTradesStackedWidgetEditCurrentPricesGroupIconsPlaceholder.setMinimumSize(45, 25)
        icon_container.addWidget(self.ActiveTradesTabMainListTradesStackedWidgetEditCurrentPricesGroupIconsPlaceholder)
        icon_container.addStretch()
        current_prices_layout.addLayout(icon_container)
        
        current_prices_layout.addStretch()
        
        bottom_section.addWidget(self.ActiveTradesTabMainListTradesStackedWidgetEditCurrentPricesGroup, 34)
        
        # Column 3: Buttons only (33%)
        right_bottom_column = QVBoxLayout()
        right_bottom_column.setSpacing(10)
        
        # Feedback text area
        self.ActiveTradesTabMainListTradesStackedWidgetEditFeedbackTextArea = QLabel()
        self.ActiveTradesTabMainListTradesStackedWidgetEditFeedbackTextArea.setObjectName("ActiveTradesTabMainListTradesStackedWidgetEditFeedbackTextArea")
        self.ActiveTradesTabMainListTradesStackedWidgetEditFeedbackTextArea.setWordWrap(True)
        self.ActiveTradesTabMainListTradesStackedWidgetEditFeedbackTextArea.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)
        right_bottom_column.addWidget(self.ActiveTradesTabMainListTradesStackedWidgetEditFeedbackTextArea)
        
        right_bottom_column.addStretch()
        
        # Buttons
        buttons_layout = QVBoxLayout()
        buttons_layout.setSpacing(10)
        
        self.ActiveTradesTabMainListTradesStackedWidgetEditEditTradeButton = QPushButton("Edit Trade")
        self.ActiveTradesTabMainListTradesStackedWidgetEditEditTradeButton.setObjectName("ActiveTradesTabMainListTradesStackedWidgetEditEditTradeButton")
        self.ActiveTradesTabMainListTradesStackedWidgetEditEditTradeButton.setMinimumHeight(40)
        buttons_layout.addWidget(self.ActiveTradesTabMainListTradesStackedWidgetEditEditTradeButton)
        
        self.ActiveTradesTabMainListTradesStackedWidgetEditBackButton = QPushButton("Back to Trades")
        self.ActiveTradesTabMainListTradesStackedWidgetEditBackButton.setObjectName("ActiveTradesTabMainListTradesStackedWidgetEditBackButton")
        self.ActiveTradesTabMainListTradesStackedWidgetEditBackButton.setMinimumHeight(40)
        buttons_layout.addWidget(self.ActiveTradesTabMainListTradesStackedWidgetEditBackButton)
        
        right_bottom_column.addLayout(buttons_layout)
        
        bottom_section.addLayout(right_bottom_column, 33)
        
        edit_main_layout.addLayout(bottom_section, 28)
        
        self.ActiveTradesTabMainListTradesStackedWidget.addWidget(self.Edit)
        
        # Set initial page to List
        self.ActiveTradesTabMainListTradesStackedWidget.setCurrentIndex(0)
    
    def _setupUi_legacy(self, ActiveTradesTabMain):
        """Legacy fixed-size implementation"""
        ActiveTradesTabMain.setObjectName("ActiveTradesTabMain")

        self.ActiveTradesTabMainListTradesStackedWidget = QStackedWidget(ActiveTradesTabMain)
        self.ActiveTradesTabMainListTradesStackedWidget.setObjectName("ActiveTradesTabMainListTradesStackedWidget")
        self.ActiveTradesTabMainListTradesStackedWidget.setGeometry(QRect(0, 0, 800, 540))
        self.ActiveTradesTabMainListTradesStackedWidget.setLayoutDirection(Qt.LayoutDirection.LeftToRight)

        # --- List Page ---
        self.List = QWidget()
        self.List.setObjectName("List")

        self.ActiveTradesTabMainListTradesStackedWidgetListScrollArea = QScrollArea(self.List)
        self.ActiveTradesTabMainListTradesStackedWidgetListScrollArea.setObjectName("ActiveTradesTabMainListTradesStackedWidgetListScrollArea")
        self.ActiveTradesTabMainListTradesStackedWidgetListScrollArea.setGeometry(QRect(10, 10, 778, 515))
        self.ActiveTradesTabMainListTradesStackedWidgetListScrollArea.setWidgetResizable(True)

        self.scrollAreaWidgetContents_7 = QWidget()
        self.scrollAreaWidgetContents_7.setObjectName("scrollAreaWidgetContents_7")
        self.scrollAreaWidgetContents_7.setGeometry(QRect(0, 0, 776, 513))
        self.ActiveTradesTabMainListTradesStackedWidgetListScrollArea.setWidget(self.scrollAreaWidgetContents_7)

        self.ActiveTradesTabMainListTradesStackedWidget.addWidget(self.List)

        self.Information = QWidget()
        self.Information.setObjectName("Information")

        font_bold = QFont()
        font_bold.setBold(True)

        self.ActiveTradesTabMainListTradesStackedWidgetInformationTradeInformationGroup = QGroupBox(self.Information)
        self.ActiveTradesTabMainListTradesStackedWidgetInformationTradeInformationGroup.setObjectName("ActiveTradesTabMainListTradesStackedWidgetInformationTradeInformationGroup")
        self.ActiveTradesTabMainListTradesStackedWidgetInformationTradeInformationGroup.setGeometry(QRect(20, 20, 331, 501))

        # Titles (Labels with bold font)
        self.ActiveTradesTabMainListTradesStackedWidgetInformationTradeInformationGroupTradeIdTitle = QLabel(self.ActiveTradesTabMainListTradesStackedWidgetInformationTradeInformationGroup)
        self.ActiveTradesTabMainListTradesStackedWidgetInformationTradeInformationGroupTradeIdTitle.setObjectName("ActiveTradesTabMainListTradesStackedWidgetInformationTradeInformationGroupTradeIdTitle")
        self.ActiveTradesTabMainListTradesStackedWidgetInformationTradeInformationGroupTradeIdTitle.setGeometry(QRect(20, 30, 49, 16))
        self.ActiveTradesTabMainListTradesStackedWidgetInformationTradeInformationGroupTradeIdTitle.setFont(font_bold)

        self.ActiveTradesTabMainListTradesStackedWidgetInformationTradeInformationGroupCreationDateTitle = QLabel(self.ActiveTradesTabMainListTradesStackedWidgetInformationTradeInformationGroup)
        self.ActiveTradesTabMainListTradesStackedWidgetInformationTradeInformationGroupCreationDateTitle.setObjectName("ActiveTradesTabMainListTradesStackedWidgetInformationTradeInformationGroupCreationDateTitle")
        self.ActiveTradesTabMainListTradesStackedWidgetInformationTradeInformationGroupCreationDateTitle.setGeometry(QRect(20, 60, 91, 16))
        self.ActiveTradesTabMainListTradesStackedWidgetInformationTradeInformationGroupCreationDateTitle.setFont(font_bold)

        self.ActiveTradesTabMainListTradesStackedWidgetInformationTradeInformationGroupCreationValueTitle = QLabel(self.ActiveTradesTabMainListTradesStackedWidgetInformationTradeInformationGroup)
        self.ActiveTradesTabMainListTradesStackedWidgetInformationTradeInformationGroupCreationValueTitle.setObjectName("ActiveTradesTabMainListTradesStackedWidgetInformationTradeInformationGroupCreationValueTitle")
        self.ActiveTradesTabMainListTradesStackedWidgetInformationTradeInformationGroupCreationValueTitle.setGeometry(QRect(20, 90, 91, 16))
        self.ActiveTradesTabMainListTradesStackedWidgetInformationTradeInformationGroupCreationValueTitle.setFont(font_bold)

        self.ActiveTradesTabMainListTradesStackedWidgetInformationTradeInformationGroupTimesFlippedTitle = QLabel(self.ActiveTradesTabMainListTradesStackedWidgetInformationTradeInformationGroup)
        self.ActiveTradesTabMainListTradesStackedWidgetInformationTradeInformationGroupTimesFlippedTitle.setObjectName("ActiveTradesTabMainListTradesStackedWidgetInformationTradeInformationGroupTimesFlippedTitle")
        self.ActiveTradesTabMainListTradesStackedWidgetInformationTradeInformationGroupTimesFlippedTitle.setGeometry(QRect(20, 120, 121, 16))
        self.ActiveTradesTabMainListTradesStackedWidgetInformationTradeInformationGroupTimesFlippedTitle.setFont(font_bold)

        self.ActiveTradesTabMainListTradesStackedWidgetInformationTradeInformationGroupProfitableFlipsTitle = QLabel(self.ActiveTradesTabMainListTradesStackedWidgetInformationTradeInformationGroup)
        self.ActiveTradesTabMainListTradesStackedWidgetInformationTradeInformationGroupProfitableFlipsTitle.setObjectName("ActiveTradesTabMainListTradesStackedWidgetInformationTradeInformationGroupProfitableFlipsTitle")
        self.ActiveTradesTabMainListTradesStackedWidgetInformationTradeInformationGroupProfitableFlipsTitle.setGeometry(QRect(20, 150, 101, 16))
        self.ActiveTradesTabMainListTradesStackedWidgetInformationTradeInformationGroupProfitableFlipsTitle.setFont(font_bold)

        self.ActiveTradesTabMainListTradesStackedWidgetInformationTradeInformationGroupUnprofitablFlipsTitle = QLabel(self.ActiveTradesTabMainListTradesStackedWidgetInformationTradeInformationGroup)
        self.ActiveTradesTabMainListTradesStackedWidgetInformationTradeInformationGroupUnprofitablFlipsTitle.setObjectName("ActiveTradesTabMainListTradesStackedWidgetInformationTradeInformationGroupUnprofitablFlipsTitle")
        self.ActiveTradesTabMainListTradesStackedWidgetInformationTradeInformationGroupUnprofitablFlipsTitle.setGeometry(QRect(20, 180, 111, 16))
        self.ActiveTradesTabMainListTradesStackedWidgetInformationTradeInformationGroupUnprofitablFlipsTitle.setFont(font_bold)

        self.ActiveTradesTabMainListTradesStackedWidgetInformationTradeInformationGroupWinRatioTitle = QLabel(self.ActiveTradesTabMainListTradesStackedWidgetInformationTradeInformationGroup)
        self.ActiveTradesTabMainListTradesStackedWidgetInformationTradeInformationGroupWinRatioTitle.setObjectName("ActiveTradesTabMainListTradesStackedWidgetInformationTradeInformationGroupWinRatioTitle")
        self.ActiveTradesTabMainListTradesStackedWidgetInformationTradeInformationGroupWinRatioTitle.setGeometry(QRect(20, 210, 71, 16))
        self.ActiveTradesTabMainListTradesStackedWidgetInformationTradeInformationGroupWinRatioTitle.setFont(font_bold)

        self.ActiveTradesTabMainListTradesStackedWidgetInformationTradeInformationGroupTotalProfitTitle = QLabel(self.ActiveTradesTabMainListTradesStackedWidgetInformationTradeInformationGroup)
        self.ActiveTradesTabMainListTradesStackedWidgetInformationTradeInformationGroupTotalProfitTitle.setObjectName("ActiveTradesTabMainListTradesStackedWidgetInformationTradeInformationGroupTotalProfitTitle")
        self.ActiveTradesTabMainListTradesStackedWidgetInformationTradeInformationGroupTotalProfitTitle.setGeometry(QRect(20, 240, 81, 16))
        self.ActiveTradesTabMainListTradesStackedWidgetInformationTradeInformationGroupTotalProfitTitle.setFont(font_bold)

        self.ActiveTradesTabMainListTradesStackedWidgetInformationTradeInformationGroupIndicatorUsedTitle = QLabel(self.ActiveTradesTabMainListTradesStackedWidgetInformationTradeInformationGroup)
        self.ActiveTradesTabMainListTradesStackedWidgetInformationTradeInformationGroupIndicatorUsedTitle.setObjectName("ActiveTradesTabMainListTradesStackedWidgetInformationTradeInformationGroupIndicatorUsedTitle")
        self.ActiveTradesTabMainListTradesStackedWidgetInformationTradeInformationGroupIndicatorUsedTitle.setGeometry(QRect(20, 300, 91, 16))
        self.ActiveTradesTabMainListTradesStackedWidgetInformationTradeInformationGroupIndicatorUsedTitle.setFont(font_bold)

        self.ActiveTradesTabMainListTradesStackedWidgetInformationTradeInformationGroupTradeVolumeTitle = QLabel(self.ActiveTradesTabMainListTradesStackedWidgetInformationTradeInformationGroup)
        self.ActiveTradesTabMainListTradesStackedWidgetInformationTradeInformationGroupTradeVolumeTitle.setObjectName("ActiveTradesTabMainListTradesStackedWidgetInformationTradeInformationGroupTradeVolumeTitle")
        self.ActiveTradesTabMainListTradesStackedWidgetInformationTradeInformationGroupTradeVolumeTitle.setGeometry(QRect(20, 270, 91, 16))
        self.ActiveTradesTabMainListTradesStackedWidgetInformationTradeInformationGroupTradeVolumeTitle.setFont(font_bold)

        self.ActiveTradesTabMainListTradesStackedWidgetInformationTradeInformationGroupCurrentTradeValueTitle = QLabel(self.ActiveTradesTabMainListTradesStackedWidgetInformationTradeInformationGroup)
        self.ActiveTradesTabMainListTradesStackedWidgetInformationTradeInformationGroupCurrentTradeValueTitle.setObjectName("ActiveTradesTabMainListTradesStackedWidgetInformationTradeInformationGroupCurrentTradeValueTitle")
        self.ActiveTradesTabMainListTradesStackedWidgetInformationTradeInformationGroupCurrentTradeValueTitle.setGeometry(QRect(20, 400, 121, 16))
        self.ActiveTradesTabMainListTradesStackedWidgetInformationTradeInformationGroupCurrentTradeValueTitle.setFont(font_bold)

        self.ActiveTradesTabMainListTradesStackedWidgetInformationTradeInformationGroupTradeIdTextArea = QLabel(self.ActiveTradesTabMainListTradesStackedWidgetInformationTradeInformationGroup)
        self.ActiveTradesTabMainListTradesStackedWidgetInformationTradeInformationGroupTradeIdTextArea.setObjectName("ActiveTradesTabMainListTradesStackedWidgetInformationTradeInformationGroupTradeIdTextArea")
        self.ActiveTradesTabMainListTradesStackedWidgetInformationTradeInformationGroupTradeIdTextArea.setGeometry(QRect(150, 30, 161, 16))

        self.ActiveTradesTabMainListTradesStackedWidgetInformationTradeInformationGroupCreationDateTextArea = QLabel(self.ActiveTradesTabMainListTradesStackedWidgetInformationTradeInformationGroup)
        self.ActiveTradesTabMainListTradesStackedWidgetInformationTradeInformationGroupCreationDateTextArea.setObjectName("ActiveTradesTabMainListTradesStackedWidgetInformationTradeInformationGroupCreationDateTextArea")
        self.ActiveTradesTabMainListTradesStackedWidgetInformationTradeInformationGroupCreationDateTextArea.setGeometry(QRect(150, 52, 161, 16))

        self.ActiveTradesTabMainListTradesStackedWidgetInformationTradeInformationGroupCreationValueTextArea = QLabel(self.ActiveTradesTabMainListTradesStackedWidgetInformationTradeInformationGroup)
        self.ActiveTradesTabMainListTradesStackedWidgetInformationTradeInformationGroupCreationValueTextArea.setObjectName("ActiveTradesTabMainListTradesStackedWidgetInformationTradeInformationGroupCreationValueTextArea")
        self.ActiveTradesTabMainListTradesStackedWidgetInformationTradeInformationGroupCreationValueTextArea.setGeometry(QRect(150, 90, 161, 16))

        self.ActiveTradesTabMainListTradesStackedWidgetInformationTradeInformationGroupTimesFlippedTextArea = QLabel(self.ActiveTradesTabMainListTradesStackedWidgetInformationTradeInformationGroup)
        self.ActiveTradesTabMainListTradesStackedWidgetInformationTradeInformationGroupTimesFlippedTextArea.setObjectName("ActiveTradesTabMainListTradesStackedWidgetInformationTradeInformationGroupTimesFlippedTextArea")
        self.ActiveTradesTabMainListTradesStackedWidgetInformationTradeInformationGroupTimesFlippedTextArea.setGeometry(QRect(150, 120, 161, 16))

        self.ActiveTradesTabMainListTradesStackedWidgetInformationTradeInformationGroupProfitableFlipsTextArea = QLabel(self.ActiveTradesTabMainListTradesStackedWidgetInformationTradeInformationGroup)
        self.ActiveTradesTabMainListTradesStackedWidgetInformationTradeInformationGroupProfitableFlipsTextArea.setObjectName("ActiveTradesTabMainListTradesStackedWidgetInformationTradeInformationGroupProfitableFlipsTextArea")
        self.ActiveTradesTabMainListTradesStackedWidgetInformationTradeInformationGroupProfitableFlipsTextArea.setGeometry(QRect(150, 150, 161, 16))

        self.ActiveTradesTabMainListTradesStackedWidgetInformationTradeInformationGroupUnprofitablFlipsTextArea = QLabel(self.ActiveTradesTabMainListTradesStackedWidgetInformationTradeInformationGroup)
        self.ActiveTradesTabMainListTradesStackedWidgetInformationTradeInformationGroupUnprofitablFlipsTextArea.setObjectName("ActiveTradesTabMainListTradesStackedWidgetInformationTradeInformationGroupUnprofitablFlipsTextArea")
        self.ActiveTradesTabMainListTradesStackedWidgetInformationTradeInformationGroupUnprofitablFlipsTextArea.setGeometry(QRect(150, 180, 161, 16))

        self.ActiveTradesTabMainListTradesStackedWidgetInformationTradeInformationGroupWinRatioTextArea = QLabel(self.ActiveTradesTabMainListTradesStackedWidgetInformationTradeInformationGroup)
        self.ActiveTradesTabMainListTradesStackedWidgetInformationTradeInformationGroupWinRatioTextArea.setObjectName("ActiveTradesTabMainListTradesStackedWidgetInformationTradeInformationGroupWinRatioTextArea")
        self.ActiveTradesTabMainListTradesStackedWidgetInformationTradeInformationGroupWinRatioTextArea.setGeometry(QRect(150, 210, 161, 16))

        self.ActiveTradesTabMainListTradesStackedWidgetInformationTradeInformationGroupTotalProfitTextArea = QLabel(self.ActiveTradesTabMainListTradesStackedWidgetInformationTradeInformationGroup)
        self.ActiveTradesTabMainListTradesStackedWidgetInformationTradeInformationGroupTotalProfitTextArea.setObjectName("ActiveTradesTabMainListTradesStackedWidgetInformationTradeInformationGroupTotalProfitTextArea")
        self.ActiveTradesTabMainListTradesStackedWidgetInformationTradeInformationGroupTotalProfitTextArea.setGeometry(QRect(150, 240, 161, 16))

        self.ActiveTradesTabMainListTradesStackedWidgetInformationTradeInformationGroupIndicatorUsedTextArea = QLabel(self.ActiveTradesTabMainListTradesStackedWidgetInformationTradeInformationGroup)
        self.ActiveTradesTabMainListTradesStackedWidgetInformationTradeInformationGroupIndicatorUsedTextArea.setObjectName("ActiveTradesTabMainListTradesStackedWidgetInformationTradeInformationGroupIndicatorUsedTextArea")
        self.ActiveTradesTabMainListTradesStackedWidgetInformationTradeInformationGroupIndicatorUsedTextArea.setGeometry(QRect(150, 300, 161, 16))

        self.ActiveTradesTabMainListTradesStackedWidgetInformationTradeInformationGroupTradeVolumeTextArea = QLabel(self.ActiveTradesTabMainListTradesStackedWidgetInformationTradeInformationGroup)
        self.ActiveTradesTabMainListTradesStackedWidgetInformationTradeInformationGroupTradeVolumeTextArea.setObjectName("ActiveTradesTabMainListTradesStackedWidgetInformationTradeInformationGroupTradeVolumeTextArea")
        self.ActiveTradesTabMainListTradesStackedWidgetInformationTradeInformationGroupTradeVolumeTextArea.setGeometry(QRect(150, 270, 161, 16))

        # Current trade value label (large font)
        self.ActiveTradesTabMainListTradesStackedWidgetInformationTradeInformationGroupCurrentTradeValueTextArea = QLabel(self.ActiveTradesTabMainListTradesStackedWidgetInformationTradeInformationGroup)
        self.ActiveTradesTabMainListTradesStackedWidgetInformationTradeInformationGroupCurrentTradeValueTextArea.setObjectName("ActiveTradesTabMainListTradesStackedWidgetInformationTradeInformationGroupCurrentTradeValueTextArea")
        self.ActiveTradesTabMainListTradesStackedWidgetInformationTradeInformationGroupCurrentTradeValueTextArea.setGeometry(QRect(20, 430, 191, 41))
        font_large = QFont()
        font_large.setPointSize(14)
        self.ActiveTradesTabMainListTradesStackedWidgetInformationTradeInformationGroupCurrentTradeValueTextArea.setFont(font_large)
        self.ActiveTradesTabMainListTradesStackedWidgetInformationTradeInformationGroupCurrentTradeValueTextArea.setAlignment(
        Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignTrailing | Qt.AlignmentFlag.AlignVCenter
        )

        self.ActiveTradesTabMainListTradesStackedWidgetInformationTradeInformationGroupCurrentTradeValueTickerTextArea = QLabel(self.ActiveTradesTabMainListTradesStackedWidgetInformationTradeInformationGroup)
        self.ActiveTradesTabMainListTradesStackedWidgetInformationTradeInformationGroupCurrentTradeValueTickerTextArea.setObjectName("ActiveTradesTabMainListTradesStackedWidgetInformationTradeInformationGroupCurrentTradeValueTickerTextArea")
        self.ActiveTradesTabMainListTradesStackedWidgetInformationTradeInformationGroupCurrentTradeValueTickerTextArea.setGeometry(QRect(220, 430, 91, 41))
        self.ActiveTradesTabMainListTradesStackedWidgetInformationTradeInformationGroupCurrentTradeValueTickerTextArea.setFont(font_large)

        self.ActiveTradesTabMainListTradesStackedWidgetInformationBackToTradesListButton = QPushButton(self.Information)
        self.ActiveTradesTabMainListTradesStackedWidgetInformationBackToTradesListButton.setObjectName("ActiveTradesTabMainListTradesStackedWidgetInformationBackToTradesListButton")
        self.ActiveTradesTabMainListTradesStackedWidgetInformationBackToTradesListButton.setGeometry(QRect(644, 473, 131, 51))

        self.ActiveTradesTabMainListTradesStackedWidgetInformationChartText = QLabel(self.Information)
        self.ActiveTradesTabMainListTradesStackedWidgetInformationChartText.setObjectName("ActiveTradesTabMainListTradesStackedWidgetInformationChartText")
        self.ActiveTradesTabMainListTradesStackedWidgetInformationChartText.setGeometry(QRect(370, 350, 411, 31))
        self.ActiveTradesTabMainListTradesStackedWidgetInformationChartText.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.ActiveTradesTabMainListTradesStackedWidget.addWidget(self.Information)

        # --- Edit page ---
        self.Edit = QWidget()
        self.Edit.setObjectName(u"Edit")

        self.ActiveTradesTabMainListTradesStackedWidgetEditEditTradeInformationGroup = QGroupBox(self.Edit)
        self.ActiveTradesTabMainListTradesStackedWidgetEditEditTradeInformationGroup.setObjectName(u"ActiveTradesTabMainListTradesStackedWidgetEditEditTradeInformationGroup")
        self.ActiveTradesTabMainListTradesStackedWidgetEditEditTradeInformationGroup.setGeometry(QRect(10, 20, 211, 211))

        self.ActiveTradesTabMainListTradesStackedWidgetEditEditTradeInformationGroupTradeIDTitle = QLabel(self.ActiveTradesTabMainListTradesStackedWidgetEditEditTradeInformationGroup)
        self.ActiveTradesTabMainListTradesStackedWidgetEditEditTradeInformationGroupTradeIDTitle.setObjectName(u"ActiveTradesTabMainListTradesStackedWidgetEditEditTradeInformationGroupTradeIDTitle")
        self.ActiveTradesTabMainListTradesStackedWidgetEditEditTradeInformationGroupTradeIDTitle.setGeometry(QRect(10, 20, 61, 20))
        self.ActiveTradesTabMainListTradesStackedWidgetEditEditTradeInformationGroupTradeIDTitle.setFont(font_bold)

        self.ActiveTradesTabMainListTradesStackedWidgetEditEditTradeInformationGroupTradeIDTextArea = QLabel(self.ActiveTradesTabMainListTradesStackedWidgetEditEditTradeInformationGroup)
        self.ActiveTradesTabMainListTradesStackedWidgetEditEditTradeInformationGroupTradeIDTextArea.setObjectName(u"ActiveTradesTabMainListTradesStackedWidgetEditEditTradeInformationGroupTradeIDTextArea")
        self.ActiveTradesTabMainListTradesStackedWidgetEditEditTradeInformationGroupTradeIDTextArea.setGeometry(QRect(80, 20, 121, 20))
        self.ActiveTradesTabMainListTradesStackedWidgetEditEditTradeInformationGroupTradeIDTextArea.setInputMethodHints(Qt.InputMethodHint.ImhFormattedNumbersOnly)
        self.ActiveTradesTabMainListTradesStackedWidgetEditEditTradeInformationGroupTradeIDTextArea.setTextInteractionFlags(Qt.TextInteractionFlag.NoTextInteraction)

        self.ActiveTradesTabMainListTradesStackedWidgetEditEditTradeInformationGroupTradePairTitle = QLabel(self.ActiveTradesTabMainListTradesStackedWidgetEditEditTradeInformationGroup)
        self.ActiveTradesTabMainListTradesStackedWidgetEditEditTradeInformationGroupTradePairTitle.setObjectName(u"ActiveTradesTabMainListTradesStackedWidgetEditEditTradeInformationGroupTradePairTitle")
        self.ActiveTradesTabMainListTradesStackedWidgetEditEditTradeInformationGroupTradePairTitle.setGeometry(QRect(10, 40, 61, 20))
        self.ActiveTradesTabMainListTradesStackedWidgetEditEditTradeInformationGroupTradePairTitle.setFont(font_bold)

        self.ActiveTradesTabMainListTradesStackedWidgetEditEditTradeInformationGroupTradePairTextArea = QLabel(self.ActiveTradesTabMainListTradesStackedWidgetEditEditTradeInformationGroup)
        self.ActiveTradesTabMainListTradesStackedWidgetEditEditTradeInformationGroupTradePairTextArea.setObjectName(u"ActiveTradesTabMainListTradesStackedWidgetEditEditTradeInformationGroupTradePairTextArea")
        self.ActiveTradesTabMainListTradesStackedWidgetEditEditTradeInformationGroupTradePairTextArea.setGeometry(QRect(80, 40, 121, 20))

        self.ActiveTradesTabMainListTradesStackedWidgetEditEditTradeInformationGroupTokensTitle = QLabel(self.ActiveTradesTabMainListTradesStackedWidgetEditEditTradeInformationGroup)
        self.ActiveTradesTabMainListTradesStackedWidgetEditEditTradeInformationGroupTokensTitle.setObjectName(u"ActiveTradesTabMainListTradesStackedWidgetEditEditTradeInformationGroupTokensTitle")
        self.ActiveTradesTabMainListTradesStackedWidgetEditEditTradeInformationGroupTokensTitle.setGeometry(QRect(10, 60, 49, 20))
        self.ActiveTradesTabMainListTradesStackedWidgetEditEditTradeInformationGroupTokensTitle.setFont(font_bold)

        self.ActiveTradesTabMainListTradesStackedWidgetEditEditTradeInformationGroupTokensField = QLabel(self.ActiveTradesTabMainListTradesStackedWidgetEditEditTradeInformationGroup)
        self.ActiveTradesTabMainListTradesStackedWidgetEditEditTradeInformationGroupTokensField.setObjectName(u"ActiveTradesTabMainListTradesStackedWidgetEditEditTradeInformationGroupTokensField")
        self.ActiveTradesTabMainListTradesStackedWidgetEditEditTradeInformationGroupTokensField.setGeometry(QRect(80, 60, 81, 20))

        self.ActiveTradesTabMainListTradesStackedWidgetEditEditTradeInformationGroupTokensTicker = QLabel(self.ActiveTradesTabMainListTradesStackedWidgetEditEditTradeInformationGroup)
        self.ActiveTradesTabMainListTradesStackedWidgetEditEditTradeInformationGroupTokensTicker.setObjectName(u"ActiveTradesTabMainListTradesStackedWidgetEditEditTradeInformationGroupTokensTicker")
        self.ActiveTradesTabMainListTradesStackedWidgetEditEditTradeInformationGroupTokensTicker.setGeometry(QRect(160, 60, 41, 20))
        self.ActiveTradesTabMainListTradesStackedWidgetEditEditTradeInformationGroupTokensTicker.setLayoutDirection(Qt.LayoutDirection.LeftToRight)
        self.ActiveTradesTabMainListTradesStackedWidgetEditEditTradeInformationGroupTokensTicker.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.ActiveTradesTabMainListTradesStackedWidgetEditEditTradeInformationGroupStopLossTitle = QLabel(self.ActiveTradesTabMainListTradesStackedWidgetEditEditTradeInformationGroup)
        self.ActiveTradesTabMainListTradesStackedWidgetEditEditTradeInformationGroupStopLossTitle.setObjectName(u"ActiveTradesTabMainListTradesStackedWidgetEditEditTradeInformationGroupStopLossTitle")
        self.ActiveTradesTabMainListTradesStackedWidgetEditEditTradeInformationGroupStopLossTitle.setGeometry(QRect(10, 80, 75, 20))
        self.ActiveTradesTabMainListTradesStackedWidgetEditEditTradeInformationGroupStopLossTitle.setFont(font_bold)

        self.ActiveTradesTabMainListTradesStackedWidgetEditEditTradeInformationGroupStopLossField = QLineEdit(self.ActiveTradesTabMainListTradesStackedWidgetEditEditTradeInformationGroup)
        self.ActiveTradesTabMainListTradesStackedWidgetEditEditTradeInformationGroupStopLossField.setObjectName("ActiveTradesTabMainListTradesStackedWidgetEditEditTradeInformationGroupStopLossField")
        self.ActiveTradesTabMainListTradesStackedWidgetEditEditTradeInformationGroupStopLossField.setGeometry(QRect(90, 80, 22, 22))

        self.ActiveTradesTabMainListTradesStackedWidgetEditEditTradeInformationGroupStopLossText = QLabel(self.ActiveTradesTabMainListTradesStackedWidgetEditEditTradeInformationGroup)
        self.ActiveTradesTabMainListTradesStackedWidgetEditEditTradeInformationGroupStopLossText.setObjectName(u"ActiveTradesTabMainListTradesStackedWidgetEditEditTradeInformationGroupTokensText")
        self.ActiveTradesTabMainListTradesStackedWidgetEditEditTradeInformationGroupStopLossText.setGeometry(QRect(115, 80, 20, 20))

        self.ActiveTradesTabMainListTradesStackedWidgetEditEditTradeInformationGroupTrailingStopTitle = QLabel(self.ActiveTradesTabMainListTradesStackedWidgetEditEditTradeInformationGroup)
        self.ActiveTradesTabMainListTradesStackedWidgetEditEditTradeInformationGroupTrailingStopTitle.setObjectName(u"ActiveTradesTabMainListTradesStackedWidgetEditEditTradeInformationGroupTrailingStopTitle")
        self.ActiveTradesTabMainListTradesStackedWidgetEditEditTradeInformationGroupTrailingStopTitle.setGeometry(QRect(10, 105, 75, 20))
        self.ActiveTradesTabMainListTradesStackedWidgetEditEditTradeInformationGroupTrailingStopTitle.setFont(font_bold)

        self.ActiveTradesTabMainListTradesStackedWidgetEditEditTradeInformationGroupTrailingStopField = QLineEdit(self.ActiveTradesTabMainListTradesStackedWidgetEditEditTradeInformationGroup)
        self.ActiveTradesTabMainListTradesStackedWidgetEditEditTradeInformationGroupTrailingStopField.setObjectName("ActiveTradesTabMainListTradesStackedWidgetEditEditTradeInformationGroupTrailingStopField")
        self.ActiveTradesTabMainListTradesStackedWidgetEditEditTradeInformationGroupTrailingStopField.setGeometry(QRect(90, 105, 22, 22))

        self.ActiveTradesTabMainListTradesStackedWidgetEditEditTradeInformationGroupTrailingStopText = QLabel(self.ActiveTradesTabMainListTradesStackedWidgetEditEditTradeInformationGroup)
        self.ActiveTradesTabMainListTradesStackedWidgetEditEditTradeInformationGroupTrailingStopText.setObjectName(u"ActiveTradesTabMainListTradesStackedWidgetEditEditTradeInformationGroupTokensText")
        self.ActiveTradesTabMainListTradesStackedWidgetEditEditTradeInformationGroupTrailingStopText.setGeometry(QRect(115, 105, 20, 20))

        # Compound Profit Checkbox
        self.ActiveTradesTabMainListTradesStackedWidgetEditCompoundProfitCheckbox = QCheckBox(self.ActiveTradesTabMainListTradesStackedWidgetEditEditTradeInformationGroup)
        self.ActiveTradesTabMainListTradesStackedWidgetEditCompoundProfitCheckbox.setObjectName(u"ActiveTradesTabMainListTradesStackedWidgetEditCompoundProfitCheckbox")
        self.ActiveTradesTabMainListTradesStackedWidgetEditCompoundProfitCheckbox.setGeometry(QRect(10, 188, 191, 20))
        self.ActiveTradesTabMainListTradesStackedWidgetEditCompoundProfitCheckbox.setLayoutDirection(Qt.LayoutDirection.RightToLeft)

        # Accumulate Token Radio Buttons
        self.ActiveTradesTabMainListTradesStackedWidgetEditAccumulateTokenTitle = QLabel(self.ActiveTradesTabMainListTradesStackedWidgetEditEditTradeInformationGroup)
        self.ActiveTradesTabMainListTradesStackedWidgetEditAccumulateTokenTitle.setObjectName(u"ActiveTradesTabMainListTradesStackedWidgetEditAccumulateTokenTitle")
        self.ActiveTradesTabMainListTradesStackedWidgetEditAccumulateTokenTitle.setGeometry(QRect(10, 130, 171, 20))
        self.ActiveTradesTabMainListTradesStackedWidgetEditAccumulateTokenTitle.setFont(font_bold)
        self.ActiveTradesTabMainListTradesStackedWidgetEditAccumulateTokenRadioButtonOne = QRadioButton(self.ActiveTradesTabMainListTradesStackedWidgetEditEditTradeInformationGroup)
        self.ActiveTradesTabMainListTradesStackedWidgetEditAccumulateTokenRadioButtonOne.setObjectName(u"ActiveTradesTabMainListTradesStackedWidgetEditAccumulateTokenRadioButtonOne")
        self.ActiveTradesTabMainListTradesStackedWidgetEditAccumulateTokenRadioButtonOne.setGeometry(QRect(10, 150, 71, 20))
        self.ActiveTradesTabMainListTradesStackedWidgetEditAccumulateTokenRadioButtonTwo = QRadioButton(self.ActiveTradesTabMainListTradesStackedWidgetEditEditTradeInformationGroup)
        self.ActiveTradesTabMainListTradesStackedWidgetEditAccumulateTokenRadioButtonTwo.setObjectName(u"ActiveTradesTabMainListTradesStackedWidgetEditAccumulateTokenRadioButtonTwo")
        self.ActiveTradesTabMainListTradesStackedWidgetEditAccumulateTokenRadioButtonTwo.setGeometry(QRect(10, 150, 71, 20))

        self.ActiveTradesTabMainListTradesStackedWidgetEditText = QLabel(self.Edit)
        self.ActiveTradesTabMainListTradesStackedWidgetEditText.setObjectName(u"ActiveTradesTabMainListTradesStackedWidgetEditText")
        self.ActiveTradesTabMainListTradesStackedWidgetEditText.setGeometry(QRect(240, 30, 541, 60))
        self.ActiveTradesTabMainListTradesStackedWidgetEditText.setWordWrap(True)

        # AI Strategy Indicators Group
        self.ActiveTradesTabMainListTradesStackedWidgetEditAIStrategyIndicatorsGroup = QGroupBox(self.Edit)
        self.ActiveTradesTabMainListTradesStackedWidgetEditAIStrategyIndicatorsGroup.setObjectName(u"ActiveTradesTabMainListTradesStackedWidgetEditAIStrategyIndicatorsGroup")
        self.ActiveTradesTabMainListTradesStackedWidgetEditAIStrategyIndicatorsGroup.setGeometry(QRect(229, 100, 557, 130))

        self.ActiveTradesTabMainListTradesStackedWidgetEditAIStrategyIndicatorsGroupRSILowTitle = QLabel(self.ActiveTradesTabMainListTradesStackedWidgetEditAIStrategyIndicatorsGroup)
        self.ActiveTradesTabMainListTradesStackedWidgetEditAIStrategyIndicatorsGroupRSILowTitle.setObjectName(u"ActiveTradesTabMainListTradesStackedWidgetEditAIStrategyIndicatorsGroupRSILowTitle")
        self.ActiveTradesTabMainListTradesStackedWidgetEditAIStrategyIndicatorsGroupRSILowTitle.setGeometry(QRect(10, 20, 530, 65))
        self.ActiveTradesTabMainListTradesStackedWidgetEditAIStrategyIndicatorsGroupRSILowTitle.setWordWrap(True)

        self.ActiveTradesTabMainListTradesStackedWidgetEditAIStrategyIndicatorsGroupSelectedCheckbox = QCheckBox(self.ActiveTradesTabMainListTradesStackedWidgetEditAIStrategyIndicatorsGroup)
        self.ActiveTradesTabMainListTradesStackedWidgetEditAIStrategyIndicatorsGroupSelectedCheckbox.setObjectName(u"ActiveTradesTabMainListTradesStackedWidgetEditAIStrategyIndicatorsGroupSelectedCheckbox")
        self.ActiveTradesTabMainListTradesStackedWidgetEditAIStrategyIndicatorsGroupSelectedCheckbox.setGeometry(QRect(395, 105, 150, 20))
        self.ActiveTradesTabMainListTradesStackedWidgetEditAIStrategyIndicatorsGroupSelectedCheckbox.setLayoutDirection(Qt.LayoutDirection.RightToLeft)

        # RSI Indicator GroupBox and widgets
        self.ActiveTradesTabMainListTradesStackedWidgetEditRSIIndicatorGroup = QGroupBox(self.Edit)
        self.ActiveTradesTabMainListTradesStackedWidgetEditRSIIndicatorGroup.setObjectName("ActiveTradesTabMainListTradesStackedWidgetEditRSIIndicatorGroup")
        self.ActiveTradesTabMainListTradesStackedWidgetEditRSIIndicatorGroup.setGeometry(QRect(400, 245, 181, 135))

        self.ActiveTradesTabMainListTradesStackedWidgetEditRSIIndicatorGroupRSILowValueTitle = QLabel(self.ActiveTradesTabMainListTradesStackedWidgetEditRSIIndicatorGroup)
        self.ActiveTradesTabMainListTradesStackedWidgetEditRSIIndicatorGroupRSILowValueTitle.setObjectName("ActiveTradesTabMainListTradesStackedWidgetEditRSIIndicatorGroupRSILowValueTitle")
        self.ActiveTradesTabMainListTradesStackedWidgetEditRSIIndicatorGroupRSILowValueTitle.setGeometry(QRect(10, 20, 81, 20))

        self.ActiveTradesTabMainListTradesStackedWidgetEditRSIIndicatorGroupRSIHighValueTitle = QLabel(self.ActiveTradesTabMainListTradesStackedWidgetEditRSIIndicatorGroup)
        self.ActiveTradesTabMainListTradesStackedWidgetEditRSIIndicatorGroupRSIHighValueTitle.setObjectName("ActiveTradesTabMainListTradesStackedWidgetEditRSIIndicatorGroupRSIHighValueTitle")
        self.ActiveTradesTabMainListTradesStackedWidgetEditRSIIndicatorGroupRSIHighValueTitle.setGeometry(QRect(10, 50, 81, 20))

        self.ActiveTradesTabMainListTradesStackedWidgetEditRSIIndicatorGroupRSIPeriodTitle = QLabel(self.ActiveTradesTabMainListTradesStackedWidgetEditRSIIndicatorGroup)
        self.ActiveTradesTabMainListTradesStackedWidgetEditRSIIndicatorGroupRSIPeriodTitle.setObjectName("ActiveTradesTabMainListTradesStackedWidgetEditRSIIndicatorGroupRSIPeriodTitle")
        self.ActiveTradesTabMainListTradesStackedWidgetEditRSIIndicatorGroupRSIPeriodTitle.setGeometry(QRect(10, 80, 81, 20))

        self.ActiveTradesTabMainListTradesStackedWidgetEditRSIIndicatorGroupRSILowValueField = QLineEdit(self.ActiveTradesTabMainListTradesStackedWidgetEditRSIIndicatorGroup)
        self.ActiveTradesTabMainListTradesStackedWidgetEditRSIIndicatorGroupRSILowValueField.setObjectName("ActiveTradesTabMainListTradesStackedWidgetEditRSIIndicatorGroupRSILowValueField")
        self.ActiveTradesTabMainListTradesStackedWidgetEditRSIIndicatorGroupRSILowValueField.setGeometry(QRect(130, 20, 41, 22))

        self.ActiveTradesTabMainListTradesStackedWidgetEditRSIIndicatorGroupRSIHighValueField = QLineEdit(self.ActiveTradesTabMainListTradesStackedWidgetEditRSIIndicatorGroup)
        self.ActiveTradesTabMainListTradesStackedWidgetEditRSIIndicatorGroupRSIHighValueField.setObjectName("ActiveTradesTabMainListTradesStackedWidgetEditRSIIndicatorGroupRSIHighValueField")
        self.ActiveTradesTabMainListTradesStackedWidgetEditRSIIndicatorGroupRSIHighValueField.setGeometry(QRect(130, 50, 41, 22))

        self.ActiveTradesTabMainListTradesStackedWidgetEditRSIIndicatorGroupRSIPeriodField = QLineEdit(self.ActiveTradesTabMainListTradesStackedWidgetEditRSIIndicatorGroup)
        self.ActiveTradesTabMainListTradesStackedWidgetEditRSIIndicatorGroupRSIPeriodField.setObjectName("ActiveTradesTabMainListTradesStackedWidgetEditRSIIndicatorGroupRSIPeriodField")
        self.ActiveTradesTabMainListTradesStackedWidgetEditRSIIndicatorGroupRSIPeriodField.setGeometry(QRect(130, 80, 41, 22))

        self.ActiveTradesTabMainListTradesStackedWidgetEditRSIIndicatorGroupIndicatorSelectedCheckbox = QCheckBox(self.ActiveTradesTabMainListTradesStackedWidgetEditRSIIndicatorGroup)
        self.ActiveTradesTabMainListTradesStackedWidgetEditRSIIndicatorGroupIndicatorSelectedCheckbox.setObjectName("ActiveTradesTabMainListTradesStackedWidgetEditRSIIndicatorGroupIndicatorSelectedCheckbox")
        self.ActiveTradesTabMainListTradesStackedWidgetEditRSIIndicatorGroupIndicatorSelectedCheckbox.setGeometry(QRect(10, 110, 161, 20))
        self.ActiveTradesTabMainListTradesStackedWidgetEditRSIIndicatorGroupIndicatorSelectedCheckbox.setLayoutDirection(Qt.LayoutDirection.RightToLeft)

        # MACD Indicator GroupBox and widgets
        self.ActiveTradesTabMainListTradesStackedWidgetEditMACDIndicatorGroup = QGroupBox(self.Edit)
        self.ActiveTradesTabMainListTradesStackedWidgetEditMACDIndicatorGroup.setObjectName("ActiveTradesTabMainListTradesStackedWidgetEditMACDIndicatorGroup")
        self.ActiveTradesTabMainListTradesStackedWidgetEditMACDIndicatorGroup.setGeometry(QRect(590, 245, 196, 135))

        self.ActiveTradesTabMainListTradesStackedWidgetEditMACDIndicatorGroupMACDLowTimeframeTitle = QLabel(self.ActiveTradesTabMainListTradesStackedWidgetEditMACDIndicatorGroup)
        self.ActiveTradesTabMainListTradesStackedWidgetEditMACDIndicatorGroupMACDLowTimeframeTitle.setObjectName("ActiveTradesTabMainListTradesStackedWidgetEditMACDIndicatorGroupMACDLowTimeframeTitle")
        self.ActiveTradesTabMainListTradesStackedWidgetEditMACDIndicatorGroupMACDLowTimeframeTitle.setGeometry(QRect(10, 20, 131, 20))

        self.ActiveTradesTabMainListTradesStackedWidgetEditMACDIndicatorGroupMACDHighTimeframeTitle = QLabel(self.ActiveTradesTabMainListTradesStackedWidgetEditMACDIndicatorGroup)
        self.ActiveTradesTabMainListTradesStackedWidgetEditMACDIndicatorGroupMACDHighTimeframeTitle.setObjectName("ActiveTradesTabMainListTradesStackedWidgetEditMACDIndicatorGroupMACDHighTimeframeTitle")
        self.ActiveTradesTabMainListTradesStackedWidgetEditMACDIndicatorGroupMACDHighTimeframeTitle.setGeometry(QRect(10, 50, 131, 20))

        self.ActiveTradesTabMainListTradesStackedWidgetEditMACDIndicatorGroupMACDSignalPeriodTitle = QLabel(self.ActiveTradesTabMainListTradesStackedWidgetEditMACDIndicatorGroup)
        self.ActiveTradesTabMainListTradesStackedWidgetEditMACDIndicatorGroupMACDSignalPeriodTitle.setObjectName("ActiveTradesTabMainListTradesStackedWidgetEditMACDIndicatorGroupMACDSignalPeriodTitle")
        self.ActiveTradesTabMainListTradesStackedWidgetEditMACDIndicatorGroupMACDSignalPeriodTitle.setGeometry(QRect(10, 80, 111, 20))

        self.ActiveTradesTabMainListTradesStackedWidgetEditMACDIndicatorGroupMACDLowTimeframeField = QLineEdit(self.ActiveTradesTabMainListTradesStackedWidgetEditMACDIndicatorGroup)
        self.ActiveTradesTabMainListTradesStackedWidgetEditMACDIndicatorGroupMACDLowTimeframeField.setObjectName("ActiveTradesTabMainListTradesStackedWidgetEditMACDIndicatorGroupMACDLowTimeframeField")
        self.ActiveTradesTabMainListTradesStackedWidgetEditMACDIndicatorGroupMACDLowTimeframeField.setGeometry(QRect(145, 20, 41, 22))

        self.ActiveTradesTabMainListTradesStackedWidgetEditMACDIndicatorGroupMACDHighTimeframeField = QLineEdit(self.ActiveTradesTabMainListTradesStackedWidgetEditMACDIndicatorGroup)
        self.ActiveTradesTabMainListTradesStackedWidgetEditMACDIndicatorGroupMACDHighTimeframeField.setObjectName("ActiveTradesTabMainListTradesStackedWidgetEditMACDIndicatorGroupMACDHighTimeframeField")
        self.ActiveTradesTabMainListTradesStackedWidgetEditMACDIndicatorGroupMACDHighTimeframeField.setGeometry(QRect(145, 50, 41, 22))

        self.ActiveTradesTabMainListTradesStackedWidgetEditMACDIndicatorGroupMACDSignalPeriodField = QLineEdit(self.ActiveTradesTabMainListTradesStackedWidgetEditMACDIndicatorGroup)
        self.ActiveTradesTabMainListTradesStackedWidgetEditMACDIndicatorGroupMACDSignalPeriodField.setObjectName("ActiveTradesTabMainListTradesStackedWidgetEditMACDIndicatorGroupMACDSignalPeriodField")
        self.ActiveTradesTabMainListTradesStackedWidgetEditMACDIndicatorGroupMACDSignalPeriodField.setGeometry(QRect(145, 80, 41, 22))

        self.ActiveTradesTabMainListTradesStackedWidgetEditMACDIndicatorGroupIndicatorSelectedCheckbox = QCheckBox(self.ActiveTradesTabMainListTradesStackedWidgetEditMACDIndicatorGroup)
        self.ActiveTradesTabMainListTradesStackedWidgetEditMACDIndicatorGroupIndicatorSelectedCheckbox.setObjectName("ActiveTradesTabMainListTradesStackedWidgetEditMACDIndicatorGroupIndicatorSelectedCheckbox")
        self.ActiveTradesTabMainListTradesStackedWidgetEditMACDIndicatorGroupIndicatorSelectedCheckbox.setGeometry(QRect(10, 110, 176, 20))
        self.ActiveTradesTabMainListTradesStackedWidgetEditMACDIndicatorGroupIndicatorSelectedCheckbox.setLayoutDirection(Qt.LayoutDirection.RightToLeft)

        # BB Indicator GroupBox and widgets
        self.ActiveTradesTabMainListTradesStackedWidgetEditBBIndicatorGroup = QGroupBox(self.Edit)
        self.ActiveTradesTabMainListTradesStackedWidgetEditBBIndicatorGroup.setObjectName("ActiveTradesTabMainListTradesStackedWidgetEditBBIndicatorGroup")
        self.ActiveTradesTabMainListTradesStackedWidgetEditBBIndicatorGroup.setGeometry(QRect(210, 245, 181, 135))

        self.ActiveTradesTabMainListTradesStackedWidgetEditBBIndicatorGroupBBPeriodTitle = QLabel(self.ActiveTradesTabMainListTradesStackedWidgetEditBBIndicatorGroup)
        self.ActiveTradesTabMainListTradesStackedWidgetEditBBIndicatorGroupBBPeriodTitle.setObjectName("ActiveTradesTabMainListTradesStackedWidgetEditBBIndicatorGroupBBPeriodTitle")
        self.ActiveTradesTabMainListTradesStackedWidgetEditBBIndicatorGroupBBPeriodTitle.setGeometry(QRect(10, 20, 71, 20))

        self.ActiveTradesTabMainListTradesStackedWidgetEditBBIndicatorGroupBBStdDevMultiplierTitle = QLabel(self.ActiveTradesTabMainListTradesStackedWidgetEditBBIndicatorGroup)
        self.ActiveTradesTabMainListTradesStackedWidgetEditBBIndicatorGroupBBStdDevMultiplierTitle.setObjectName("ActiveTradesTabMainListTradesStackedWidgetEditBBIndicatorGroupBBStdDevMultiplierTitle")
        self.ActiveTradesTabMainListTradesStackedWidgetEditBBIndicatorGroupBBStdDevMultiplierTitle.setGeometry(QRect(10, 50, 121, 20))

        self.ActiveTradesTabMainListTradesStackedWidgetEditBBIndicatorGroupBBPeriodField = QLineEdit(self.ActiveTradesTabMainListTradesStackedWidgetEditBBIndicatorGroup)
        self.ActiveTradesTabMainListTradesStackedWidgetEditBBIndicatorGroupBBPeriodField.setObjectName("ActiveTradesTabMainListTradesStackedWidgetEditBBIndicatorGroupBBPeriodField")
        self.ActiveTradesTabMainListTradesStackedWidgetEditBBIndicatorGroupBBPeriodField.setGeometry(QRect(130, 20, 41, 22))

        self.ActiveTradesTabMainListTradesStackedWidgetEditBBIndicatorGroupBBStdDevMultiplierField = QLineEdit(self.ActiveTradesTabMainListTradesStackedWidgetEditBBIndicatorGroup)
        self.ActiveTradesTabMainListTradesStackedWidgetEditBBIndicatorGroupBBStdDevMultiplierField.setObjectName("ActiveTradesTabMainListTradesStackedWidgetEditBBIndicatorGroupBBStdDevMultiplierField")
        self.ActiveTradesTabMainListTradesStackedWidgetEditBBIndicatorGroupBBStdDevMultiplierField.setGeometry(QRect(130, 50, 41, 22))

        self.ActiveTradesTabMainListTradesStackedWidgetEditBBIndicatorGroupIndicatorSelectedCheckbox = QCheckBox(self.ActiveTradesTabMainListTradesStackedWidgetEditBBIndicatorGroup)
        self.ActiveTradesTabMainListTradesStackedWidgetEditBBIndicatorGroupIndicatorSelectedCheckbox.setObjectName("ActiveTradesTabMainListTradesStackedWidgetEditBBIndicatorGroupIndicatorSelectedCheckbox")
        self.ActiveTradesTabMainListTradesStackedWidgetEditBBIndicatorGroupIndicatorSelectedCheckbox.setGeometry(QRect(10, 110, 161, 20))
        self.ActiveTradesTabMainListTradesStackedWidgetEditBBIndicatorGroupIndicatorSelectedCheckbox.setLayoutDirection(Qt.LayoutDirection.RightToLeft)

        # MA Crossover Indicator GroupBox and widgets
        self.ActiveTradesTabMainListTradesStackedWidgetEditMACrossoverIndicatorGroup = QGroupBox(self.Edit)
        self.ActiveTradesTabMainListTradesStackedWidgetEditMACrossoverIndicatorGroup.setObjectName("ActiveTradesTabMainListTradesStackedWidgetEditMACrossoverIndicatorGroup")
        self.ActiveTradesTabMainListTradesStackedWidgetEditMACrossoverIndicatorGroup.setGeometry(QRect(10, 245, 191, 135))

        self.ActiveTradesTabMainListTradesStackedWidgetEditMACrossoverIndicatorGroupMACrossShortTitle = QLabel(self.ActiveTradesTabMainListTradesStackedWidgetEditMACrossoverIndicatorGroup)
        self.ActiveTradesTabMainListTradesStackedWidgetEditMACrossoverIndicatorGroupMACrossShortTitle.setObjectName("ActiveTradesTabMainListTradesStackedWidgetEditMACrossoverIndicatorGroupMACrossShortTitle")
        self.ActiveTradesTabMainListTradesStackedWidgetEditMACrossoverIndicatorGroupMACrossShortTitle.setGeometry(QRect(10, 20, 91, 20))

        self.ActiveTradesTabMainListTradesStackedWidgetEditMACrossoverIndicatorGroupMACrossLongTitle = QLabel(self.ActiveTradesTabMainListTradesStackedWidgetEditMACrossoverIndicatorGroup)
        self.ActiveTradesTabMainListTradesStackedWidgetEditMACrossoverIndicatorGroupMACrossLongTitle.setObjectName("ActiveTradesTabMainListTradesStackedWidgetEditMACrossoverIndicatorGroupMACrossLongTitle")
        self.ActiveTradesTabMainListTradesStackedWidgetEditMACrossoverIndicatorGroupMACrossLongTitle.setGeometry(QRect(10, 50, 101, 20))

        self.ActiveTradesTabMainListTradesStackedWidgetEditMACrossoverIndicatorGroupMACrossLongField = QLineEdit(self.ActiveTradesTabMainListTradesStackedWidgetEditMACrossoverIndicatorGroup)
        self.ActiveTradesTabMainListTradesStackedWidgetEditMACrossoverIndicatorGroupMACrossLongField.setObjectName("ActiveTradesTabMainListTradesStackedWidgetEditMACrossoverIndicatorGroupMACrossLongField")
        self.ActiveTradesTabMainListTradesStackedWidgetEditMACrossoverIndicatorGroupMACrossLongField.setGeometry(QRect(140, 50, 41, 22))

        self.ActiveTradesTabMainListTradesStackedWidgetEditMACrossoverIndicatorGroupMACrossShortField = QLineEdit(self.ActiveTradesTabMainListTradesStackedWidgetEditMACrossoverIndicatorGroup)
        self.ActiveTradesTabMainListTradesStackedWidgetEditMACrossoverIndicatorGroupMACrossShortField.setObjectName("ActiveTradesTabMainListTradesStackedWidgetEditMACrossoverIndicatorGroupMACrossShortField")
        self.ActiveTradesTabMainListTradesStackedWidgetEditMACrossoverIndicatorGroupMACrossShortField.setGeometry(QRect(140, 20, 41, 22))

        self.ActiveTradesTabMainListTradesStackedWidgetEditMACrossoverIndicatorGroupIndicatorSelectedCheckbox = QCheckBox(self.ActiveTradesTabMainListTradesStackedWidgetEditMACrossoverIndicatorGroup)
        self.ActiveTradesTabMainListTradesStackedWidgetEditMACrossoverIndicatorGroupIndicatorSelectedCheckbox.setObjectName("ActiveTradesTabMainListTradesStackedWidgetEditMACrossoverIndicatorGroupIndicatorSelectedCheckbox")
        self.ActiveTradesTabMainListTradesStackedWidgetEditMACrossoverIndicatorGroupIndicatorSelectedCheckbox.setGeometry(QRect(10, 110, 171, 20))
        self.ActiveTradesTabMainListTradesStackedWidgetEditMACrossoverIndicatorGroupIndicatorSelectedCheckbox.setLayoutDirection(Qt.LayoutDirection.RightToLeft)

        # Ping Pong Indicator GroupBox and widgets
        self.ActiveTradesTabMainListTradesStackedWidgetEditPingPongIndicatorGroup = QGroupBox(self.Edit)
        self.ActiveTradesTabMainListTradesStackedWidgetEditPingPongIndicatorGroup.setObjectName(u"ActiveTradesTabMainListTradesStackedWidgetEditPingPongIndicatorGroup")
        self.ActiveTradesTabMainListTradesStackedWidgetEditPingPongIndicatorGroup.setGeometry(QRect(10, 400, 261, 116))

        self.ActiveTradesTabMainListTradesStackedWidgetEditPingPongIndicatorGroupBuyPriceTitle = QLabel(self.ActiveTradesTabMainListTradesStackedWidgetEditPingPongIndicatorGroup)
        self.ActiveTradesTabMainListTradesStackedWidgetEditPingPongIndicatorGroupBuyPriceTitle.setObjectName(u"ActiveTradesTabMainListTradesStackedWidgetEditPingPongIndicatorGroupBuyPriceTitle")
        self.ActiveTradesTabMainListTradesStackedWidgetEditPingPongIndicatorGroupBuyPriceTitle.setGeometry(QRect(10, 20, 61, 20))

        self.ActiveTradesTabMainListTradesStackedWidgetEditPingPongIndicatorGroupSellPriceTitle = QLabel(self.ActiveTradesTabMainListTradesStackedWidgetEditPingPongIndicatorGroup)
        self.ActiveTradesTabMainListTradesStackedWidgetEditPingPongIndicatorGroupSellPriceTitle.setObjectName(u"ActiveTradesTabMainListTradesStackedWidgetEditPingPongIndicatorGroupSellPriceTitle")
        self.ActiveTradesTabMainListTradesStackedWidgetEditPingPongIndicatorGroupSellPriceTitle.setGeometry(QRect(10, 50, 71, 20))

        self.ActiveTradesTabMainListTradesStackedWidgetEditPingPongIndicatorGroupBuyPriceField = QLineEdit(self.ActiveTradesTabMainListTradesStackedWidgetEditPingPongIndicatorGroup)
        self.ActiveTradesTabMainListTradesStackedWidgetEditPingPongIndicatorGroupBuyPriceField.setObjectName(u"ActiveTradesTabMainListTradesStackedWidgetEditPingPongIndicatorGroupBuyPriceField")
        self.ActiveTradesTabMainListTradesStackedWidgetEditPingPongIndicatorGroupBuyPriceField.setGeometry(QRect(80, 20, 101, 22))

        self.ActiveTradesTabMainListTradesStackedWidgetEditPingPongIndicatorGroupSellPriceField = QLineEdit(self.ActiveTradesTabMainListTradesStackedWidgetEditPingPongIndicatorGroup)
        self.ActiveTradesTabMainListTradesStackedWidgetEditPingPongIndicatorGroupSellPriceField.setObjectName(u"ActiveTradesTabMainListTradesStackedWidgetEditPingPongIndicatorGroupSellPriceField")
        self.ActiveTradesTabMainListTradesStackedWidgetEditPingPongIndicatorGroupSellPriceField.setGeometry(QRect(80, 50, 101, 22))

        self.ActiveTradesTabMainListTradesStackedWidgetEditPingPongIndicatorGroupIndicatorSelectedCheckbox = QCheckBox(self.ActiveTradesTabMainListTradesStackedWidgetEditPingPongIndicatorGroup)
        self.ActiveTradesTabMainListTradesStackedWidgetEditPingPongIndicatorGroupIndicatorSelectedCheckbox.setObjectName(u"ActiveTradesTabMainListTradesStackedWidgetEditPingPongIndicatorGroupIndicatorSelectedCheckbox")
        self.ActiveTradesTabMainListTradesStackedWidgetEditPingPongIndicatorGroupIndicatorSelectedCheckbox.setGeometry(QRect(10, 90, 190, 20))
        self.ActiveTradesTabMainListTradesStackedWidgetEditPingPongIndicatorGroupIndicatorSelectedCheckbox.setLayoutDirection(Qt.LayoutDirection.RightToLeft)

        self.ActiveTradesTabMainListTradesStackedWidgetEditPingPongIndicatorGroupBuyPriceSymbol = QLabel(self.ActiveTradesTabMainListTradesStackedWidgetEditPingPongIndicatorGroup)
        self.ActiveTradesTabMainListTradesStackedWidgetEditPingPongIndicatorGroupBuyPriceSymbol.setObjectName(u"ActiveTradesTabMainListTradesStackedWidgetEditPingPongIndicatorGroupBuyPriceSymbol")
        self.ActiveTradesTabMainListTradesStackedWidgetEditPingPongIndicatorGroupBuyPriceSymbol.setGeometry(QRect(190, 20, 61, 20))

        self.ActiveTradesTabMainListTradesStackedWidgetEditPingPongIndicatorGroupSellPriceSymbol = QLabel(self.ActiveTradesTabMainListTradesStackedWidgetEditPingPongIndicatorGroup)
        self.ActiveTradesTabMainListTradesStackedWidgetEditPingPongIndicatorGroupSellPriceSymbol.setObjectName(u"ActiveTradesTabMainListTradesStackedWidgetEditPingPongIndicatorGroupSellPriceSymbol")
        self.ActiveTradesTabMainListTradesStackedWidgetEditPingPongIndicatorGroupSellPriceSymbol.setGeometry(QRect(190, 50, 61, 20))

        # Current Prices Groupbox and Widget
        self.ActiveTradesTabMainListTradesStackedWidgetEditCurrentPricesGroup = QGroupBox(self.Edit)
        self.ActiveTradesTabMainListTradesStackedWidgetEditCurrentPricesGroup.setObjectName(u"ActiveTradesTabMainListTradesStackedWidgetEditCurrentPricesGroup")
        self.ActiveTradesTabMainListTradesStackedWidgetEditCurrentPricesGroup.setGeometry(QRect(290, 400, 291, 116))
        self.ActiveTradesTabMainListTradesStackedWidgetEditCurrentPricesGroupPriceOne = QLabel(self.ActiveTradesTabMainListTradesStackedWidgetEditCurrentPricesGroup)
        self.ActiveTradesTabMainListTradesStackedWidgetEditCurrentPricesGroupPriceOne.setObjectName(u"ActiveTradesTabMainListTradesStackedWidgetEditCurrentPricesGroupPriceOne")
        self.ActiveTradesTabMainListTradesStackedWidgetEditCurrentPricesGroupPriceOne.setGeometry(QRect(30, 30, 191, 20))
        self.ActiveTradesTabMainListTradesStackedWidgetEditCurrentPricesGroupPriceTwo = QLabel(self.ActiveTradesTabMainListTradesStackedWidgetEditCurrentPricesGroup)
        self.ActiveTradesTabMainListTradesStackedWidgetEditCurrentPricesGroupPriceTwo.setObjectName(u"ActiveTradesTabMainListTradesStackedWidgetEditCurrentPricesGroupPriceTwo")
        self.ActiveTradesTabMainListTradesStackedWidgetEditCurrentPricesGroupPriceTwo.setGeometry(QRect(30, 70, 191, 20))
        from gui.overlapping_icon_widget import OverlappingIconWidget
        self.ActiveTradesTabMainListTradesStackedWidgetEditCurrentPricesGroupIconsPlaceholder = OverlappingIconWidget(20, self.ActiveTradesTabMainListTradesStackedWidgetEditCurrentPricesGroup)
        self.ActiveTradesTabMainListTradesStackedWidgetEditCurrentPricesGroupIconsPlaceholder.setObjectName(u"ActiveTradesTabMainListTradesStackedWidgetEditCurrentPricesGroupIconsPlaceholder")
        self.ActiveTradesTabMainListTradesStackedWidgetEditCurrentPricesGroupIconsPlaceholder.setGeometry(QRect(230, 40, 45, 30))

        # Edit Trade Button
        self.ActiveTradesTabMainListTradesStackedWidgetEditEditTradeButton = QPushButton(self.Edit)
        self.ActiveTradesTabMainListTradesStackedWidgetEditEditTradeButton.setObjectName("ActiveTradesTabMainListTradesStackedWidgetEditEditTradeButton")
        self.ActiveTradesTabMainListTradesStackedWidgetEditEditTradeButton.setGeometry(QRect(600, 412, 180, 50))

        # Back Button
        self.ActiveTradesTabMainListTradesStackedWidgetEditBackButton = QPushButton(self.Edit)
        self.ActiveTradesTabMainListTradesStackedWidgetEditBackButton.setObjectName("ActiveTradesTabMainListTradesStackedWidgetEditBackButton")
        self.ActiveTradesTabMainListTradesStackedWidgetEditBackButton.setGeometry(QRect(600, 475, 180, 40))

        # Feedback Text Area
        self.ActiveTradesTabMainListTradesStackedWidgetEditFeedbackTextArea = QLabel(self.Edit)
        self.ActiveTradesTabMainListTradesStackedWidgetEditFeedbackTextArea.setObjectName("ActiveTradesTabMainListTradesStackedWidgetEditFeedbackTextArea")
        self.ActiveTradesTabMainListTradesStackedWidgetEditFeedbackTextArea.setGeometry(QRect(240, 0, 531, 31))

        self.ActiveTradesTabMainListTradesStackedWidget.addWidget(self.Edit)

        # --- Delete Page ---
        self.Delete = QWidget()
        self.Delete.setObjectName("Delete")

        self.ActiveTradesTabMainListTradesStackedWidgetDeleteTitle = QLabel(self.Delete)
        self.ActiveTradesTabMainListTradesStackedWidgetDeleteTitle.setObjectName("ActiveTradesTabMainListTradesStackedWidgetDeleteTitle")
        self.ActiveTradesTabMainListTradesStackedWidgetDeleteTitle.setGeometry(QRect(300, 40, 201, 61))
        font_delete = QFont()
        font_delete.setPointSize(24)
        font_delete.setBold(True)
        self.ActiveTradesTabMainListTradesStackedWidgetDeleteTitle.setFont(font_delete)

        self.ActiveTradesTabMainListTradesStackedWidgetDeleteText = QLabel(self.Delete)
        self.ActiveTradesTabMainListTradesStackedWidgetDeleteText.setObjectName("ActiveTradesTabMainListTradesStackedWidgetDeleteText")
        self.ActiveTradesTabMainListTradesStackedWidgetDeleteText.setGeometry(QRect(150, 100, 501, 51))
        self.ActiveTradesTabMainListTradesStackedWidgetDeleteText.setWordWrap(True)

        self.ActiveTradesTabMainListTradesStackedWidgetDeleteBackButton = QPushButton(self.Delete)
        self.ActiveTradesTabMainListTradesStackedWidgetDeleteBackButton.setObjectName("ActiveTradesTabMainListTradesStackedWidgetDeleteBackButton")
        self.ActiveTradesTabMainListTradesStackedWidgetDeleteBackButton.setGeometry(QRect(160, 280, 91, 31))

        self.ActiveTradesTabMainListTradesStackedWidgetDeleteDeletButton = QPushButton(self.Delete)
        self.ActiveTradesTabMainListTradesStackedWidgetDeleteDeletButton.setObjectName("ActiveTradesTabMainListTradesStackedWidgetDeleteDeletButton")
        self.ActiveTradesTabMainListTradesStackedWidgetDeleteDeletButton.setGeometry(QRect(494, 280, 131, 31))

        self.ActiveTradesTabMainListTradesStackedWidget.addWidget(self.Delete)

        # Raise Widgets
        #self.ActiveTradesTabMainListTradesStackedWidgetEditAIStrategyIndicatorsGroup.raise_()
        #self.ActiveTradesTabMainListTradesStackedWidgetEditAIStrategyIndicatorsGroupRSILowTitle.raise_()
        #self.ActiveTradesTabMainListTradesStackedWidgetEditAIStrategyIndicatorsGroupSelectedCheckbox.raise_()

        # Set initial page to List
        self.ActiveTradesTabMainListTradesStackedWidget.setCurrentIndex(0)
    
    def _setup_information_page_legacy(self):
        """Legacy Information page setup - converted in Phase 3"""
        # Information page now handled in responsive version
        # Keeping this method for structure consistency
        pass
    
    def _setup_edit_page_legacy(self):
        """Legacy Edit page setup - to be converted in Phase 4-5"""
        # Placeholder - will extract Edit page code here in Phase 4-5
        pass
    
    def _setup_delete_page_legacy(self):
        """Legacy Delete page setup - converted in Phase 2"""
        # Delete page now handled in responsive version
        # Keeping this method for structure consistency
        pass
    
    def retranslateUi(self, ActiveTradesTabMain):
        _translate = QCoreApplication.translate

        self.ActiveTradesTabMainListTradesStackedWidget.setWhatsThis("")

        # Legacy mode widgets (Information and Edit pages not yet converted)
        if not USE_RESPONSIVE_LAYOUTS:
            # Information Group Titles
            self.ActiveTradesTabMainListTradesStackedWidgetInformationTradeInformationGroup.setTitle(_translate("ActiveTradesTabMain", " Trade Information "))
            self.ActiveTradesTabMainListTradesStackedWidgetInformationTradeInformationGroupTradeIdTitle.setText(_translate("ActiveTradesTabMain", "Trade ID:"))
            self.ActiveTradesTabMainListTradesStackedWidgetInformationTradeInformationGroupCreationDateTitle.setText(_translate("ActiveTradesTabMain", "Creation Date:"))
            self.ActiveTradesTabMainListTradesStackedWidgetInformationTradeInformationGroupCreationValueTitle.setText(_translate("ActiveTradesTabMain", "Creation Value:"))
            self.ActiveTradesTabMainListTradesStackedWidgetInformationTradeInformationGroupTimesFlippedTitle.setText(_translate("ActiveTradesTabMain", "Times Flipped:"))
            self.ActiveTradesTabMainListTradesStackedWidgetInformationTradeInformationGroupProfitableFlipsTitle.setText(_translate("ActiveTradesTabMain", "Profitable Flips:"))
            self.ActiveTradesTabMainListTradesStackedWidgetInformationTradeInformationGroupUnprofitablFlipsTitle.setText(_translate("ActiveTradesTabMain", "Unprofitable Flips:"))
            self.ActiveTradesTabMainListTradesStackedWidgetInformationTradeInformationGroupWinRatioTitle.setText(_translate("ActiveTradesTabMain", "Win Ratio:"))
            self.ActiveTradesTabMainListTradesStackedWidgetInformationTradeInformationGroupTotalProfitTitle.setText(_translate("ActiveTradesTabMain", "Total Profit:"))
            self.ActiveTradesTabMainListTradesStackedWidgetInformationTradeInformationGroupIndicatorUsedTitle.setText(_translate("ActiveTradesTabMain", "Indicator Used:"))
            self.ActiveTradesTabMainListTradesStackedWidgetInformationTradeInformationGroupTradeVolumeTitle.setText(_translate("ActiveTradesTabMain", "Trade Volume:"))
            self.ActiveTradesTabMainListTradesStackedWidgetInformationTradeInformationGroupCurrentTradeValueTitle.setText(_translate("ActiveTradesTabMain", "Current Trade Value:"))

            # Information Group Values
            self.ActiveTradesTabMainListTradesStackedWidgetInformationTradeInformationGroupTradeIdTextArea.setText(_translate("ActiveTradesTabMain", "23"))
            self.ActiveTradesTabMainListTradesStackedWidgetInformationTradeInformationGroupCreationDateTextArea.setText(_translate("ActiveTradesTabMain", "19th May 2025 @ 17:23"))
            self.ActiveTradesTabMainListTradesStackedWidgetInformationTradeInformationGroupCreationValueTextArea.setText(_translate("ActiveTradesTabMain", "100,000 XRD"))
            self.ActiveTradesTabMainListTradesStackedWidgetInformationTradeInformationGroupTimesFlippedTextArea.setText(_translate("ActiveTradesTabMain", "17"))
            self.ActiveTradesTabMainListTradesStackedWidgetInformationTradeInformationGroupProfitableFlipsTextArea.setText(_translate("ActiveTradesTabMain", "10"))
            self.ActiveTradesTabMainListTradesStackedWidgetInformationTradeInformationGroupUnprofitablFlipsTextArea.setText(_translate("ActiveTradesTabMain", "7"))
            self.ActiveTradesTabMainListTradesStackedWidgetInformationTradeInformationGroupWinRatioTextArea.setText(_translate("ActiveTradesTabMain", "TextLabel"))
            self.ActiveTradesTabMainListTradesStackedWidgetInformationTradeInformationGroupTotalProfitTextArea.setText(_translate("ActiveTradesTabMain", "58,947 XRD"))
            self.ActiveTradesTabMainListTradesStackedWidgetInformationTradeInformationGroupIndicatorUsedTextArea.setText(_translate("ActiveTradesTabMain", "AI Strategy"))
            self.ActiveTradesTabMainListTradesStackedWidgetInformationTradeInformationGroupTradeVolumeTextArea.setText(_translate("ActiveTradesTabMain", "2,129,486.4769   XRD"))
            self.ActiveTradesTabMainListTradesStackedWidgetInformationTradeInformationGroupCurrentTradeValueTextArea.setText(_translate("ActiveTradesTabMain", "158,947.00"))
            self.ActiveTradesTabMainListTradesStackedWidgetInformationTradeInformationGroupCurrentTradeValueTickerTextArea.setText(_translate("ActiveTradesTabMain", " "))
            self.ActiveTradesTabMainListTradesStackedWidgetEditEditTradeInformationGroupStopLossField.setPlaceholderText(_translate("ActiveTradesTabMain", "0"))
            self.ActiveTradesTabMainListTradesStackedWidgetEditEditTradeInformationGroupTrailingStopField.setPlaceholderText(_translate("ActiveTradesTabMain", "0"))
        
        # Information page texts - both legacy and responsive modes
        self.ActiveTradesTabMainListTradesStackedWidgetInformationBackToTradesListButton.setText(_translate("ActiveTradesTabMain", "Back To Trades List"))
        self.ActiveTradesTabMainListTradesStackedWidgetInformationChartText.setText(_translate("ActiveTradesTabMain", "The chart above shows how the market is seen by your chosen indicator/s."))

        if not USE_RESPONSIVE_LAYOUTS:
                # Edit Page
            self.ActiveTradesTabMainListTradesStackedWidgetEditEditTradeInformationGroup.setTitle(_translate("ActiveTradesTabMain", " Edit Trade Information"))
            self.ActiveTradesTabMainListTradesStackedWidgetEditEditTradeInformationGroupTradeIDTitle.setText(_translate("ActiveTradesTabMain", "Trade ID:"))
            self.ActiveTradesTabMainListTradesStackedWidgetEditEditTradeInformationGroupTradeIDTextArea.setText(_translate("ActiveTradesTabMain", "23"))
            self.ActiveTradesTabMainListTradesStackedWidgetEditEditTradeInformationGroupTradePairTitle.setText(_translate("ActiveTradesTabMain", "Trade Pair: "))
            self.ActiveTradesTabMainListTradesStackedWidgetEditEditTradeInformationGroupTradePairTextArea.setText(_translate("ActiveTradesTabMain", "XRD-xUSDC"))
            self.ActiveTradesTabMainListTradesStackedWidgetEditEditTradeInformationGroupTokensTitle.setText(_translate("ActiveTradesTabMain", "Tokens:"))
            self.ActiveTradesTabMainListTradesStackedWidgetEditEditTradeInformationGroupTokensField.setText(_translate("ActiveTradesTabMain", "123,456"))
            self.ActiveTradesTabMainListTradesStackedWidgetEditEditTradeInformationGroupTokensTicker.setText(_translate("ActiveTradesTabMain", "XRD"))
            self.ActiveTradesTabMainListTradesStackedWidgetEditEditTradeInformationGroupStopLossTitle.setText(_translate("ActiveTradesTabMain", "Stop Loss:"))
            self.ActiveTradesTabMainListTradesStackedWidgetEditEditTradeInformationGroupStopLossText.setText(_translate("ActiveTradesTabMain", " %"))
            self.ActiveTradesTabMainListTradesStackedWidgetEditEditTradeInformationGroupTrailingStopTitle.setText(_translate("ActiveTradesTabMain", "Trailing Stop:"))
            self.ActiveTradesTabMainListTradesStackedWidgetEditEditTradeInformationGroupTrailingStopText.setText(_translate("ActiveTradesTabMain", " %"))
        
        # Instruction text and AI Strategy - both legacy and responsive modes
        self.ActiveTradesTabMainListTradesStackedWidgetEditText.setText(_translate("ActiveTradesTabMain", "<html><head/><body><p>To edit this trade please check which indicators are &quot;selected&quot; and that you are happy with that selection. Then edit the indicator settings to be able to fine tune the trade a little more beyond the default settings.</p></body></html>"))

        # AI Strategy Indicators Group - Edit Trade Page
        self.ActiveTradesTabMainListTradesStackedWidgetEditAIStrategyIndicatorsGroup.setTitle(_translate("ActiveTradesTabMain", " AI Strategy Indicators  "))
        self.ActiveTradesTabMainListTradesStackedWidgetEditAIStrategyIndicatorsGroupRSILowTitle.setText(_translate("ActiveTradesTabMain", "<html><head/><body><p>The AI Strategy uses machine learning to adapt to market conditions. It has access to 8 indicators and choses the best for any given market. Weekly, it will backtest 27 different parameter combinations to make sure your trades are as optimised as possible.<br>Learn more about it in the 'Help' tab.</p></body></html>"))
        self.ActiveTradesTabMainListTradesStackedWidgetEditAIStrategyIndicatorsGroupSelectedCheckbox.setText(_translate("ActiveTradesTabMain", "Indicator Selected?       "))

        # RSI Indicator Group - Edit Trade Page
        self.ActiveTradesTabMainListTradesStackedWidgetEditRSIIndicatorGroup.setTitle(_translate("ActiveTradesTabMain", " RSI Indicator "))
        self.ActiveTradesTabMainListTradesStackedWidgetEditRSIIndicatorGroupRSILowValueTitle.setText(_translate("ActiveTradesTabMain", "RSI Low Value:"))
        self.ActiveTradesTabMainListTradesStackedWidgetEditRSIIndicatorGroupRSIHighValueTitle.setText(_translate("ActiveTradesTabMain", "RSI High Value:"))
        self.ActiveTradesTabMainListTradesStackedWidgetEditRSIIndicatorGroupRSIPeriodTitle.setText(_translate("ActiveTradesTabMain", "RSI Period"))
        self.ActiveTradesTabMainListTradesStackedWidgetEditRSIIndicatorGroupRSILowValueField.setText(_translate("ActiveTradesTabMain", "30"))
        self.ActiveTradesTabMainListTradesStackedWidgetEditRSIIndicatorGroupRSIHighValueField.setText(_translate("ActiveTradesTabMain", "70"))
        self.ActiveTradesTabMainListTradesStackedWidgetEditRSIIndicatorGroupRSIPeriodField.setText(_translate("ActiveTradesTabMain", "14"))
        self.ActiveTradesTabMainListTradesStackedWidgetEditRSIIndicatorGroupIndicatorSelectedCheckbox.setText(_translate("ActiveTradesTabMain", "Indicator Selected?      "))

        # MACD Indicator Group - Edit Trade Page
        self.ActiveTradesTabMainListTradesStackedWidgetEditMACDIndicatorGroup.setTitle(_translate("ActiveTradesTabMain", " MACD Indicator "))
        self.ActiveTradesTabMainListTradesStackedWidgetEditMACDIndicatorGroupMACDLowTimeframeTitle.setText(_translate("ActiveTradesTabMain", "MACD Low Timeframe:"))
        self.ActiveTradesTabMainListTradesStackedWidgetEditMACDIndicatorGroupMACDHighTimeframeTitle.setText(_translate("ActiveTradesTabMain", "MACD High Timeframe:"))
        self.ActiveTradesTabMainListTradesStackedWidgetEditMACDIndicatorGroupMACDSignalPeriodTitle.setText(_translate("ActiveTradesTabMain", "MACD Signal Period:"))
        self.ActiveTradesTabMainListTradesStackedWidgetEditMACDIndicatorGroupMACDLowTimeframeField.setText(_translate("ActiveTradesTabMain", "12"))
        self.ActiveTradesTabMainListTradesStackedWidgetEditMACDIndicatorGroupMACDHighTimeframeField.setText(_translate("ActiveTradesTabMain", "26"))
        self.ActiveTradesTabMainListTradesStackedWidgetEditMACDIndicatorGroupMACDSignalPeriodField.setText(_translate("ActiveTradesTabMain", "9"))
        self.ActiveTradesTabMainListTradesStackedWidgetEditMACDIndicatorGroupIndicatorSelectedCheckbox.setText(_translate("ActiveTradesTabMain", "Indicator Selected?                   "))

        # Bollinger Bands Indicator Group - Edit Trade Page
        self.ActiveTradesTabMainListTradesStackedWidgetEditBBIndicatorGroup.setTitle(_translate("ActiveTradesTabMain", " BB Indicator "))
        self.ActiveTradesTabMainListTradesStackedWidgetEditBBIndicatorGroupBBPeriodTitle.setText(_translate("ActiveTradesTabMain", "BB Period:"))
        self.ActiveTradesTabMainListTradesStackedWidgetEditBBIndicatorGroupBBStdDevMultiplierTitle.setText(_translate("ActiveTradesTabMain", "BB Std Dev Multiplier:"))
        self.ActiveTradesTabMainListTradesStackedWidgetEditBBIndicatorGroupBBPeriodField.setText(_translate("ActiveTradesTabMain", "20"))
        self.ActiveTradesTabMainListTradesStackedWidgetEditBBIndicatorGroupBBStdDevMultiplierField.setText(_translate("ActiveTradesTabMain", "2"))
        self.ActiveTradesTabMainListTradesStackedWidgetEditBBIndicatorGroupIndicatorSelectedCheckbox.setText(_translate("ActiveTradesTabMain", "Indicator Selected?                "))

        # MACrossover Indicator Group - Edit Trade Page
        self.ActiveTradesTabMainListTradesStackedWidgetEditMACrossoverIndicatorGroup.setTitle(_translate("ActiveTradesTabMain", " MA Crossover Indicator "))
        self.ActiveTradesTabMainListTradesStackedWidgetEditMACrossoverIndicatorGroupMACrossShortTitle.setText(_translate("ActiveTradesTabMain", "MA Cross Short:"))
        self.ActiveTradesTabMainListTradesStackedWidgetEditMACrossoverIndicatorGroupMACrossLongTitle.setText(_translate("ActiveTradesTabMain", "MA Cross Long:"))
        self.ActiveTradesTabMainListTradesStackedWidgetEditMACrossoverIndicatorGroupMACrossLongField.setText(_translate("ActiveTradesTabMain", "22"))
        self.ActiveTradesTabMainListTradesStackedWidgetEditMACrossoverIndicatorGroupMACrossShortField.setText(_translate("ActiveTradesTabMain", "8"))
        self.ActiveTradesTabMainListTradesStackedWidgetEditMACrossoverIndicatorGroupIndicatorSelectedCheckbox.setText(_translate("ActiveTradesTabMain", "Indicator Selected?       "))

        # Ping Pong Indicator Group - Edit Trade Page
        self.ActiveTradesTabMainListTradesStackedWidgetEditPingPongIndicatorGroup.setTitle(_translate("ActiveTradesTabMain", " Ping Pong Indicator"))
        self.ActiveTradesTabMainListTradesStackedWidgetEditPingPongIndicatorGroupBuyPriceTitle.setText(_translate("ActiveTradesTabMain", "Buy Price:"))
        self.ActiveTradesTabMainListTradesStackedWidgetEditPingPongIndicatorGroupSellPriceTitle.setText(_translate("ActiveTradesTabMain", "Sell Price:"))
        self.ActiveTradesTabMainListTradesStackedWidgetEditPingPongIndicatorGroupBuyPriceField.setPlaceholderText(_translate("ActiveTradesTabMain", "0.98"))
        self.ActiveTradesTabMainListTradesStackedWidgetEditPingPongIndicatorGroupSellPriceField.setPlaceholderText(_translate("ActiveTradesTabMain", "1.02"))
        self.ActiveTradesTabMainListTradesStackedWidgetEditPingPongIndicatorGroupIndicatorSelectedCheckbox.setText(_translate("ActiveTradesTabMain", "Indicator Selected?                       "))
        self.ActiveTradesTabMainListTradesStackedWidgetEditPingPongIndicatorGroupBuyPriceSymbol.setText(QCoreApplication.translate("AkondRadBotMainWindow", u"", None))
        self.ActiveTradesTabMainListTradesStackedWidgetEditPingPongIndicatorGroupSellPriceSymbol.setText(QCoreApplication.translate("AkondRadBotMainWindow", u"", None))

        # Current Prices Group - Edit Trade Page
        self.ActiveTradesTabMainListTradesStackedWidgetEditCurrentPricesGroup.setTitle(QCoreApplication.translate("AkondRadBotMainWindow", u"Current Prices", None))
        self.ActiveTradesTabMainListTradesStackedWidgetEditCurrentPricesGroupPriceOne.setText(QCoreApplication.translate("AkondRadBotMainWindow", u"Token one price for token two", None))
        self.ActiveTradesTabMainListTradesStackedWidgetEditCurrentPricesGroupPriceTwo.setText(QCoreApplication.translate("AkondRadBotMainWindow", u"Token two price for token one", None))
        
        # Compound Profit Checkbox - Edit Trade Page
        self.ActiveTradesTabMainListTradesStackedWidgetEditCompoundProfitCheckbox.setText(QCoreApplication.translate("AkondRadBotMainWindow", u"Compound Profit?                    ", None))

        # Accumulate Token Selection - Edit Trade Page
        self.ActiveTradesTabMainListTradesStackedWidgetEditAccumulateTokenTitle.setText(QCoreApplication.translate("AkondRadBotMainWindow", u"Accumulate: Token:", None))
        self.ActiveTradesTabMainListTradesStackedWidgetEditAccumulateTokenRadioButtonOne.setText(QCoreApplication.translate("AkondRadBotMainWindow", u"Token 1", None))
        self.ActiveTradesTabMainListTradesStackedWidgetEditAccumulateTokenRadioButtonTwo.setText(QCoreApplication.translate("AkondRadBotMainWindow", u"Token 2", None))

        # Edit Trade Button - Edit Trade Page
        self.ActiveTradesTabMainListTradesStackedWidgetEditEditTradeButton.setText(_translate("ActiveTradesTabMain", "Edit Trade"))

        # Back to Trade List Button - Edit Trade Page
        self.ActiveTradesTabMainListTradesStackedWidgetEditBackButton.setText(_translate("ActiveTradesTabMain", "Back to Trades"))

        # Edit Trade Feedback Text Area
        self.ActiveTradesTabMainListTradesStackedWidgetEditFeedbackTextArea.setText("")

        # Delete page (responsive mode)
        self.ActiveTradesTabMainListTradesStackedWidgetDeleteTitle.setText(_translate("ActiveTradesTabMain", "Delete Trade"))
        self.ActiveTradesTabMainListTradesStackedWidgetDeleteText.setText(_translate("ActiveTradesTabMain", "<html><head/><body><p>Are you sure you would like to delete this trade? Once deleted it can not be &quot;undeleted&quot;. Although you could recreate a similar trade again, any data created by this trade will be lost and data collection for it would have to start over.</p></body></html>"))
        self.ActiveTradesTabMainListTradesStackedWidgetDeleteBackButton.setText(_translate("ActiveTradesTabMain", "No, Go Back!"))
        self.ActiveTradesTabMainListTradesStackedWidgetDeleteDeletButton.setText(_translate("ActiveTradesTabMain", "Yes, Delete This Trade!"))