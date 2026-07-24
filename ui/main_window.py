from PyQt5.QtWidgets import QMainWindow, QTabWidget

from ui.login import APP_NAME
from ui.material import MaterialWidget
from ui.quote_list import QuoteListWidget
from ui.users import UserManagerWidget


class MainWindow(QMainWindow):
    def __init__(self, username=''):
        super().__init__()
        self.setWindowTitle(APP_NAME + (' - ' + username if username else ''))
        self.resize(1280, 800)
        tabs = QTabWidget()
        self.material_page = MaterialWidget()
        self.quote_page = QuoteListWidget()
        tabs.addTab(self.quote_page, '报价单管理')
        tabs.addTab(self.material_page, '物料库管理')
        if username == 'woge':
            self.users_page = UserManagerWidget()
            tabs.addTab(self.users_page, '用户管理')
        self.setCentralWidget(tabs)
