from PyQt5.QtWidgets import QMainWindow, QTabWidget

from ui.material import MaterialWidget
from ui.quote_list import QuoteListWidget


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('窝哥报价系统')
        self.resize(1280, 800)
        tabs = QTabWidget()
        self.material_page = MaterialWidget()
        self.quote_page = QuoteListWidget()
        tabs.addTab(self.quote_page, '报价单管理')
        tabs.addTab(self.material_page, '物料库管理')
        self.setCentralWidget(tabs)
