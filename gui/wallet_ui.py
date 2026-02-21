from PySide6.QtCore import QCoreApplication, QRect, Qt
from PySide6.QtGui import QFont, QPixmap
from PySide6.QtWidgets import (
    QFrame, QGridLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton, 
    QScrollArea, QSizePolicy, QTextEdit, QVBoxLayout, QWidget
)
from gui import resources_rc

# Toggle between responsive layouts and legacy setGeometry positioning
USE_RESPONSIVE_LAYOUTS = True

class Ui_WalletTabMain(object):
    def setupUi(self, WalletTabMain):
        if USE_RESPONSIVE_LAYOUTS:
            self._setupUi_responsive(WalletTabMain)
        else:
            self.setupUi_legacy(WalletTabMain)
        
        self.retranslateUi(WalletTabMain)
    
    def _setupUi_responsive(self, WalletTabMain):
        """Modern responsive layout using Qt layouts"""
        WalletTabMain.setObjectName("WalletTabMain")
        
        # Main vertical layout
        main_layout = QVBoxLayout(WalletTabMain)
        main_layout.setContentsMargins(15, 15, 15, 15)
        main_layout.setSpacing(10)
        
        # Section 1: Current Wallet Address (Frame One)
        self.WalletTabMainFrameOne = self._create_address_section()
        main_layout.addWidget(self.WalletTabMainFrameOne)
        
        # Section 2: Wallet Loading/Creation (Frame Two)
        self.WalletTabMainFrameTwo = self._create_wallet_controls_section()
        main_layout.addWidget(self.WalletTabMainFrameTwo)
        
        # Section 3: Balances + Withdraw (Frame Three)
        self.WalletTabMainFrameThree = self._create_balances_withdraw_section()
        main_layout.addWidget(self.WalletTabMainFrameThree, stretch=1)
    
    def _create_address_section(self):
        """Create current wallet address display section"""
        frame = QFrame()
        frame.setObjectName("WalletTabMainFrameOne")
        frame.setFrameShape(QFrame.Shape.StyledPanel)
        frame.setFrameShadow(QFrame.Shadow.Raised)
        frame.setMinimumHeight(60)
        frame.setMaximumHeight(80)
        
        layout = QHBoxLayout(frame)
        layout.setContentsMargins(15, 10, 15, 10)
        layout.setSpacing(10)
        
        # Title label
        self.WalletTabMainCurrentWalletAddressTitle = QLabel("Current wallet address:")
        self.WalletTabMainCurrentWalletAddressTitle.setObjectName("WalletTabMainCurrentWalletAddressTitle")
        font = QFont()
        font.setBold(True)
        self.WalletTabMainCurrentWalletAddressTitle.setFont(font)
        layout.addWidget(self.WalletTabMainCurrentWalletAddressTitle)
        
        # Address status label (expands to fill space)
        self.WalletTabMainCurrentAddressStatusLabel = QLabel()
        self.WalletTabMainCurrentAddressStatusLabel.setObjectName("WalletTabMainCurrentAddressStatusLabel")
        self.WalletTabMainCurrentAddressStatusLabel.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        layout.addWidget(self.WalletTabMainCurrentAddressStatusLabel)
        
        # QR Code icon
        self.WalletTabMainCurrentWalletAddressQRCodeIcon = QLabel()
        self.WalletTabMainCurrentWalletAddressQRCodeIcon.setObjectName("WalletTabMainCurrentWalletAddressQRCodeIcon")
        self.WalletTabMainCurrentWalletAddressQRCodeIcon.setPixmap(QPixmap(":/images/images/QRIcon.png"))
        self.WalletTabMainCurrentWalletAddressQRCodeIcon.setScaledContents(True)
        self.WalletTabMainCurrentWalletAddressQRCodeIcon.setFixedSize(21, 21)
        layout.addWidget(self.WalletTabMainCurrentWalletAddressQRCodeIcon)
        
        return frame
    
    def _create_wallet_controls_section(self):
        """Create wallet loading/creation controls section"""
        frame = QFrame()
        frame.setObjectName("WalletTabMainFrameTwo")
        frame.setFrameShape(QFrame.Shape.StyledPanel)
        frame.setFrameShadow(QFrame.Shadow.Raised)
        frame.setMinimumHeight(90)
        
        layout = QGridLayout(frame)
        layout.setContentsMargins(15, 10, 15, 10)
        layout.setSpacing(10)
        
        # Set column stretch factors: 39%, 1% space, 33%, 1% space, 26%
        layout.setColumnStretch(0, 39)  # Input fields column
        layout.setColumnStretch(1, 1)   # Spacer
        layout.setColumnStretch(2, 33)  # Buttons column
        layout.setColumnStretch(3, 1)   # Spacer
        layout.setColumnStretch(4, 26)  # Info text column
        
        # ROW 0 - LEFT COLUMN (col 0): Wallet file input
        self.WalletTabMainSelectWalletInputText = QLineEdit()
        self.WalletTabMainSelectWalletInputText.setObjectName("WalletTabMainSelectWalletInputText")
        self.WalletTabMainSelectWalletInputText.setMinimumWidth(200)
        layout.addWidget(self.WalletTabMainSelectWalletInputText, 0, 0, 1, 1)
        
        # ROW 0 - MIDDLE COLUMN (col 2): Browse and Export buttons
        buttons_row_0 = QHBoxLayout()
        buttons_row_0.setSpacing(10)
        
        self.WalletTabMainSelectWalletBrowseButton = QPushButton("Browse")
        self.WalletTabMainSelectWalletBrowseButton.setObjectName("WalletTabMainSelectWalletBrowseButton")
        self.WalletTabMainSelectWalletBrowseButton.setMaximumWidth(80)
        buttons_row_0.addWidget(self.WalletTabMainSelectWalletBrowseButton)
        
        self.WalletTabMainSelectWalletExportButton = QPushButton("Export Wallet")
        self.WalletTabMainSelectWalletExportButton.setObjectName("WalletTabMainSelectWalletExportButton")
        self.WalletTabMainSelectWalletExportButton.setMaximumWidth(120)
        buttons_row_0.addWidget(self.WalletTabMainSelectWalletExportButton)
        
        buttons_row_0.addStretch()
        layout.addLayout(buttons_row_0, 0, 2, 1, 1)
        
        # ROW 1 - LEFT COLUMN (col 0): Password label and input
        password_container = QHBoxLayout()
        password_container.setSpacing(10)
        
        font = QFont()
        font.setBold(True)
        
        self.WalletTabMainWalletPasswordTitle = QLabel("Wallet Password")
        self.WalletTabMainWalletPasswordTitle.setObjectName("WalletTabMainWalletPasswordTitle")
        self.WalletTabMainWalletPasswordTitle.setFont(font)
        self.WalletTabMainWalletPasswordTitle.setMaximumWidth(130)
        password_container.addWidget(self.WalletTabMainWalletPasswordTitle)
        
        self.WalletTabMainWalletPasswordUnlockInput = QLineEdit()
        self.WalletTabMainWalletPasswordUnlockInput.setObjectName("WalletTabMainWalletPasswordUnlockInput")
        self.WalletTabMainWalletPasswordUnlockInput.setEchoMode(QLineEdit.EchoMode.Password)
        self.WalletTabMainWalletPasswordUnlockInput.setMinimumWidth(150)
        password_container.addWidget(self.WalletTabMainWalletPasswordUnlockInput)
        
        layout.addLayout(password_container, 1, 0, 1, 1)
        
        # ROW 1 - MIDDLE COLUMN (col 2): Load, Create, Import buttons
        buttons_row_1 = QHBoxLayout()
        buttons_row_1.setSpacing(10)
        
        self.WalletTabMainEnterWalletPasswordLoadButton = QPushButton("Load Wallet")
        self.WalletTabMainEnterWalletPasswordLoadButton.setObjectName("WalletTabMainEnterWalletPasswordLoadButton")
        self.WalletTabMainEnterWalletPasswordLoadButton.setMaximumWidth(100)
        buttons_row_1.addWidget(self.WalletTabMainEnterWalletPasswordLoadButton)
        
        self.WalletTabMainEnterWalletPasswordCreateButton = QPushButton("Create Wallet")
        self.WalletTabMainEnterWalletPasswordCreateButton.setObjectName("WalletTabMainEnterWalletPasswordCreateButton")
        self.WalletTabMainEnterWalletPasswordCreateButton.setMaximumWidth(100)
        buttons_row_1.addWidget(self.WalletTabMainEnterWalletPasswordCreateButton)
        
        self.WalletTabMainSelectWalletImportButton = QPushButton("Import Wallet")
        self.WalletTabMainSelectWalletImportButton.setObjectName("WalletTabMainSelectWalletImportButton")
        self.WalletTabMainSelectWalletImportButton.setMaximumWidth(110)
        buttons_row_1.addWidget(self.WalletTabMainSelectWalletImportButton)
        
        buttons_row_1.addStretch()
        layout.addLayout(buttons_row_1, 1, 2, 1, 1)
        
        # RIGHT COLUMN (col 4): Information text spanning both rows
        self.WalletTabMainLoadCreateWalletText = QLabel()
        self.WalletTabMainLoadCreateWalletText.setObjectName("WalletTabMainLoadCreateWalletText")
        self.WalletTabMainLoadCreateWalletText.setWordWrap(True)
        self.WalletTabMainLoadCreateWalletText.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)
        layout.addWidget(self.WalletTabMainLoadCreateWalletText, 0, 4, 2, 1)
        
        return frame
    
    def _create_balances_withdraw_section(self):
        """Create wallet balances and withdraw section"""
        frame = QFrame()
        frame.setObjectName("WalletTabMainFrameThree")
        frame.setFrameShape(QFrame.Shape.StyledPanel)
        frame.setFrameShadow(QFrame.Shadow.Raised)
        frame.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        
        layout = QHBoxLayout(frame)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(20)
        
        # Left side: Wallet Balances
        left_layout = QVBoxLayout()
        left_layout.setSpacing(10)
        
        font = QFont()
        font.setBold(True)
        
        self.WalletTabMainWalletBalancesTitle = QLabel("Wallet Balances")
        self.WalletTabMainWalletBalancesTitle.setObjectName("WalletTabMainWalletBalancesTitle")
        self.WalletTabMainWalletBalancesTitle.setFont(font)
        left_layout.addWidget(self.WalletTabMainWalletBalancesTitle)
        
        self.WalletTabMainWalletBalancesScrollArea = QScrollArea()
        self.WalletTabMainWalletBalancesScrollArea.setObjectName("WalletTabMainWalletBalancesScrollArea")
        self.WalletTabMainWalletBalancesScrollArea.setWidgetResizable(True)
        self.WalletTabMainWalletBalancesScrollArea.setMinimumWidth(350)
        self.WalletTabMainWalletBalancesScrollArea.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        
        self.scrollAreaWidgetContents_2 = QWidget()
        self.scrollAreaWidgetContents_2.setObjectName("scrollAreaWidgetContents_2")
        self.WalletTabMainWalletBalancesScrollArea.setWidget(self.scrollAreaWidgetContents_2)
        
        # Create layout for scroll area content
        self.WalletTabMainWalletBalancesScrollAreaLayout = QVBoxLayout(self.scrollAreaWidgetContents_2)
        self.WalletTabMainWalletBalancesScrollAreaLayout.setSpacing(0)
        self.WalletTabMainWalletBalancesScrollAreaLayout.setContentsMargins(0, 0, 0, 0)
        
        left_layout.addWidget(self.WalletTabMainWalletBalancesScrollArea)
        layout.addLayout(left_layout, stretch=1)
        
        # Right side: Withdraw Section
        right_layout = QVBoxLayout()
        right_layout.setSpacing(10)
        
        self.WalletTabMainWithdrawAddressTitle = QLabel("Withdraw Address")
        self.WalletTabMainWithdrawAddressTitle.setObjectName("WalletTabMainWithdrawAddressTitle")
        self.WalletTabMainWithdrawAddressTitle.setFont(font)
        right_layout.addWidget(self.WalletTabMainWithdrawAddressTitle)
        
        self.WalletTabMainWithdrawAddressTextInput = QTextEdit()
        self.WalletTabMainWithdrawAddressTextInput.setObjectName("WalletTabMainWithdrawAddressTextInput")
        self.WalletTabMainWithdrawAddressTextInput.setMaximumHeight(70)
        right_layout.addWidget(self.WalletTabMainWithdrawAddressTextInput)
        
        self.WalletTabMainWithdrawText = QLabel()
        self.WalletTabMainWithdrawText.setObjectName("WalletTabMainWithdrawText")
        self.WalletTabMainWithdrawText.setWordWrap(True)
        self.WalletTabMainWithdrawText.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)
        right_layout.addWidget(self.WalletTabMainWithdrawText)
        
        right_layout.addStretch()
        
        # Password input
        password_layout = QVBoxLayout()
        password_layout.setSpacing(5)
        
        self.WalletTabMainWithdrawPasswordTitle = QLabel("Wallet Password")
        self.WalletTabMainWithdrawPasswordTitle.setObjectName("WalletTabMainWithdrawPasswordTitle")
        self.WalletTabMainWithdrawPasswordTitle.setFont(font)
        password_layout.addWidget(self.WalletTabMainWithdrawPasswordTitle)
        
        self.WalletTabMainWalletPasswordWithdrawInput = QLineEdit()
        self.WalletTabMainWalletPasswordWithdrawInput.setObjectName("WalletTabMainWalletPasswordWithdrawInput")
        self.WalletTabMainWalletPasswordWithdrawInput.setEchoMode(QLineEdit.EchoMode.Password)
        self.WalletTabMainWalletPasswordWithdrawInput.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        password_layout.addWidget(self.WalletTabMainWalletPasswordWithdrawInput)
        
        right_layout.addLayout(password_layout)
        
        # Withdraw button (right-aligned)
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        self.WalletTabMainWithdrawButton = QPushButton("Withdraw")
        self.WalletTabMainWithdrawButton.setObjectName("WalletTabMainWithdrawButton")
        self.WalletTabMainWithdrawButton.setMinimumSize(110, 30)
        button_layout.addWidget(self.WalletTabMainWithdrawButton)
        
        right_layout.addLayout(button_layout)
        layout.addLayout(right_layout, stretch=1)
        
        return frame
    
    def setupUi_legacy(self, WalletTabMain):
        """Legacy setGeometry-based UI setup"""
        WalletTabMain.setObjectName("WalletTabMain")
        sizePolicy = QSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        
        # Create scroll area layout
        self.WalletTabMainWalletBalancesScrollAreaLayout = QVBoxLayout(WalletTabMain)
        self.WalletTabMainWalletBalancesScrollAreaLayout.setSpacing(0)
        self.WalletTabMainWalletBalancesScrollAreaLayout.setContentsMargins(0, 0, 0, 0)
        
        self.WalletTabMainSelectWalletBrowseButton = QPushButton(WalletTabMain)
        self.WalletTabMainSelectWalletBrowseButton.setObjectName("WalletTabMainSelectWalletBrowseButton")
        self.WalletTabMainSelectWalletBrowseButton.setGeometry(QRect(250, 90, 75, 24))
        
        self.WalletTabMainSelectWalletInputText = QLineEdit(WalletTabMain)
        self.WalletTabMainSelectWalletInputText.setObjectName("WalletTabMainSelectWalletInputText")
        self.WalletTabMainSelectWalletInputText.setGeometry(QRect(30, 90, 211, 21))
        
        self.WalletTabMainWalletPasswordUnlockInput = QLineEdit(WalletTabMain)
        self.WalletTabMainWalletPasswordUnlockInput.setObjectName("WalletTabMainWalletPasswordUnlockInput")
        self.WalletTabMainWalletPasswordUnlockInput.setGeometry(QRect(30, 140, 211, 22))
        self.WalletTabMainWalletPasswordUnlockInput.setEchoMode(QLineEdit.EchoMode.Password)
        
        self.WalletTabMainEnterWalletPasswordLoadButton = QPushButton(WalletTabMain)
        self.WalletTabMainEnterWalletPasswordLoadButton.setObjectName("WalletTabMainEnterWalletPasswordLoadButton")
        self.WalletTabMainEnterWalletPasswordLoadButton.setGeometry(QRect(250, 140, 75, 24))
        
        self.WalletTabMainEnterWalletPasswordCreateButton = QPushButton(WalletTabMain)
        self.WalletTabMainEnterWalletPasswordCreateButton.setObjectName("WalletTabMainEnterWalletPasswordCreateButton")
        self.WalletTabMainEnterWalletPasswordCreateButton.setGeometry(QRect(363, 140, 81, 24))
        
        self.WalletTabMainCurrentWalletAddressTitle = QLabel(WalletTabMain)
        self.WalletTabMainCurrentWalletAddressTitle.setObjectName("WalletTabMainCurrentWalletAddressTitle")
        self.WalletTabMainCurrentWalletAddressTitle.setGeometry(QRect(30, 30, 131, 16))
        font = QFont()
        font.setBold(True)     
        self.WalletTabMainCurrentWalletAddressTitle.setFont(font)
        
        self.WalletTabMainCurrentAddressStatusLabel = QLabel(WalletTabMain)
        self.WalletTabMainCurrentAddressStatusLabel.setObjectName("WalletTabMainCurrentAddressStatusLabel")
        self.WalletTabMainCurrentAddressStatusLabel.setGeometry(QRect(170, 30, 541, 16))
        
        self.WalletTabMainSelectWalletExportButton = QPushButton(WalletTabMain)
        self.WalletTabMainSelectWalletExportButton.setObjectName("WalletTabMainSelectWalletExportButton")
        self.WalletTabMainSelectWalletExportButton.setGeometry(QRect(363, 90, 81, 24))
        
        self.WalletTabMainLoadCreateWalletText = QLabel(WalletTabMain)
        self.WalletTabMainLoadCreateWalletText.setObjectName("WalletTabMainLoadCreateWalletText")
        self.WalletTabMainLoadCreateWalletText.setGeometry(QRect(460, 117, 311, 51))
        self.WalletTabMainLoadCreateWalletText.setWordWrap(True)
        
        #self.WalletTabMainSelectWalletText = QLabel(WalletTabMain)
        #self.WalletTabMainSelectWalletText.setObjectName("WalletTabMainSelectWalletText")
        #self.WalletTabMainSelectWalletText.setGeometry(QRect(460, 85, 311, 31))
        #self.WalletTabMainSelectWalletText.setWordWrap(True)
        
        self.WalletTabMainWalletBalancesScrollArea = QScrollArea(WalletTabMain)
        self.WalletTabMainWalletBalancesScrollArea.setObjectName("WalletTabMainWalletBalancesScrollArea")
        self.WalletTabMainWalletBalancesScrollArea.setGeometry(QRect(30, 220, 391, 291))
        self.WalletTabMainWalletBalancesScrollArea.setWidgetResizable(True)
        
        self.scrollAreaWidgetContents_2 = QWidget()
        self.scrollAreaWidgetContents_2.setObjectName("scrollAreaWidgetContents_2")
        self.scrollAreaWidgetContents_2.setGeometry(QRect(0, 0, 389, 289))
        self.WalletTabMainWalletBalancesScrollArea.setWidget(self.scrollAreaWidgetContents_2)
        
        self.WalletTabMainFrameThree = QFrame(WalletTabMain)
        self.WalletTabMainFrameThree.setObjectName("WalletTabMainFrameThree")
        self.WalletTabMainFrameThree.setGeometry(QRect(13, 180, 771, 341))
        self.WalletTabMainFrameThree.setFrameShape(QFrame.Shape.StyledPanel)
        self.WalletTabMainFrameThree.setFrameShadow(QFrame.Shadow.Raised)
        
        self.WalletTabMainWithdrawButton = QPushButton(self.WalletTabMainFrameThree)
        self.WalletTabMainWithdrawButton.setObjectName("WalletTabMainWithdrawButton")
        self.WalletTabMainWithdrawButton.setGeometry(QRect(640, 300, 111, 31))
        
        self.WalletTabMainWithdrawText = QLabel(self.WalletTabMainFrameThree)
        self.WalletTabMainWithdrawText.setObjectName("WalletTabMainWithdrawText")
        self.WalletTabMainWithdrawText.setGeometry(QRect(450, 100, 301, 141))
        self.WalletTabMainWithdrawText.setWordWrap(True)
        
        self.WalletTabMainWithdrawPasswordTitle = QLabel(self.WalletTabMainFrameThree)
        self.WalletTabMainWithdrawPasswordTitle.setObjectName("WalletTabMainWithdrawPasswordTitle")
        self.WalletTabMainWithdrawPasswordTitle.setGeometry(QRect(450, 243, 101, 16))
        self.WalletTabMainWithdrawPasswordTitle.setFont(font)
        
        self.WalletTabMainWalletPasswordWithdrawInput = QLineEdit(self.WalletTabMainFrameThree)
        self.WalletTabMainWalletPasswordWithdrawInput.setObjectName("WalletTabMainWalletPasswordWithdrawInput")
        self.WalletTabMainWalletPasswordWithdrawInput.setGeometry(QRect(450, 270, 301, 22))
        sizePolicy.setHeightForWidth(self.WalletTabMainWalletPasswordWithdrawInput.sizePolicy().hasHeightForWidth())
        self.WalletTabMainWalletPasswordWithdrawInput.setSizePolicy(sizePolicy)
        self.WalletTabMainWalletPasswordWithdrawInput.setEchoMode(QLineEdit.EchoMode.Password)
        
        self.WalletTabMainWithdrawAddressTextInput = QTextEdit(self.WalletTabMainFrameThree)
        self.WalletTabMainWithdrawAddressTextInput.setObjectName("WalletTabMainWithdrawAddressTextInput")
        self.WalletTabMainWithdrawAddressTextInput.setGeometry(QRect(450, 40, 301, 61))
        
        self.WalletTabMainFrameTwo = QFrame(WalletTabMain)
        self.WalletTabMainFrameTwo.setObjectName("WalletTabMainFrameTwo")
        self.WalletTabMainFrameTwo.setGeometry(QRect(13, 80, 771, 91))
        self.WalletTabMainFrameTwo.setFrameShape(QFrame.Shape.StyledPanel)
        self.WalletTabMainFrameTwo.setFrameShadow(QFrame.Shadow.Raised)
        
        self.WalletTabMainWalletPasswordTitle = QLabel(self.WalletTabMainFrameTwo)
        self.WalletTabMainWalletPasswordTitle.setObjectName("WalletTabMainWalletPasswordTitle")
        self.WalletTabMainWalletPasswordTitle.setGeometry(QRect(20, 40, 131, 16))
        self.WalletTabMainWalletPasswordTitle.setFont(font)
        
        self.WalletTabMainSelectWalletImportButton = QPushButton(self.WalletTabMainFrameTwo)
        self.WalletTabMainSelectWalletImportButton.setObjectName("WalletTabMainSelectWalletImportButton")
        self.WalletTabMainSelectWalletImportButton.setGeometry(QRect(350, 35, 81, 24))
        
        self.WalletTabMainFrameOne = QFrame(WalletTabMain)
        self.WalletTabMainFrameOne.setObjectName("WalletTabMainFrameOne")
        self.WalletTabMainFrameOne.setGeometry(QRect(13, 10, 771, 61))
        self.WalletTabMainFrameOne.setFrameShape(QFrame.Shape.StyledPanel)
        self.WalletTabMainFrameOne.setFrameShadow(QFrame.Shadow.Raised)
        
        self.WalletTabMainCurrentWalletAddressQRCodeIcon = QLabel(self.WalletTabMainFrameOne)
        self.WalletTabMainCurrentWalletAddressQRCodeIcon.setObjectName("WalletTabMainCurrentWalletAddressQRCodeIcon")
        self.WalletTabMainCurrentWalletAddressQRCodeIcon.setGeometry(QRect(740, 10, 21, 21))
        self.WalletTabMainCurrentWalletAddressQRCodeIcon.setPixmap(QPixmap(":/images/images/QRIcon.png"))
        self.WalletTabMainCurrentWalletAddressQRCodeIcon.setScaledContents(True)
        
        # Add back the title labels
        self.WalletTabMainWalletBalancesTitle = QLabel(WalletTabMain)
        self.WalletTabMainWalletBalancesTitle.setObjectName("WalletTabMainWalletBalancesTitle")
        self.WalletTabMainWalletBalancesTitle.setGeometry(QRect(30, 200, 91, 16))
        self.WalletTabMainWalletBalancesTitle.setFont(font)
        
        self.WalletTabMainWithdrawAddressTitle = QLabel(WalletTabMain)
        self.WalletTabMainWithdrawAddressTitle.setObjectName("WalletTabMainWithdrawAddressTitle")
        self.WalletTabMainWithdrawAddressTitle.setGeometry(QRect(460, 200, 101, 16))
        self.WalletTabMainWithdrawAddressTitle.setFont(font)
        
        # Raise order
        self.WalletTabMainFrameThree.raise_()
        self.WalletTabMainFrameOne.raise_()
        self.WalletTabMainFrameTwo.raise_()
        self.WalletTabMainSelectWalletBrowseButton.raise_()
        self.WalletTabMainSelectWalletInputText.raise_()
        self.WalletTabMainWalletPasswordUnlockInput.raise_()
        self.WalletTabMainEnterWalletPasswordLoadButton.raise_()
        self.WalletTabMainEnterWalletPasswordCreateButton.raise_()
        self.WalletTabMainCurrentWalletAddressTitle.raise_()
        self.WalletTabMainCurrentAddressStatusLabel.raise_()
        self.WalletTabMainSelectWalletExportButton.raise_()
        self.WalletTabMainLoadCreateWalletText.raise_()
        #self.WalletTabMainSelectWalletText.raise_()
        self.WalletTabMainWalletBalancesScrollArea.raise_()
        self.WalletTabMainWalletBalancesTitle.raise_()
        self.WalletTabMainWithdrawAddressTitle.raise_()
        self.WalletTabMainWalletBalancesTitle.raise_()
        self.WalletTabMainWithdrawAddressTitle.raise_()
    
    def retranslateUi(self, WalletTabMain):
        """Set all UI text/translations"""
        _translate = QCoreApplication.translate
        
        self.WalletTabMainSelectWalletBrowseButton.setText(_translate("WalletTabMain", "Browse"))
        self.WalletTabMainSelectWalletInputText.setText(_translate("WalletTabMain", "Select wallet file..."))
        self.WalletTabMainWalletPasswordUnlockInput.setText("")
        self.WalletTabMainEnterWalletPasswordLoadButton.setText(_translate("WalletTabMain", "Load Wallet"))
        self.WalletTabMainEnterWalletPasswordCreateButton.setText(_translate("WalletTabMain", "Create Wallet"))
        self.WalletTabMainCurrentWalletAddressTitle.setText(_translate("WalletTabMain", "Current wallet address:"))
        self.WalletTabMainCurrentAddressStatusLabel.setText(_translate("WalletTabMain", "Not found. Create or load one below."))
        self.WalletTabMainSelectWalletExportButton.setText(_translate("WalletTabMain", "Export Wallet"))
        self.WalletTabMainLoadCreateWalletText.setText(_translate("WalletTabMain", "<html><head/><body><p>Loading, creating, importing and exporting a wallet requires a password. Keep your password safe.</p></body></html>"))
        #self.WalletTabMainSelectWalletText.setText(_translate("WalletTabMain", ""))
        self.WalletTabMainWalletBalancesTitle.setText(_translate("WalletTabMain", "Wallet Balances"))
        self.WalletTabMainWithdrawAddressTitle.setText(_translate("WalletTabMain", "Withdraw Address"))
        self.WalletTabMainWithdrawButton.setText(_translate("WalletTabMain", "Withdraw"))
        self.WalletTabMainWithdrawText.setText(_translate("WalletTabMain", "<html><head/><body><p>The wallet balances to the left of this dialog each have a field for you to set how many of each token you would like to withdraw to the wallet address stated above. Just set how many of each token you would like to withdraw, enter the wallet password below and hit the Withdraw button. Multiple tokens can be withdrawn in a single transaction.</p></body></html>"))
        self.WalletTabMainWithdrawPasswordTitle.setText(_translate("WalletTabMain", "Wallet Password"))
        self.WalletTabMainWalletPasswordTitle.setText(_translate("WalletTabMain", "Wallet Password"))
        self.WalletTabMainSelectWalletImportButton.setText(_translate("WalletTabMain", "Import Wallet"))
        self.WalletTabMainCurrentWalletAddressQRCodeIcon.setText("")
