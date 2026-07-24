from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (QDialog, QDialogButtonBox, QFormLayout,
                             QHBoxLayout, QHeaderView, QLineEdit, QMessageBox,
                             QPushButton, QTableWidget, QTableWidgetItem,
                             QVBoxLayout, QWidget)

from db import get_conn

ADMIN_NAME = 'woge'


class UserEditDialog(QDialog):
    def __init__(self, parent=None, name='', password=''):
        super().__init__(parent)
        self.setWindowTitle('编辑用户' if name else '新增用户')
        self.setFixedSize(340, 170)
        form = QFormLayout(self)
        self.ed_name = QLineEdit(name)
        form.addRow('用户名称', self.ed_name)
        self.ed_pwd = QLineEdit(password)
        self.ed_pwd.setPlaceholderText('登录密码')
        form.addRow('登录密码', self.ed_pwd)
        btns = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        btns.accepted.connect(self.accept)
        btns.rejected.connect(self.reject)
        form.addRow(btns)

    def value(self):
        return self.ed_name.text().strip(), self.ed_pwd.text()


class UserManagerWidget(QWidget):
    def __init__(self):
        super().__init__()
        lay = QVBoxLayout(self)

        bar = QHBoxLayout()
        b_add = QPushButton('新增用户')
        b_add.clicked.connect(self.add_user)
        b_edit = QPushButton('编辑')
        b_edit.clicked.connect(self.edit_user)
        b_toggle = QPushButton('禁用/启用')
        b_toggle.clicked.connect(self.toggle_user)
        b_del = QPushButton('删除')
        b_del.clicked.connect(self.delete_user)
        for b in [b_add, b_edit, b_toggle, b_del]:
            bar.addWidget(b)
        bar.addStretch()
        lay.addLayout(bar)

        self.table = QTableWidget(0, 4)
        self.table.setHorizontalHeaderLabels(['ID', '用户名称', '角色', '状态'])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        lay.addWidget(self.table)
        self.reload()

    def reload(self):
        conn = get_conn()
        rows = conn.execute('SELECT * FROM users ORDER BY is_admin DESC, id').fetchall()
        conn.close()
        self.table.setRowCount(len(rows))
        for i, r in enumerate(rows):
            vals = [r['id'], r['name'],
                    '超级管理员' if r['is_admin'] else '普通用户',
                    '已禁用' if r['disabled'] else '正常']
            for j, v in enumerate(vals):
                it = QTableWidgetItem(str(v))
                it.setTextAlignment(Qt.AlignCenter)
                self.table.setItem(i, j, it)

    def _selected(self):
        row = self.table.currentRow()
        if row < 0:
            QMessageBox.information(self, '提示', '请先选择一行')
            return None
        return int(self.table.item(row, 0).text()), self.table.item(row, 1).text()

    def add_user(self):
        dlg = UserEditDialog(self)
        if dlg.exec_() == QDialog.Accepted:
            name, pwd = dlg.value()
            if not name or not pwd:
                QMessageBox.warning(self, '提示', '名称和密码不能为空')
                return
            conn = get_conn()
            try:
                conn.execute('INSERT INTO users(name, password) VALUES(?, ?)', (name, pwd))
                conn.commit()
            except Exception:
                QMessageBox.warning(self, '失败', '用户名已存在')
            conn.close()
            self.reload()

    def edit_user(self):
        sel = self._selected()
        if not sel:
            return
        uid, old_name = sel
        conn = get_conn()
        row = conn.execute('SELECT password FROM users WHERE id=?', (uid,)).fetchone()
        conn.close()
        dlg = UserEditDialog(self, old_name, row['password'] if row else '')
        if old_name == ADMIN_NAME:
            dlg.ed_name.setReadOnly(True)
        if dlg.exec_() == QDialog.Accepted:
            name, pwd = dlg.value()
            if not name or not pwd:
                QMessageBox.warning(self, '提示', '名称和密码不能为空')
                return
            conn = get_conn()
            try:
                conn.execute('UPDATE users SET name=?, password=? WHERE id=?', (name, pwd, uid))
                conn.commit()
            except Exception:
                QMessageBox.warning(self, '失败', '用户名已存在')
            conn.close()
            self.reload()

    def toggle_user(self):
        sel = self._selected()
        if not sel:
            return
        uid, name = sel
        if name == ADMIN_NAME:
            QMessageBox.warning(self, '提示', '超级管理员不能禁用')
            return
        conn = get_conn()
        conn.execute('UPDATE users SET disabled = 1 - disabled WHERE id=?', (uid,))
        conn.commit()
        conn.close()
        self.reload()

    def delete_user(self):
        sel = self._selected()
        if not sel:
            return
        uid, name = sel
        if name == ADMIN_NAME:
            QMessageBox.warning(self, '提示', '超级管理员不能删除')
            return
        if QMessageBox.question(self, '确认', '确定删除用户 “{}”？'.format(name)) != QMessageBox.Yes:
            return
        conn = get_conn()
        conn.execute('DELETE FROM users WHERE id=?', (uid,))
        conn.commit()
        conn.close()
        self.reload()
