from PySide6.QtCore import QCoreApplication, QRect, Qt
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QWidget, QTabWidget, QSizePolicy, QVBoxLayout
from version import __app_name__, __version__, __subtitle__

class Ui_AkondRadBotMainWindow(object):
    def setupUi(self, AkondRadBotMainWindow):
        AkondRadBotMainWindow.setObjectName("AkondRadBotMainWindow")
        
        # Set window icon (Qt will automatically use appropriate size for title bar)
        icon = QIcon()
        icon.addFile("images/Radbot16.png")  # For small displays
        icon.addFile("images/Radbotk32.png")  # For normal displays
        icon.addFile("images/Radbot48.png")  # For larger displays
        icon.addFile("images/Radbot64.png")  # For high DPI
        AkondRadBotMainWindow.setWindowIcon(icon)
        
        # Set starting size (same as before)
        AkondRadBotMainWindow.resize(801, 569)
        
        # Set minimum size to prevent window from being too small
        AkondRadBotMainWindow.setMinimumSize(801, 580)

        sizePolicy = QSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(AkondRadBotMainWindow.sizePolicy().hasHeightForWidth())
        AkondRadBotMainWindow.setSizePolicy(sizePolicy)

        self.centralwidget = QWidget(AkondRadBotMainWindow)
        self.centralwidget.setObjectName("centralwidget")

        # Create layout for central widget to make tab widget responsive
        central_layout = QVBoxLayout(self.centralwidget)
        central_layout.setContentsMargins(0, 0, 0, 0)
        central_layout.setSpacing(0)

        self.RadBotMainTabMenu = QTabWidget(self.centralwidget)
        self.RadBotMainTabMenu.setObjectName("RadBotMainTabMenu")
        self.RadBotMainTabMenu.setEnabled(True)
        # Removed setGeometry - now uses layout
        self.RadBotMainTabMenu.setFocusPolicy(Qt.FocusPolicy.TabFocus)
        self.RadBotMainTabMenu.setTabShape(QTabWidget.TabShape.Rounded)
        self.RadBotMainTabMenu.setTabBarAutoHide(False)
        
        # Add tab widget to layout
        central_layout.addWidget(self.RadBotMainTabMenu)

        AkondRadBotMainWindow.setCentralWidget(self.centralwidget)

    def retranslateUi(self, AkondRadBotMainWindow):
        _translate = QCoreApplication.translate
        AkondRadBotMainWindow.setWindowTitle(f"{__app_name__} - {__subtitle__} - v{__version__}")