from PyQt5.QtCore import Qt, QDate
from PyQt5.QtWidgets import (QCheckBox, QDateEdit, QDialog, QDialogButtonBox,
                             QFileDialog, QFormLayout, QHBoxLayout, QHeaderView,
                             QLabel, QLineEdit, QMessageBox, QPushButton,
                             QTableWidget, QTableWidgetItem, QVBoxLayout,
                             QWidget)

from db import get_conn
from importer import parse_material_file
from utils import fmt_money, normalize_date, to_float

COLUMNS = ['', 'ID', '客户', '物料名称', '规格', '代码', '单位', '单价', '数量', '日期', '合同号', '合计']


class MaterialEditDialog(QDialog):
    def __init__(self, parent=None, data=None):
        super().__init__(parent)
        self.setWindowTitle('编辑物料' if data else '新增物料')
        self.setMinimumWidth(420)
        data = data or {}
        form = QFormLayout(self)
        self.edits = {}
        fields = [('customer', '客户'), ('name', '物料名称'), ('spec', '规格'),
                  ('code', '代码'), ('unit', '单位'), ('price', '单价'),
                  ('qty', '数量'), ('date', '日期(YYYY-MM-DD)'),
                  ('contract_no', '合同号')]
        for key, label in fields:
            e = QLineEdit(str(data.get(key, '') or ''))
            self.edits[key] = e
            form.addRow(label, e)
        btns = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        btns.accepted.connect(self.accept)
        btns.rejected.connect(self.reject)
        form.addRow(btns)

    def values(self):
        v = {k: e.text().strip() for k, e in self.edits.items()}
        v['price'] = to_float(v['price'])
        v['qty'] = to_float(v['qty'])
        v['date'] = normalize_date(v['date'])
        v['total'] = round(v['price'] * v['qty'], 2)
        return v


class MaterialWidget(QWidget):
    def __init__(self):
        super().__init__()
        lay = QVBoxLayout(self)

        bar = QHBoxLayout()
        self.f_contract = QLineEdit()
        self.f_contract.setPlaceholderText('合同号')
        self.f_name = QLineEdit()
        self.f_name.setPlaceholderText('物料名称')
        self.f_code = QLineEdit()
        self.f_code.setPlaceholderText('物料代码')
        self.f_date_from = QDateEdit(QDate.currentDate().addYears(-10))
        self.f_date_from.setCalendarPopup(True)
        self.f_date_from.setDisplayFormat('yyyy-MM-dd')
        self.f_date_to = QDateEdit(QDate.currentDate().addYears(1))
        self.f_date_to.setCalendarPopup(True)
        self.f_date_to.setDisplayFormat('yyyy-MM-dd')
        self.f_date_on = QCheckBox('按日期')
        btn_search = QPushButton('查询')
        btn_search.clicked.connect(self.reload)
        btn_reset = QPushButton('重置')
        btn_reset.clicked.connect(self.reset_filter)
        for w in [self.f_contract, self.f_name, self.f_code, self.f_date_on,
                  QLabel('从'), self.f_date_from, QLabel('到'), self.f_date_to,
                  btn_search, btn_reset]:
            bar.addWidget(w)
        lay.addLayout(bar)

        bar2 = QHBoxLayout()
        btn_import = QPushButton('批量导入')
        btn_import.clicked.connect(self.do_import)
        btn_sel_all = QPushButton('全选')
        btn_sel_all.setCheckable(True)
        btn_sel_all.toggled.connect(self.toggle_select_all)
        btn_export = QPushButton('批量导出')
        btn_export.clicked.connect(self.do_export)
        btn_del = QPushButton('批量删除')
        btn_del.clicked.connect(self.batch_delete)
        btn_add = QPushButton('新增')
        btn_add.clicked.connect(self.add_row)
        btn_edit = QPushButton('编辑')
        btn_edit.clicked.connect(self.edit_selected)
        self.lbl_count = QLabel('')
        for w in [btn_import, btn_export, btn_sel_all, btn_del, btn_add, btn_edit]:
            bar2.addWidget(w)
        bar2.addStretch()
        bar2.addWidget(self.lbl_count)
        lay.addLayout(bar2)

        self.table = QTableWidget(0, len(COLUMNS))
        self.table.setHorizontalHeaderLabels(COLUMNS)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(3, QHeaderView.Stretch)
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.itemDoubleClicked.connect(lambda *_: self.edit_selected())
        lay.addWidget(self.table)
        self.reload()

    def reset_filter(self):
        self.f_contract.clear()
        self.f_name.clear()
        self.f_code.clear()
        self.f_date_on.setChecked(False)
        self.reload()

    def _query_rows(self):
        sql = 'SELECT * FROM material WHERE 1=1'
        args = []
        if self.f_contract.text().strip():
            sql += ' AND contract_no LIKE ?'
            args.append('%' + self.f_contract.text().strip() + '%')
        if self.f_name.text().strip():
            sql += ' AND name LIKE ?'
            args.append('%' + self.f_name.text().strip() + '%')
        if self.f_code.text().strip():
            sql += ' AND code LIKE ?'
            args.append('%' + self.f_code.text().strip() + '%')
        if self.f_date_on.isChecked():
            sql += ' AND date BETWEEN ? AND ?'
            args += [self.f_date_from.date().toString('yyyy-MM-dd'),
                     self.f_date_to.date().toString('yyyy-MM-dd')]
        sql += ' ORDER BY date DESC, id DESC'
        conn = get_conn()
        rows = conn.execute(sql, args).fetchall()
        conn.close()
        return rows

    def reload(self):
        rows = self._query_rows()
        self.table.setRowCount(0)
        self.table.setRowCount(len(rows))
        for i, r in enumerate(rows):
            chk = QTableWidgetItem()
            chk.setFlags(Qt.ItemIsUserCheckable | Qt.ItemIsEnabled)
            chk.setCheckState(Qt.Unchecked)
            self.table.setItem(i, 0, chk)
            vals = [r['id'], r['customer'], r['name'], r['spec'], r['code'],
                    r['unit'], fmt_money(r['price']), r['qty'], r['date'],
                    r['contract_no'], fmt_money(r['total'])]
            for j, v in enumerate(vals, start=1):
                it = QTableWidgetItem(str(v if v is not None else ''))
                it.setFlags(it.flags() & ~Qt.ItemIsEditable)
                self.table.setItem(i, j, it)
        self.lbl_count.setText('共 {} 条'.format(len(rows)))

    def toggle_select_all(self, checked):
        state = Qt.Checked if checked else Qt.Unchecked
        for i in range(self.table.rowCount()):
            chk = self.table.item(i, 0)
            if chk:
                chk.setCheckState(state)

    def _selected_ids(self):
        ids = []
        for i in range(self.table.rowCount()):
            chk = self.table.item(i, 0)
            if chk and chk.checkState() == Qt.Checked:
                ids.append(int(self.table.item(i, 1).text()))
        return ids

    def do_import(self):
        path, _ = QFileDialog.getOpenFileName(
            self, '选择导入文件（附件01模版）', '', '数据文件 (*.csv *.xlsx)')
        if not path:
            return
        try:
            rows = parse_material_file(path)
        except Exception as e:
            QMessageBox.critical(self, '导入失败', str(e))
            return
        if not rows:
            QMessageBox.information(self, '提示', '文件中没有可导入的数据')
            return
        conn = get_conn()
        conn.executemany(
            'INSERT INTO material(customer,name,spec,code,unit,price,qty,date,contract_no,total)'
            ' VALUES(:customer,:name,:spec,:code,:unit,:price,:qty,:date,:contract_no,:total)',
            rows)
        conn.commit()
        conn.close()
        QMessageBox.information(self, '导入完成', '成功导入 {} 条记录'.format(len(rows)))
        self.reload()

    def do_export(self):
        rows = self._query_rows()
        if not rows:
            QMessageBox.information(self, '提示', '当前没有可导出的数据')
            return
        path, _ = QFileDialog.getSaveFileName(
            self, '导出物料', '物料导出.xlsx', 'Excel (*.xlsx)')
        if not path:
            return
        import openpyxl
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.append(['签单日期', '销售合同号', '客户', '物料名称', '规格型号',
                   '物料编码', '销售单位', '销售数量', '单价',
                   '价税合计', '价税合计（本位币）', '销售员', '备注'])
        for r in rows:
            total = r['total'] or round((r['price'] or 0) * (r['qty'] or 0), 2)
            ws.append([r['date'], r['contract_no'], r['customer'], r['name'],
                       r['spec'], r['code'], r['unit'], r['qty'], r['price'],
                       total, total, '', ''])
        for col, w in zip('ABCDEFGHIJKLM', [12, 16, 28, 24, 24, 12, 8, 10, 12, 14, 18, 10, 10]):
            ws.column_dimensions[col].width = w
        try:
            wb.save(path)
        except Exception as e:
            QMessageBox.critical(self, '导出失败', str(e))
            return
        QMessageBox.information(self, '完成', '已导出 {} 条：\n{}'.format(len(rows), path))

    def batch_delete(self):
        ids = self._selected_ids()
        if not ids:
            QMessageBox.information(self, '提示', '请先勾选要删除的行')
            return
        if QMessageBox.question(self, '确认', '确定删除选中的 {} 条记录？'.format(len(ids))) != QMessageBox.Yes:
            return
        conn = get_conn()
        conn.executemany('DELETE FROM material WHERE id=?', [(i,) for i in ids])
        conn.commit()
        conn.close()
        self.reload()

    def add_row(self):
        dlg = MaterialEditDialog(self)
        if dlg.exec_() == QDialog.Accepted:
            v = dlg.values()
            conn = get_conn()
            conn.execute(
                'INSERT INTO material(customer,name,spec,code,unit,price,qty,date,contract_no,total)'
                ' VALUES(?,?,?,?,?,?,?,?,?,?)',
                (v['customer'], v['name'], v['spec'], v['code'], v['unit'],
                 v['price'], v['qty'], v['date'], v['contract_no'], v['total']))
            conn.commit()
            conn.close()
            self.reload()

    def edit_selected(self):
        row = self.table.currentRow()
        if row < 0:
            QMessageBox.information(self, '提示', '请先选择一行')
            return
        mid = int(self.table.item(row, 1).text())
        conn = get_conn()
        r = conn.execute('SELECT * FROM material WHERE id=?', (mid,)).fetchone()
        conn.close()
        dlg = MaterialEditDialog(self, dict(r))
        if dlg.exec_() == QDialog.Accepted:
            v = dlg.values()
            conn = get_conn()
            conn.execute(
                'UPDATE material SET customer=?,name=?,spec=?,code=?,unit=?,price=?,qty=?,date=?,contract_no=?,total=?'
                ' WHERE id=?',
                (v['customer'], v['name'], v['spec'], v['code'], v['unit'],
                 v['price'], v['qty'], v['date'], v['contract_no'], v['total'], mid))
            conn.commit()
            conn.close()
            self.reload()
