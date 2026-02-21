from PySide6.QtWidgets import QFrame, QVBoxLayout, QLabel, QSizePolicy
from PySide6.QtCore import Qt, QRect
from PySide6.QtGui import QPainter, QPen, QColor, QLinearGradient, QBrush
import math

class VolumeChart(QFrame):
    """Chart showing trading volume over days"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFrameShape(QFrame.StyledPanel)
        self.setFrameShadow(QFrame.Raised)
        self.setMinimumSize(350, 200)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        # Background from theme QSS (QFrame styling)
        
        # Layout with title
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(15, 15, 15, 15)
        
        self.title = QLabel("Trading Volume - (XRD)")
        self.title.setStyleSheet("font-weight: bold; font-size: 14px;")
        self.layout.addWidget(self.title)
        
        # Add a spacer to ensure the chart area is available for painting
        self.layout.addStretch(1)
        
        # Sample volume data for last 7 days: [(day, volume), ...]
        # where day is 0-6 (Monday to Sunday) and volume is in XRD
        self.volume_data = [
            ("Mon", 150),
            ("Tue", 220),
            ("Wed", 180),
            ("Thu", 240),
            ("Fri", 300),
            ("Sat", 120),
            ("Sun", 90)
        ]
        
    def set_volume_data(self, volume_data):
        """Update with new volume data"""
        self.volume_data = volume_data
        self.update()
        
    def paintEvent(self, event):
        """Draw the volume chart"""
        super().paintEvent(event)
        
        if not self.volume_data:
            return
            
        # Create and setup painter
        painter = QPainter()
        if not painter.begin(self):
            return
            
        painter.setRenderHint(QPainter.Antialiasing)
        
        try:
            # Chart dimensions using contentsRect for proper layout handling
            content_rect = self.contentsRect()
            # Add more left padding to make room for value labels
            chart_rect = content_rect.adjusted(50, 50, -20, -20)
            
            # Find max value for scaling
            max_volume = max(volume for _, volume in self.volume_data)
            max_scale = max(max_volume * 1.1, 1)  # Add 10% headroom, prevent division by zero
            
            # Draw axes
            painter.setPen(QPen(QColor(30, 41, 59), 1))  # Theme border
            painter.drawLine(
                chart_rect.left(), chart_rect.bottom(),
                chart_rect.right(), chart_rect.bottom()
            )
            
            # Calculate bar width and spacing
            num_bars = len(self.volume_data)
            bar_width = chart_rect.width() / (num_bars * 2)  # Use half the available space
            
            # Draw volume bars
            for i, (day, volume) in enumerate(self.volume_data):
                # Calculate bar position
                bar_x = chart_rect.left() + i * (chart_rect.width() / num_bars) + (chart_rect.width() / (num_bars * 2) - bar_width / 2)
                bar_height = (volume / max_scale) * chart_rect.height()
                bar_y = chart_rect.bottom() - bar_height
                
                # Create gradient fill for bar
                gradient = QLinearGradient(0, bar_y, 0, chart_rect.bottom())
                gradient.setColorAt(0, QColor(13, 110, 253))  # Theme blue top
                gradient.setColorAt(1, QColor(0, 212, 255))  # Theme cyan bottom
                
                # Draw bar with gradient
                painter.setBrush(gradient)
                painter.setPen(Qt.NoPen)
                painter.drawRect(
                    int(bar_x), 
                    int(bar_y),
                    int(bar_width),
                    int(bar_height)
                )
                
                # Draw day label below bar
                #painter.setPen(QPen(QColor(200, 200, 200)))
                #painter.drawText(
                #    int(bar_x - 10), 
                #    int(chart_rect.bottom() + 15),
                #    int(bar_width + 20),
                #    20,
                #    Qt.AlignCenter, 
                #    day
                #)
            
            # Draw horizontal guidelines
            painter.setPen(QPen(QColor(30, 41, 59), 1, Qt.DashLine))  # Theme border
            num_guidelines = 4
            for i in range(1, num_guidelines + 1):
                y = chart_rect.bottom() - (i * chart_rect.height() / num_guidelines)
                painter.drawLine(
                    chart_rect.left(), 
                    int(y),
                    chart_rect.right(), 
                    int(y)
                )
                
                # Draw value label with proper alignment and position
                # Ensure there's enough space on the left side
                value = int(max_scale * i / num_guidelines)
                painter.setPen(QPen(QColor(148, 163, 184)))  # Theme secondary text
                text_rect = QRect(
                    int(chart_rect.left() - 45), 
                    int(y - 10),
                    40,
                    20
                )
                painter.drawText(
                    text_rect,
                    Qt.AlignRight | Qt.AlignVCenter,
                    str(value)
                )
        finally:
            painter.end()
