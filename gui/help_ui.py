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
    QTextBrowser, QTextEdit, QTreeView, QVBoxLayout, QWidget, QHBoxLayout, QSpacerItem)
from gui import resources_rc

# Toggle between layout-based (True) and legacy setGeometry (False)
USE_RESPONSIVE_LAYOUTS = True

class Ui_HelpTabMain(object):   
    def setupUi(self, HelpTabMain):
        if USE_RESPONSIVE_LAYOUTS:
            self.setupUi_layouts(HelpTabMain)
        else:
            self.setupUi_legacy(HelpTabMain)
    
    def setupUi_layouts(self, HelpTabMain):
        """Layout-based responsive UI setup"""
        HelpTabMain.setObjectName(u"HelpTabMain")
        
        # Main horizontal layout: [Left Navigation Panel | Right Content Area]
        main_layout = QHBoxLayout(HelpTabMain)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(15)
        
        # LEFT PANEL: Navigation + Branding
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(10)
        
        # Documentation Title
        self.HelpTabMainDocumentationTitle = QLabel("Documentation")
        self.HelpTabMainDocumentationTitle.setObjectName(u"HelpTabMainDocumentationTitle")
        self.HelpTabMainDocumentationTitle.setStyleSheet("font-weight: bold; font-size: 14px;")
        left_layout.addWidget(self.HelpTabMainDocumentationTitle)
        
        # Navigation Tree - expands to fill available space
        self.HelpTabMainDocumentationTreeView = QTreeView()
        self.HelpTabMainDocumentationTreeView.setHeaderHidden(True)
        self.HelpTabMainDocumentationTreeView.setObjectName(u"HelpTabMainDocumentationTreeView")
        self.HelpTabMainDocumentationTreeView.setAutoFillBackground(False)
        self.HelpTabMainDocumentationTreeView.setMinimumWidth(180)
        self.HelpTabMainDocumentationTreeView.setMaximumWidth(250)
        self.HelpTabMainDocumentationTreeView.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Expanding)
        left_layout.addWidget(self.HelpTabMainDocumentationTreeView, stretch=1)  # Give it stretch
        
        # Spacer to push branding to bottom
        left_layout.addItem(QSpacerItem(0, 0, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding))
        
        # Akond Logo
        self.HelpTabMainAkondImage = QLabel()
        self.HelpTabMainAkondImage.setObjectName(u"HelpTabMainAkondImage")
        self.HelpTabMainAkondImage.setPixmap(QPixmap(u":/images/images/AkondLogoName-45.png"))
        self.HelpTabMainAkondImage.setScaledContents(True)
        self.HelpTabMainAkondImage.setMaximumHeight(34)
        self.HelpTabMainAkondImage.setAlignment(Qt.AlignmentFlag.AlignCenter)
        left_layout.addWidget(self.HelpTabMainAkondImage)
        
        # Akond Text
        self.HelpTabMainAkondText = QLabel()
        self.HelpTabMainAkondText.setObjectName(u"HelpTabMainAkondText")
        self.HelpTabMainAkondText.setWordWrap(True)
        self.HelpTabMainAkondText.setStyleSheet("font-size: 12px;")
        self.HelpTabMainAkondText.setMaximumHeight(180)
        left_layout.addWidget(self.HelpTabMainAkondText)
        
        # Add left panel to main layout (fixed width)
        left_panel.setMaximumWidth(250)
        main_layout.addWidget(left_panel)
        
        # RIGHT PANEL: Content Browser (QTextBrowser supports rich HTML)
        self.content_label = QTextBrowser()
        self.content_label.setObjectName(u"HelpTabMainContentBrowser")
        self.content_label.setOpenExternalLinks(True)
        self.content_label.setStyleSheet("""
            QTextBrowser {
                background-color: #0a0e27;
                color: #d4d4d4;
                border: 1px solid #1e293b;
                border-radius: 6px;
                padding: 12px;
                font-size: 12px;
            }
        """)
        self.content_label.setHtml("<p>Welcome to RadBot! Please select a section from the navigation tree to view its documentation.</p>")
        
        # Add browser to main layout (expands to fill)
        main_layout.addWidget(self.content_label, stretch=1)
        
        # Call retranslateUi
        self.retranslateUi(HelpTabMain)
    
    def setupUi_legacy(self, HelpTabMain):
        """Legacy setGeometry-based UI setup"""  
        HelpTabMain.setObjectName(u"HelpTabMain")
        self.content_label = QTextBrowser(HelpTabMain)
        self.content_label.setObjectName(u"HelpTabMainContentBrowser")
        self.content_label.setGeometry(QRect(215, 20, 571, 501))
        self.content_label.setOpenExternalLinks(True)
        self.content_label.setStyleSheet("""
            QTextBrowser {
                background-color: #0a0e27;
                color: #d4d4d4;
                border: 1px solid #1e293b;
                border-radius: 6px;
                padding: 12px;
                font-size: 12px;
            }
        """)
        self.content_label.setHtml("<p>Welcome to RadBot! Please select a section from the navigation tree to view its documentation.</p>")
        
        # Navigation Tree
        self.HelpTabMainDocumentationTreeView = QTreeView(HelpTabMain)
        self.HelpTabMainDocumentationTreeView.setHeaderHidden(True)
        self.HelpTabMainDocumentationTreeView.setObjectName(u"HelpTabMainDocumentationTreeView")
        self.HelpTabMainDocumentationTreeView.setGeometry(QRect(10, 20, 191, 271))
        self.HelpTabMainDocumentationTreeView.setAutoFillBackground(False)
        
        # Title and Branding
        self.HelpTabMainDocumentationTitle = QLabel(HelpTabMain)
        self.HelpTabMainDocumentationTitle.setObjectName(u"HelpTabMainDocumentationTitle")
        self.HelpTabMainDocumentationTitle.setGeometry(QRect(13, 5, 121, 16))
        self.HelpTabMainDocumentationTitle.setStyleSheet("font-weight: bold; font-size: 14px;")
        # self.HelpTabMainDocumentationTitle.setText("Documentation")
        
        self.HelpTabMainAkondImage = QLabel(HelpTabMain)
        self.HelpTabMainAkondImage.setObjectName(u"HelpTabMainAkondImage")
        self.HelpTabMainAkondImage.setGeometry(QRect(30, 300, 151, 34))
        self.HelpTabMainAkondImage.setPixmap(QPixmap(u":/images/images/AkondLogoName-45.png"))
        self.HelpTabMainAkondImage.setScaledContents(True)
        
        self.HelpTabMainAkondText = QLabel(HelpTabMain)
        self.HelpTabMainAkondText.setObjectName(u"HelpTabMainAkondText")
        self.HelpTabMainAkondText.setGeometry(QRect(15, 340, 181, 181))
        self.HelpTabMainAkondText.setWordWrap(True)
        self.HelpTabMainAkondText.setTextFormat(Qt.RichText)
        self.HelpTabMainAkondText.setTextInteractionFlags(Qt.TextBrowserInteraction)
        self.HelpTabMainAkondText.setStyleSheet("font-size: 12px;")
        self.HelpTabMainAkondText.setText("For more information and support, visit our website and join our community.")
        
    
    def update_content(self, content):
        """Update the content area with new content"""
        self.content_label.setHtml(content)
    
    def retranslateUi(self, HelpTabMain):
        self.HelpTabMainDocumentationTitle.setText(QCoreApplication.translate("HelpTabMain", u"Documentation", None))
        self.HelpTabMainAkondImage.setText("")
        self.HelpTabMainAkondText.setText(QCoreApplication.translate("HelpTabMain", u"<html><head/><body><p>RadBot is brought to you by Akond Ltd.<br/><br/>A small fee is added to every trade to cover our time in development, maintenance, and the future improvement of this tool.</p><p>Join the Radix community to discuss RadBot.</p><p><a href='https://radixtalk.com/' style='color: #00D4FF; text-decoration: none;'>Join RadixTalk</a></p></body></html>", None))