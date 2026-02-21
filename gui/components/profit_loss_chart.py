from PySide6.QtWidgets import QFrame, QVBoxLayout, QLabel, QSizePolicy
from PySide6.QtCore import Qt
from PySide6.QtGui import QPainter, QPen, QColor, QLinearGradient, QBrush, QPainterPath
import math

class ProfitLossChart(QFrame):
    """Chart showing profit/loss trends over time"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFrameShape(QFrame.StyledPanel)
        self.setFrameShadow(QFrame.Raised)
        self.setMinimumSize(350, 220)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        # Background from theme QSS (QFrame styling)
        
        # Layout with title
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(15, 15, 10, 10)
        
        self.title = QLabel("Profit/Loss")
        self.title.setStyleSheet("font-weight: bold; font-size: 14px;")
        self.layout.addWidget(self.title)
        
        # Add a spacer to ensure the chart area is available for painting
        self.layout.addStretch(1)
        
        # Data for the chart
        self.data = [10, 15, 20, 15, 30, 45, 40, 50, 55, 45, 60]  # Default mock data
        
    def set_data(self, data):
        """Update chart with new data"""
        self.data = data
        self.update()  # Trigger a repaint
        
    def paintEvent(self, event):
        """Draw the profit/loss chart"""
        super().paintEvent(event)
        
        if not self.data or len(self.data) < 2:
            return
        
        # Create painter
        painter = QPainter()
        painter.begin(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        try:
            # Set up chart area
            content_rect = self.contentsRect()
            chart_rect = content_rect.adjusted(20, 50, -20, -20)  # Margins for the chart area
            
            # Find min and max values for scaling
            min_val = min(self.data)
            max_val = max(self.data)
            value_range = max(max_val - min_val, 1)  # Prevent division by zero
            
            # Draw the axes
            painter.setPen(QPen(QColor(30, 41, 59), 1))  # Theme border color
            painter.drawLine(
                chart_rect.left(), chart_rect.bottom(),
                chart_rect.right(), chart_rect.bottom()
            )
            
            # Calculate points
            points = []
            x_step = chart_rect.width() / (len(self.data) - 1)
            
            for i, value in enumerate(self.data):
                x = chart_rect.left() + i * x_step
                y_ratio = (value - min_val) / value_range
                y = chart_rect.bottom() - y_ratio * chart_rect.height()
                points.append((x, y))
            
            # Draw the line
            painter.setPen(QPen(QColor(76, 175, 80), 2))  # Theme success color
            for i in range(len(points) - 1):
                painter.drawLine(
                    int(points[i][0]), int(points[i][1]),
                    int(points[i+1][0]), int(points[i+1][1])
                )
            
            # Create and fill the area path
            gradient = QLinearGradient(
                0, chart_rect.top(),
                0, chart_rect.bottom()
            )
            gradient.setColorAt(0, QColor(76, 175, 80, 120))  # Theme success with transparency
            gradient.setColorAt(1, QColor(76, 175, 80, 10))   # Nearly transparent at bottom
            
            path = QPainterPath()
            path.moveTo(points[0][0], chart_rect.bottom())
            
            for x, y in points:
                path.lineTo(x, y)
                
            path.lineTo(points[-1][0], chart_rect.bottom())
            path.closeSubpath()
            
            painter.fillPath(path, gradient)
            
            # Draw data points
            painter.setPen(QPen(Qt.white, 1))
            painter.setBrush(QColor(76, 175, 80))  # Theme success
            
            for x, y in points:
                painter.drawEllipse(int(x-3), int(y-3), 6, 6)
                
            # Draw horizontal guide lines
            painter.setPen(QPen(QColor(30, 41, 59), 1, Qt.DashLine))  # Theme border
            num_lines = 4
            for i in range(1, num_lines):
                y = chart_rect.top() + i * chart_rect.height() / num_lines
                painter.drawLine(
                    chart_rect.left(), int(y),
                    chart_rect.right(), int(y)
                )
                
        finally:
            painter.end()
