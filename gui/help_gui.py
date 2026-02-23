from PySide6.QtWidgets import QWidget, QLabel
from PySide6.QtCore import Qt, QUrl
from PySide6.QtGui import QStandardItemModel, QStandardItem, QFont, QDesktopServices
from .help_ui import Ui_HelpTabMain  # Adjust import path accordingly
import logging
import re

logger = logging.getLogger(__name__)


def _inline_format(text: str) -> str:
    """Apply inline markdown formatting: bold, italic, inline code, links, images."""
    # Inline code (must be first to avoid bold/italic inside code)
    text = re.sub(r'`([^`]+)`', r'<code>\1</code>', text)
    # Images ![alt](url) — render as linked text since QTextBrowser has limited image support
    text = re.sub(r'!\[([^\]]*)\]\(([^)]+)\)', r'[Image: \1]', text)
    # Links [text](url)
    text = re.sub(r'\[([^\]]+)\]\(([^)]+)\)', r'<a href="\2">\1</a>', text)
    # Bold **text** or __text__
    text = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', text)
    text = re.sub(r'__(.+?)__', r'<strong>\1</strong>', text)
    # Italic *text* or _text_ (but not inside words with underscores)
    text = re.sub(r'(?<!\w)\*([^*]+?)\*(?!\w)', r'<em>\1</em>', text)
    text = re.sub(r'(?<!\w)_([^_]+?)_(?!\w)', r'<em>\1</em>', text)
    return text


class HelpTabMain(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.ui = Ui_HelpTabMain()
        self.ui.setupUi(self)
        self.ui.retranslateUi(self)
        
        # Store reference to content label for dynamic font scaling
        self.content_label = self.ui.content_label
        
        # Initialize documentation content
        self.initialize_documentation()
        
        # Connect signals
        self.ui.HelpTabMainDocumentationTreeView.clicked.connect(self.on_tree_item_clicked)
        self.ui.HelpTabMainAkondText.linkActivated.connect(self._open_external_link)
        
    def initialize_documentation(self):
        """Initialize the documentation content and navigation tree"""
        # Create model for tree view
        self.model = QStandardItemModel()
        self.model.setHorizontalHeaderLabels(['Documentation'])
        
        # Add sections to tree
        sections = [
            ("Getting Started", [
                "Introduction",
                "Installation",
                "First Trade"
            ]),
            ("Trading Strategies", [
                "Basic Strategies",
                "AI Strategy",
                "Custom Rules"
            ]),
            ("Indicator Settings", [
                "RSI",
                "MACD",
                "MA Cross",
                "Bollinger Bands"
            ]),
            ("Wallet Management", [
                "Setting Up Wallet",
                "Trading Parameters",
                "Security"
            ]),
            ("Trade Pair Management", [
                "Volume-Based Discovery",
                "Configuration Options",
                "Best Practices",
                "Troubleshooting"
            ]),
            ("Advanced Features", [
                "AI Configuration",
                "Custom Indicators",
                "API Integration"
            ]),
            ("FAQ", [
                "Common Issues",
                "Trading Questions",
                "Technical Support"
            ])
        ]
        
        # Add sections to model
        for section_name, subsections in sections:
            section_item = QStandardItem(section_name)
            section_item.setEditable(False)
            for subsection in subsections:
                sub_item = QStandardItem(subsection)
                sub_item.setEditable(False)
                section_item.appendRow(sub_item)
            self.model.appendRow(section_item)
        
        # Set model to tree view
        self.ui.HelpTabMainDocumentationTreeView.setModel(self.model)
        self.ui.HelpTabMainDocumentationTreeView.expandAll()
        
        # Set initial content
        self.show_section_content("Getting Started")
        
    def show_section_content(self, section_name):
        """Show content for a specific section by loading from markdown files"""
        try:
            # Map section names to markdown files
            section_to_file = {
                "Getting Started": "docs/getting_started.md",
                "Trading Strategies": "docs/trading_strategies.md",
                "Indicator Settings": "docs/indicator_settings.md",
                "Wallet Management": "docs/wallet_management.md",
                "Trade Pair Management": "docs/trade_pairs.md",
                "Advanced Features": "docs/advanced_features.md",
                "FAQ": "docs/faq.md"
            }
            
            # Get the corresponding markdown file
            markdown_file = section_to_file.get(section_name)
            if not markdown_file:
                content_html = "<p>No content available for this section</p>"
            else:
                # Read the markdown file
                try:
                    from config.paths import PACKAGE_ROOT
                    full_path = PACKAGE_ROOT / markdown_file
                    with open(full_path, 'r', encoding='utf-8') as f:
                        content_text = f.read()
                    content_html = self._markdown_to_html(content_text)
                except FileNotFoundError:
                    content_html = f"<p>Documentation file not found: {markdown_file}</p>"
                except Exception as e:
                    content_html = f"<p>Error reading documentation: {str(e)}</p>"
        except Exception as e:
            logger.error(f"Error loading documentation: {str(e)}")
            content_html = "<p>Error loading documentation. Please check the logs for details.</p>"
        
        # Update content display with styled HTML
        styled_html = f"""
        <html>
        <head>
        <style>
            body {{ color: #d4d4d4; font-family: 'Segoe UI', sans-serif; font-size: 12px; line-height: 1.6; background-color: #0a0e27; }}
            h1 {{ color: #00D4FF; font-size: 20px; border-bottom: 1px solid #1e293b; padding-bottom: 6px; margin-top: 16px; }}
            h2 {{ color: #00D4FF; font-size: 16px; margin-top: 14px; }}
            h3 {{ color: #4DA6FF; font-size: 14px; margin-top: 12px; }}
            h4 {{ color: #4DA6FF; font-size: 12px; margin-top: 10px; }}
            p {{ margin: 6px 0; }}
            code {{ background-color: #0f172a; color: #ce9178; padding: 2px 5px; border-radius: 3px; font-family: 'Consolas', monospace; }}
            pre {{ background-color: #0f172a; color: #d4d4d4; padding: 10px; border-radius: 4px; border: 1px solid #1e293b; font-family: 'Consolas', monospace; overflow-x: auto; }}
            a {{ color: #00D4FF; text-decoration: none; }}
            a:hover {{ text-decoration: underline; }}
            ul, ol {{ margin: 6px 0; padding-left: 24px; }}
            li {{ margin: 3px 0; }}
            blockquote {{ border-left: 3px solid #0D6EFD; padding-left: 12px; color: #94a3b8; margin: 8px 0; }}
            hr {{ border: none; border-top: 1px solid #1e293b; margin: 12px 0; }}
            strong {{ color: #e0e0e0; }}
            table {{ border-collapse: collapse; margin: 8px 0; }}
            th, td {{ border: 1px solid #1e293b; padding: 6px 10px; }}
            th {{ background-color: #0f172a; color: #00D4FF; }}
        </style>
        </head>
        <body>
        {content_html}
        </body>
        </html>
        """
        self.content_label.setHtml(styled_html)
        
    def _open_external_link(self, url):
        """Open an external URL in the system's default browser."""
        logger.info(f"Opening external link: {url}")
        QDesktopServices.openUrl(QUrl(url))

    def on_tree_item_clicked(self, index):
        """Handle tree item clicks"""
        item = self.model.itemFromIndex(index)
        if item.parent():  # If it's a subsection
            section_name = item.parent().text()
        else:  # If it's a section
            section_name = item.text()
        self.show_section_content(section_name)
    
    @staticmethod
    def _markdown_to_html(text: str) -> str:
        """Convert basic markdown to HTML for display in QTextBrowser."""
        lines = text.split('\n')
        html_lines = []
        in_code_block = False
        in_list = False
        list_type = None  # 'ul' or 'ol'

        for line in lines:
            # Fenced code blocks
            if line.strip().startswith('```'):
                if in_code_block:
                    html_lines.append('</pre>')
                    in_code_block = False
                else:
                    if in_list:
                        html_lines.append(f'</{list_type}>')
                        in_list = False
                    html_lines.append('<pre>')
                    in_code_block = True
                continue

            if in_code_block:
                # Escape HTML inside code blocks
                escaped = line.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
                html_lines.append(escaped)
                continue

            stripped = line.strip()

            # Horizontal rule
            if re.match(r'^---+$', stripped) or re.match(r'^\*\*\*+$', stripped):
                if in_list:
                    html_lines.append(f'</{list_type}>')
                    in_list = False
                html_lines.append('<hr/>')
                continue

            # Headings
            heading_match = re.match(r'^(#{1,4})\s+(.*)', stripped)
            if heading_match:
                if in_list:
                    html_lines.append(f'</{list_type}>')
                    in_list = False
                level = len(heading_match.group(1))
                heading_text = heading_match.group(2)
                heading_text = _inline_format(heading_text)
                html_lines.append(f'<h{level}>{heading_text}</h{level}>')
                continue

            # Blockquotes
            if stripped.startswith('>'):
                if in_list:
                    html_lines.append(f'</{list_type}>')
                    in_list = False
                quote_text = _inline_format(stripped.lstrip('> '))
                html_lines.append(f'<blockquote>{quote_text}</blockquote>')
                continue

            # Unordered list items
            ul_match = re.match(r'^\s*[-*+]\s+(.*)', line)
            if ul_match:
                if not in_list or list_type != 'ul':
                    if in_list:
                        html_lines.append(f'</{list_type}>')
                    html_lines.append('<ul>')
                    in_list = True
                    list_type = 'ul'
                item_text = _inline_format(ul_match.group(1))
                html_lines.append(f'<li>{item_text}</li>')
                continue

            # Ordered list items
            ol_match = re.match(r'^\s*\d+\.\s+(.*)', line)
            if ol_match:
                if not in_list or list_type != 'ol':
                    if in_list:
                        html_lines.append(f'</{list_type}>')
                    html_lines.append('<ol>')
                    in_list = True
                    list_type = 'ol'
                item_text = _inline_format(ol_match.group(1))
                html_lines.append(f'<li>{item_text}</li>')
                continue

            # Close list if non-list line
            if in_list:
                html_lines.append(f'</{list_type}>')
                in_list = False

            # Empty line
            if not stripped:
                html_lines.append('')
                continue

            # Regular paragraph
            html_lines.append(f'<p>{_inline_format(stripped)}</p>')

        # Close any open tags
        if in_code_block:
            html_lines.append('</pre>')
        if in_list:
            html_lines.append(f'</{list_type}>')

        return '\n'.join(html_lines)

    def resizeEvent(self, event):
        """Handle window resize to scale fonts dynamically"""
        super().resizeEvent(event)
        
        # Calculate font sizes based on widget dimensions
        widget_height = self.height()
        widget_width = self.width()
        
        # Base dimensions: 800x569 (original window size)
        base_height = 569.0
        base_width = 800.0
        
        # Calculate scale factor using both dimensions (average)
        height_scale = widget_height / base_height
        width_scale = widget_width / base_width
        scale_factor = (height_scale + width_scale) / 2.0
        
        # Constrain scale factor to reasonable range
        scale_factor = max(0.8, min(1.6, scale_factor))
        
        # Tree view font (base: 10pt)
        tree_size = max(8, int(10 * scale_factor))
        tree_font = self.ui.HelpTabMainDocumentationTreeView.font()
        tree_font.setPointSize(tree_size)
        self.ui.HelpTabMainDocumentationTreeView.setFont(tree_font)
        
        # Title font (base: 14pt)
        title_size = max(11, int(14 * scale_factor))
        title_font = self.ui.HelpTabMainDocumentationTitle.font()
        title_font.setPointSize(title_size)
        title_font.setBold(True)
        self.ui.HelpTabMainDocumentationTitle.setFont(title_font)
        
        # Akond text font (base: 12pt)
        akond_size = max(10, int(12 * scale_factor))
        akond_font = self.ui.HelpTabMainAkondText.font()
        akond_font.setPointSize(akond_size)
        self.ui.HelpTabMainAkondText.setFont(akond_font)