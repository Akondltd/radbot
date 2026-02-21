from PySide6.QtWidgets import QFrame, QVBoxLayout, QLabel, QSizePolicy
from PySide6.QtCore import Qt
from PySide6.QtGui import QPainter, QPen, QColor, QBrush, QFont
import math

class TokenDistributionChart(QFrame):
    """Pie chart showing distribution of different tokens in wallet"""
    
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
        
        self.title = QLabel("Wallet Token Distribution")
        self.title.setStyleSheet("font-weight: bold; font-size: 14px;")
        self.layout.addWidget(self.title)
        
        # Add a spacer to ensure the chart area is available for painting
        self.layout.addStretch(1)
        
        # Token data structure: [(token_name, amount, color), ...]
        self.token_data = [
            ("XRD", 65, QColor(46, 204, 113)),    # Green
            ("BTC", 20, QColor(52, 152, 219)),    # Blue
            ("ETH", 10, QColor(155, 89, 182)),    # Purple
            ("Others", 5, QColor(149, 165, 166))  # Gray
        ]
        
    def set_token_data(self, token_data):
        """
        Update the token distribution data
        
        Args:
            token_data: List of tuples (token_name, percentage, color_hex)
        """
        # Convert hex colors to QColor if needed
        processed_data = []
        for name, value, color in token_data:
            if isinstance(color, str) and color.startswith("#"):
                color = QColor(color)
            processed_data.append((name, value, color))
        
        self.token_data = processed_data
        self.update()
        
    def paintEvent(self, event):
        """Draw the token distribution pie chart"""
        super().paintEvent(event)
        
        if not self.token_data:
            return
        
        # Create and setup painter properly
        painter = QPainter()
        if not painter.begin(self):
            return
        
        painter.setRenderHint(QPainter.Antialiasing)
        
        try:
            # Chart dimensions using contentsRect for proper layout handling
            content_rect = self.contentsRect()
            chart_rect = content_rect.adjusted(30, 50, -20, -20)
            
            chart_center_x = chart_rect.center().x()
            chart_center_y = chart_rect.center().y()
            radius = min(chart_rect.width(), chart_rect.height()) / 2 - 1
            
            # Calculate total for percentages
            total = sum(amount for _, amount, _ in self.token_data)
            if total <= 0:
                return
            
            # Draw pie segments
            start_angle = 0
            
            for i, (token_name, amount, color) in enumerate(self.token_data):
                # Calculate segment angle (16 units = 1 degree in Qt)
                angle = int(360 * 16 * amount / total)
                
                # Draw pie segment
                painter.setBrush(QBrush(color))
                painter.setPen(QPen(Qt.white, 1))
                painter.drawPie(
                    int(chart_center_x - radius), 
                    int(chart_center_y - radius),
                    int(radius * 2), 
                    int(radius * 2), 
                    start_angle, 
                    angle
                )
                
                # Calculate position for label (in the middle of the segment)
                label_angle_rad = (start_angle + angle/2) * math.pi / (180 * 16)
                label_distance = radius * 0.85  # Place at 70% of the radius
                label_x = chart_center_x + int(label_distance * math.cos(label_angle_rad))
                label_y = chart_center_y - int(label_distance * math.sin(label_angle_rad))
                
                # Draw label
                painter.setPen(QPen(Qt.white))
                painter.setFont(QFont("Arial", 9, QFont.Bold))
                percentage = f"{amount / total * 100:.1f}%"
                painter.drawText(
                    int(label_x - 20), 
                    int(label_y - 10), 
                    40, 
                    20, 
                    Qt.AlignCenter, 
                    percentage
                )
                
                start_angle += angle
            
            # Draw center circle to create donut effect
            inner_radius = int(radius * 0.7)  # 70% of the radius for the hole
            painter.setBrush(QBrush(QColor("#0f172a")))  # Theme background color
            painter.setPen(Qt.NoPen)
            painter.drawEllipse(
                int(chart_center_x - inner_radius),
                int(chart_center_y - inner_radius),
                inner_radius * 2,
                inner_radius * 2
            )
                
            # Draw legend (moved up by 40px for better visibility)
            legend_x = chart_rect.left()
            legend_y = chart_rect.bottom() - 120  # Was -80, now -120
            box_size = 12
            
            for token_name, amount, color in self.token_data:
                painter.setBrush(QBrush(color))
                painter.setPen(QPen(Qt.white, 1))
                painter.drawRect(int(legend_x), int(legend_y), box_size, box_size)
                
                painter.setPen(QPen(Qt.white))
                painter.setFont(QFont("Arial", 8))
                painter.drawText(int(legend_x + box_size + 5), int(legend_y + box_size), token_name)
                
                legend_y += 20
        finally:
            painter.end()
    
    def sin(self, angle):
        """Sine function adjusted for Qt's coordinate system (y increases downward)"""
        return math.sin(angle)
        
    def cos(self, angle):
        """Cosine function"""
        return math.cos(angle)
