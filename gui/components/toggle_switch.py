from PySide6.QtCore import Qt, Signal, Property, QPropertyAnimation, QRect, QEasingCurve
from PySide6.QtWidgets import QWidget, QHBoxLayout, QLabel
from PySide6.QtGui import QPainter, QColor, QBrush, QPen, QFont

class ToggleSwitch(QWidget):
    """Modern toggle switch widget for binary selection."""
    toggled = Signal(bool)
    
    def __init__(self, left_text="Option 1", right_text="Option 2", parent=None):
        super().__init__(parent)
        self.left_text = left_text
        self.right_text = right_text
        self._checked = False
        
        # Initialize switch position BEFORE creating the animation
        self._switch_position = 0
        
        # Set fixed size for the switch
        self.setFixedHeight(20)
        self.setMinimumWidth(112)
        
        # Animation for smooth transitions (must be created AFTER _switch_position is initialized)
        self.animation = QPropertyAnimation(self, b"switch_position", self)
        self.animation.setEasingCurve(QEasingCurve.InOutCubic)
        self.animation.setDuration(200)
        
    @Property(int)
    def switch_position(self):
        return self._switch_position
    
    @switch_position.setter
    def switch_position(self, value):
        self._switch_position = value
        self.update()
    
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # Colors
        bg_color = QColor(10, 14, 39)  # Dark background
        active_color = QColor(0, 120, 215)  # Blue accent
        text_color = QColor(255, 255, 255)
        inactive_text_color = QColor(150, 150, 150)
        
        # Draw background
        painter.setBrush(QBrush(bg_color))
        painter.setPen(Qt.NoPen)
        painter.drawRoundedRect(0, 0, self.width(), self.height(), 16, 16)
        
        # Calculate switch position
        switch_width = self.width() // 2
        switch_x = self._switch_position
        
        # Draw active switch background
        painter.setBrush(QBrush(active_color))
        painter.drawRoundedRect(switch_x, 2, switch_width - 4, self.height() - 4, 14, 14)
        
        # Draw text
        painter.setPen(QPen(text_color if not self._checked else inactive_text_color))
        font = QFont()
        font.setPointSize(8)
        font.setBold(True)
        painter.setFont(font)
        
        # Left text
        left_rect = QRect(0, 0, switch_width, self.height())
        painter.setPen(QPen(text_color if not self._checked else inactive_text_color))
        painter.drawText(left_rect, Qt.AlignCenter, self.left_text)
        
        # Right text
        right_rect = QRect(switch_width, 0, switch_width, self.height())
        painter.setPen(QPen(text_color if self._checked else inactive_text_color))
        painter.drawText(right_rect, Qt.AlignCenter, self.right_text)
    
    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.setChecked(not self._checked)
    
    def setChecked(self, checked):
        self._checked = checked
        
        # Animate the switch
        self.animation.setStartValue(self._switch_position)
        if checked:
            self.animation.setEndValue(self.width() // 2 + 2)
        else:
            self.animation.setEndValue(2)
        
        self.animation.start()
        self.toggled.emit(checked)
    
    def isChecked(self):
        return self._checked
    
    def setLeftText(self, text):
        self.left_text = text
        self.update()
    
    def setRightText(self, text):
        self.right_text = text
        self.update()
    
    def isFirstTokenSelected(self):
        """Returns True if the first (left) option is selected. Compatible with TokenSelector API."""
        return not self._checked
    
    def isSecondTokenSelected(self):
        """Returns True if the second (right) option is selected. Compatible with TokenSelector API."""
        return self._checked
    
    def setTokens(self, token1, token2):
        """Set the token names for the toggle switch. Compatible with TokenSelector API."""
        self.setLeftText(token1)
        self.setRightText(token2)
    
    def setSelection(self, select_second):
        """Set which option is selected. True for second option, False for first. Compatible with TokenSelector API."""
        self.setChecked(select_second)


class TokenSelector(QWidget):
    """Widget containing label and toggle switch for token selection."""
    selectionChanged = Signal(bool)  # True for right option, False for left
    
    def __init__(self, label_text="Select Token:", parent=None):
        super().__init__(parent)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Label (hide if empty)
        self.label = QLabel(label_text)
        if label_text:  # Only show label if text is provided
            self.label.setMinimumWidth(100)
            layout.addWidget(self.label)
        else:
            self.label.setVisible(False)
        
        # Toggle switch
        self.toggle = ToggleSwitch("Token 1", "Token 2")
        self.toggle.toggled.connect(self.selectionChanged.emit)
        layout.addWidget(self.toggle)
        
        # layout.addStretch()
    
    def setTokens(self, token1, token2):
        """Set the token names for the toggle switch."""
        self.toggle.setLeftText(token1)
        self.toggle.setRightText(token2)
    
    def isFirstTokenSelected(self):
        """Returns True if the first (left) token is selected."""
        return not self.toggle.isChecked()
    
    def isSecondTokenSelected(self):
        """Returns True if the second (right) token is selected."""
        return self.toggle.isChecked()
    
    def setSelection(self, select_second):
        """Set which token is selected. True for second token, False for first."""
        self.toggle.setChecked(select_second)
