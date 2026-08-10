import json
import subprocess
from PyQt6.QtWidgets import (
    QFrame, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton, QComboBox, 
    QScrollArea, QWidget, QMessageBox, QApplication
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QUrl
from PyQt6.QtGui import QClipboard, QPixmap
from PyQt6.QtNetwork import QNetworkAccessManager, QNetworkRequest, QNetworkReply

class SearchThread(QThread):
    results_ready = pyqtSignal(list)
    error_occurred = pyqtSignal(str)

    def __init__(self, query, platform, region):
        super().__init__()
        self.query = query
        self.platform = platform
        self.region = region

    def run(self):
        try:
            results = []
            if self.platform == "YouTube Shorts":
                # yt-dlp ytsearch
                search_query = f"ytsearch10:{self.query} shorts {self.region}"
                cmd = ["yt-dlp", search_query, "--dump-json", "--no-warnings"]
                
                process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
                out, err = process.communicate()
                
                for line in out.splitlines():
                    if not line.strip(): continue
                    try:
                        data = json.loads(line)
                        results.append({
                            "title": data.get("title", "Unknown Title"),
                            "url": data.get("webpage_url", ""),
                            "thumbnail": data.get("thumbnail", ""),
                            "views": data.get("view_count", 0),
                            "likes": data.get("like_count", 0)
                        })
                    except:
                        pass
                
                if not results and err:
                    self.error_occurred.emit(f"Error fetching data: {err}")
                    return
                    
            elif self.platform == "TikTok":
                # Mock / Link generator for TikTok since scraping is blocked
                region_query = f"{self.query} viral {self.region}".replace(" ", "+")
                base_url = f"https://www.tiktok.com/search/video?q={region_query}"
                
                # We just return 10 generic search pointers for the user to explore
                for i in range(1, 11):
                    results.append({
                        "title": f"TikTok Search Result #{i} ({self.region})",
                        "url": base_url,
                        "thumbnail": "",
                        "views": "N/A",
                        "likes": "N/A"
                    })

            self.results_ready.emit(results)
        except Exception as e:
            self.error_occurred.emit(str(e))

class ReferencePanel(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("glass_panel")
        self.network_manager = QNetworkAccessManager(self)
        
        layout = QVBoxLayout(self)
        
        title_lbl = QLabel("Viral References")
        title_lbl.setObjectName("heading")
        layout.addWidget(title_lbl)
        
        desc_lbl = QLabel("Search trending videos to use as inspiration or source material")
        desc_lbl.setObjectName("subheading")
        layout.addWidget(desc_lbl)
        
        # Search controls
        search_layout = QHBoxLayout()
        self.query_input = QLineEdit()
        self.query_input.setPlaceholderText("Topic (e.g. podcast, funny, motivation)...")
        search_layout.addWidget(self.query_input, stretch=2)
        
        self.platform_combo = QComboBox()
        self.platform_combo.addItems(["YouTube Shorts", "TikTok"])
        search_layout.addWidget(self.platform_combo, stretch=1)
        
        self.region_combo = QComboBox()
        self.region_combo.addItems(["Global", "United States", "Indonesia", "United Kingdom", "Japan"])
        search_layout.addWidget(self.region_combo, stretch=1)
        
        self.search_btn = QPushButton("Search")
        self.search_btn.setObjectName("primary_btn")
        self.search_btn.clicked.connect(self.do_search)
        search_layout.addWidget(self.search_btn)
        
        layout.addLayout(search_layout)
        
        self.status_lbl = QLabel("")
        layout.addWidget(self.status_lbl)
        
        # Results Area
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setStyleSheet("background-color: transparent;")
        
        self.scroll_content = QWidget()
        self.scroll_content.setStyleSheet("background-color: transparent;")
        self.results_layout = QVBoxLayout(self.scroll_content)
        self.results_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        
        self.scroll.setWidget(self.scroll_content)
        layout.addWidget(self.scroll)
        
    def do_search(self):
        query = self.query_input.text().strip()
        if not query:
            query = "viral"
            
        platform = self.platform_combo.currentText()
        region = self.region_combo.currentText()
        
        self.search_btn.setEnabled(False)
        self.status_lbl.setText("Searching... Please wait.")
        
        # Clear old results
        for i in reversed(range(self.results_layout.count())):
            w = self.results_layout.itemAt(i).widget()
            if w: w.deleteLater()
            
        self.thread = SearchThread(query, platform, region)
        self.thread.results_ready.connect(self.on_results)
        self.thread.error_occurred.connect(self.on_error)
        self.thread.start()
        
    def on_results(self, results):
        self.search_btn.setEnabled(True)
        self.status_lbl.setText(f"Found {len(results)} references.")
        
        for item in results:
            card = QFrame()
            card.setStyleSheet("background-color: #161226; border: 1px solid #2B2B2B; border-radius: 8px;")
            card_layout = QHBoxLayout(card)
            
            # Thumbnail
            thumb_lbl = QLabel()
            thumb_lbl.setFixedSize(120, 68)
            thumb_lbl.setScaledContents(True)
            thumb_lbl.setStyleSheet("background-color: #2B2B2B; border-radius: 4px;")
            card_layout.addWidget(thumb_lbl)
            
            if item.get("thumbnail"):
                req = QNetworkRequest(QUrl(item["thumbnail"]))
                reply = self.network_manager.get(req)
                reply.finished.connect(lambda lbl=thumb_lbl: self.on_thumbnail_loaded(lbl))
            else:
                thumb_lbl.setText("No Image")
                thumb_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            
            # Title and Stats
            info_layout = QVBoxLayout()
            
            title = QLabel(item['title'])
            title.setWordWrap(True)
            info_layout.addWidget(title)
            
            def fmt(n):
                if n == "N/A": return n
                try:
                    c = int(n)
                    if c >= 1000000: return f"{c/1000000:.1f}M"
                    if c >= 1000: return f"{c/1000:.1f}K"
                    return str(c)
                except: return "N/A"
                
            stats_lbl = QLabel(f"{fmt(item.get('views', 0))} views   {fmt(item.get('likes', 0))} likes")
            stats_lbl.setStyleSheet("color: #A7A0C4; font-size: 12px; font-weight: bold;")
            info_layout.addWidget(stats_lbl)
            
            card_layout.addLayout(info_layout, stretch=1)
            
            # Actions
            btn_browser = QPushButton("Open in Browser")
            url = item['url']
            btn_browser.clicked.connect(lambda checked, u=url: self.open_url(u))
            card_layout.addWidget(btn_browser)
            
            btn_copy = QPushButton("Copy Link")
            btn_copy.clicked.connect(lambda checked, u=url: self.copy_url(u))
            card_layout.addWidget(btn_copy)
            
            self.results_layout.addWidget(card)
            
    def on_thumbnail_loaded(self, label):
        reply = self.sender()
        if not reply: return
        
        if reply.error() == QNetworkReply.NetworkError.NoError:
            data = reply.readAll()
            pixmap = QPixmap()
            pixmap.loadFromData(data)
            if not pixmap.isNull():
                label.setPixmap(pixmap)
        reply.deleteLater()
        
    def on_error(self, err):
        self.search_btn.setEnabled(True)
        self.status_lbl.setText("Error occurred during search.")
        QMessageBox.warning(self, "Search Error", err)
        
    def open_url(self, url):
        import webbrowser
        webbrowser.open(url)
        
    def copy_url(self, url):
        clipboard = QApplication.clipboard()
        clipboard.setText(url)
        QMessageBox.information(self, "Copied", "Link copied to clipboard! You can paste it into the Input Panel.")
