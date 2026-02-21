from PySide6.QtWidgets import QWidget, QLabel
from PySide6.QtCore import Qt

class OverlappingIconWidget(QWidget):
    def __init__(self, icon_size=25, parent=None):
        super().__init__(parent)
        self.icon_size = icon_size
        self.setFixedSize(int(icon_size * 1.5), icon_size) # Width is 1.5x icon size, height is 1x

        self.icon1 = QLabel(self)
        self.icon1.setFixedSize(icon_size, icon_size)
        self.icon1.setScaledContents(True)

        self.icon2 = QLabel(self)
        self.icon2.setFixedSize(icon_size, icon_size)
        self.icon2.setScaledContents(True)
        self.icon2.move(int(icon_size * 0.5), 0) # Overlap by 50%

    def set_icons(self, pixmap1, pixmap2):
        self.icon1.setPixmap(pixmap1)
        self.icon2.setPixmap(pixmap2)
        # Ensure icon1 (base token) is drawn on top of icon2 (quote token)
        self.icon1.raise_()
        # Make sure both icons are visible
        self.icon1.show()
        self.icon2.show()
