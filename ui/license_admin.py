from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (QDialog, QDialogButtonBox, QFormLayout,
                             QHBoxLayout, QHeaderView, QLabel, QLineEdit,
                             QMessageBox, QPushButton, QTableWidget,
                             QTableWidgetItem, QVBoxLayout, QWidget)

from db import get_conn
from license import make_serial


class GenerateDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle('生成序列号')
        self.setFixedSize(460, 220)
        lay = QVBoxLayout(self)
        form = QFormLayout()
        self.ed_customer = QLineEdit()
        self.ed_code = QLineEdit()
        self.ed_code.setPlaceholderText('客户机器码 XXXX-XXXX-XXXX-XXXX')
        form.addRow('客户名称', self.ed_customer)
        form.addRow('机器码', self.ed_code)
        lay.addLayout(form)
        self.lbl_serial = QLabel('')
        self.lbl_serial.setAlignment(Qt.AlignCenter)
        self.lbl_serial.setStyleSheet('font-size:16px;font-weight:bold;color:#c00;')
        self.lbl_serial.setTextInteractionFlags(Qt.TextSelectableByMouse)
        lay.addWidget(self.lbl_serial)
        btns = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        btns.button(QDialogButtonBox.Ok).setText('生成并保存')
        btns.accepted.connect(self.do_generate)
        btns.rejected.connect(self.reject)
        lay.addWidget(btns)
        self.result = None

    def do_generate(self):
        customer = self.ed_customer.text().strip()
        code = self.ed_code.text().strip().upper()
        if not customer or not code:
            QMessageBox.warning(self, '提示', '请填写客户名称和机器码')
            return
        serial = make_serial(code)
        conn = get_conn()
        dup = conn.execute(
            "SELECT 1 FROM license WHERE machine_code=? AND status='有效'", (code,)).fetchone()
        if dup:
            QMessageBox.warning(self, '提示', '该机器码已生成过有效序列号，如需重发请先作废原记录')
            conn.close()
            return
        conn.execute(
            'INSERT INTO license(customer, machine_code, serial, status) VALUES(?,?,?,?)',
            (customer, code, serial, '有效'))
        conn.commit()
        conn.close()
        self.lbl_serial.setText(serial)
        self.result = serial


class LicenseAdminWidget(QWidget):
    def __init__(self):
        super().__init__()
        lay = QVBoxLayout(self)

        bar = QHBoxLayout()
        b_gen = QPushButton('生成序列号')
        b_gen.clicked.connect(self.generate)
        b_toggle = QPushButton('作废/恢复')
        b_toggle.clicked.connect(self.toggle_status)
        b_del = QPushButton('删除')
        b_del.clicked.connect(self.delete)
        for b in [b_gen, b_toggle, b_del]:
            bar.addWidget(b)
        bar.addStretch()
        lay.addLayout(bar)

        self.table = QTableWidget(0, 5)
        self.table.setHorizontalHeaderLabels(['客户名称', '机器码', '序列号', '状态', '生成日期'])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        lay.addWidget(self.table)
        self.reload()

    def reload(self):
        conn = get_conn()
        rows = conn.execute('SELECT * FROM license ORDER BY id DESC').fetchall()
        conn.close()
        self.table.setRowCount(len(rows))
        self._ids = []
        for i, r in enumerate(rows):
            self._ids.append(r['id'])
            vals = [r['customer'], r['machine_code'], r['serial'], r['status'], r['created_at']]
            for j, v in enumerate(vals):
                it = QTableWidgetItem(str(v))
                it.setTextAlignment(Qt.AlignCenter)
                self.table.setItem(i, j, it)

    def generate(self):
        dlg = GenerateDialog(self)
        dlg.exec_()
        if dlg.result:
            self.reload()

    def _selected(self):
        row = self.table.currentRow()
        if row < 0:
            QMessageBox.information(self, '提示', '请先选择一行')
            return None
        return self._ids[row]

    def toggle_status(self):
        lid = self._selected()
        if lid is None:
            return
        conn = get_conn()
        conn.execute("UPDATE license SET status = CASE status WHEN '有效' THEN '已作废' ELSE '有效' END WHERE id=?", (lid,))
        conn.commit()
        conn.close()
        self.reload()

    def delete(self):
        lid = self._selected()
        if lid is None:
            return
        if QMessageBox.question(self, '确认', '确定删除该授权记录？') != QMessageBox.Yes:
            return
        conn = get_conn()
        conn.execute('DELETE FROM license WHERE id=?', (lid,))
        conn.commit()
        conn.close()
        self.reload()
