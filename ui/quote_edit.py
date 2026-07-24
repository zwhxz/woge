from PyQt5.QtCore import Qt, QDate
from PyQt5.QtWidgets import (QDateEdit, QDialog, QFileDialog, QHBoxLayout,
                             QHeaderView, QLabel, QLineEdit, QMessageBox,
                             QPushButton, QTableWidget, QTableWidgetItem,
                             QTextEdit, QVBoxLayout, QWidget)

from db import get_conn
from export_excel import export_quote
from utils import fmt_money, normalize_party_info, rmb_upper, to_float

DEFAULT_PROJECT = '圣农食品九厂制冰机维修保养报价'
DEFAULT_SELLER = ('卖方（盖章）：福建雪人震巽发展有限公司\n'
                  '法定代表人/委托代理人：\n\n'
                  '地址：长乐市航城街道里仁工业区（二期）\n'
                  '开户银行：中信银行股份有限公司福州长乐支行\n'
                  '帐　　号：7345 3101 8260 0025 327 \n'
                  '电　　话：0591-28513299\n\n'
                  '传    真：0591-28765621')
DEFAULT_BUYER = ('买方（盖章）：福建圣农食品有限公司 \n\n'
                 '法定代表人/委托代理人：\n'
                 '地址：\n'
                 '开户银行： \n'
                 '帐　　号：\n'
                 '电　　话：\n'
                 '传    真：')

COL_TOTAL = 7


class HistoryDialog(QDialog):
    def __init__(self, parent, keyword):
        super().__init__(parent)
        self.setWindowTitle('历史报价（按日期倒序）')
        self.resize(980, 480)
        self.selected = None
        lay = QVBoxLayout(self)
        lay.addWidget(QLabel('物料库中包含 “{}” 的历史报价：'.format(keyword)))
        self.table = QTableWidget(0, 9)
        self.table.setHorizontalHeaderLabels(
            ['日期', '客户', '物料名称', '规格', '代码', '单位', '单价', '数量', '合同号'])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.doubleClicked.connect(self.accept)
        lay.addWidget(self.table)
        btn = QPushButton('选择该行并填充')
        btn.clicked.connect(self.accept)
        lay.addWidget(btn)

        conn = get_conn()
        rows = conn.execute(
            'SELECT * FROM material WHERE code = ? OR name LIKE ? ORDER BY date DESC, id DESC',
            (keyword, '%' + keyword + '%')).fetchall()
        conn.close()
        self.table.setRowCount(len(rows))
        for i, r in enumerate(rows):
            vals = [r['date'], r['customer'], r['name'], r['spec'], r['code'],
                    r['unit'], fmt_money(r['price']), r['qty'], r['contract_no']]
            for j, v in enumerate(vals):
                self.table.setItem(i, j, QTableWidgetItem(str(v)))
        self._rows = rows
        if rows:
            self.table.selectRow(0)

    def accept(self):
        row = self.table.currentRow()
        if row >= 0 and row < len(self._rows):
            r = self._rows[row]
            self.selected = {'name': r['name'], 'spec': r['spec'],
                             'code': r['code'], 'unit': r['unit'],
                             'price': r['price']}
        super().accept()


class QuoteEditDialog(QDialog):
    def __init__(self, parent=None, quote_id=None):
        super().__init__(parent)
        self.quote_id = quote_id
        self.setWindowTitle('编辑报价单' if quote_id else '新增报价单')
        self.resize(1250, 850)
        self._updating = False
        lay = QVBoxLayout(self)

        top = QHBoxLayout()
        top.addWidget(QLabel('日期：'))
        self.dt = QDateEdit(QDate.currentDate())
        self.dt.setCalendarPopup(True)
        self.dt.setDisplayFormat('yyyy-MM-dd')
        top.addWidget(self.dt)
        top.addWidget(QLabel('项目名称：'))
        self.ed_project = QLineEdit(DEFAULT_PROJECT)
        top.addWidget(self.ed_project, 1)
        lay.addLayout(top)

        self.table = QTableWidget(0, 11)
        self.table.setHorizontalHeaderLabels(
            ['序号', '名称', '规格', '代码', '单价', '单位', '数量', '总价', '备注', '查询', '删除'])
        self.table.verticalHeader().setDefaultSectionSize(40)
        self.table.setMinimumHeight(340)
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.itemChanged.connect(self.on_item_changed)
        lay.addWidget(self.table, 3)

        row_btn = QHBoxLayout()
        b_add = QPushButton('新增行')
        b_add.clicked.connect(lambda: self.add_row())
        row_btn.addWidget(b_add)
        row_btn.addStretch()
        lay.addLayout(row_btn)

        total_bar = QHBoxLayout()
        self.lbl_upper = QLabel('合计金额（大写）：零元整')
        self.lbl_lower = QLabel('合计（小写）：0.00')
        total_bar.addWidget(self.lbl_upper)
        total_bar.addStretch()
        total_bar.addWidget(self.lbl_lower)
        lay.addLayout(total_bar)

        lay.addWidget(QLabel('方案（300字以内）：'))
        self.ed_plan = QTextEdit()
        self.ed_plan.setMaximumHeight(90)
        lay.addWidget(self.ed_plan)

        party = QHBoxLayout()
        left = QVBoxLayout()
        left.addWidget(QLabel('卖方信息（20行以内）：'))
        self.ed_seller = QTextEdit(DEFAULT_SELLER)
        left.addWidget(self.ed_seller)
        right = QVBoxLayout()
        right.addWidget(QLabel('买方信息（20行以内）：'))
        self.ed_buyer = QTextEdit(DEFAULT_BUYER)
        right.addWidget(self.ed_buyer)
        party.addLayout(left)
        party.addLayout(right)
        lay.addLayout(party, 2)

        btns = QHBoxLayout()
        btns.addStretch()
        b_close = QPushButton('关闭')
        b_close.clicked.connect(self.reject)
        b_save = QPushButton('保存')
        b_save.clicked.connect(self.save)
        b_export = QPushButton('导出excel')
        b_export.clicked.connect(self.save_and_export)
        for b in [b_close, b_save, b_export]:
            btns.addWidget(b)
        lay.addLayout(btns)

        if quote_id:
            self.load_quote(quote_id)
        if self.table.rowCount() == 0:
            for _ in range(5):
                self.add_row()
        self._fix_column_widths()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._fix_column_widths()

    def _fix_column_widths(self):
        w = self.table.viewport().width() - 10
        fixed = {0: 45, 9: 52, 10: 52}
        wide_cols = [1, 2, 8]
        full_cols = [3, 4, 5, 6, 7]
        avail = max(w - sum(fixed.values()), 400)
        unit = avail / (len(full_cols) + 2 * len(wide_cols))
        for c, wd in fixed.items():
            self.table.setColumnWidth(c, wd)
        for c in wide_cols:
            self.table.setColumnWidth(c, int(unit * 2))
        for c in full_cols:
            self.table.setColumnWidth(c, int(unit))

    def load_quote(self, qid):
        conn = get_conn()
        q = conn.execute('SELECT * FROM quote WHERE id=?', (qid,)).fetchone()
        items = conn.execute(
            'SELECT * FROM quote_item WHERE quote_id=? ORDER BY seq', (qid,)).fetchall()
        conn.close()
        if not q:
            return
        self.dt.setDate(QDate.fromString(q['quote_date'], 'yyyy-MM-dd'))
        self.ed_project.setText(q['project_name'])
        self.ed_plan.setPlainText(q['plan'])
        self.ed_seller.setPlainText(q['seller'])
        self.ed_buyer.setPlainText(q['buyer'])
        for it in items:
            self.add_row(dict(it))

    def add_row(self, data=None):
        self._updating = True
        row = self.table.rowCount()
        self.table.insertRow(row)
        data = data or {}
        vals = [str(row + 1), data.get('name', ''), data.get('spec', ''),
                data.get('code', ''), data.get('price', '') if data.get('price') is not None else '',
                data.get('unit', ''), data.get('qty', '') if data.get('qty') is not None else '',
                '', data.get('remark', '')]
        for j, v in enumerate(vals):
            it = QTableWidgetItem(str(v))
            if j in (0, COL_TOTAL):
                it.setFlags(it.flags() & ~Qt.ItemIsEditable)
            self.table.setItem(row, j, it)
        b_q = QPushButton('查询')
        b_q.clicked.connect(lambda: self.query_history(self._btn_row()))
        b_d = QPushButton('删除')
        b_d.clicked.connect(lambda: self.del_row(self._btn_row()))
        self.table.setCellWidget(row, 9, b_q)
        self.table.setCellWidget(row, 10, b_d)
        if data:
            self.recalc_row(row)
        self._updating = False
        self.recalc_total()

    def _btn_row(self):
        btn = self.sender()
        if btn is None:
            return -1
        return self.table.indexAt(btn.pos()).row()

    def del_row(self, row):
        if 0 <= row < self.table.rowCount():
            self.table.removeRow(row)
        self._updating = True
        for i in range(self.table.rowCount()):
            self.table.item(i, 0).setText(str(i + 1))
        self._updating = False
        self.recalc_total()

    def query_history(self, row):
        code_item = self.table.item(row, 3)
        name_item = self.table.item(row, 1)
        keyword = (code_item.text().strip() if code_item else '') or \
                  (name_item.text().strip() if name_item else '')
        if not keyword:
            QMessageBox.information(self, '提示', '请先填写代码或名称再查询')
            return
        dlg = HistoryDialog(self, keyword)
        if dlg.exec_() and dlg.selected:
            s = dlg.selected
            self._updating = True
            self.table.item(row, 1).setText(s['name'])
            self.table.item(row, 2).setText(s['spec'])
            self.table.item(row, 3).setText(s['code'])
            self.table.item(row, 4).setText(fmt_money(s['price']).replace(',', ''))
            self.table.item(row, 5).setText(s['unit'])
            self._updating = False
            self.recalc_row(row)
            self.recalc_total()

    def on_item_changed(self, item):
        if self._updating or item.column() not in (4, 6):
            return
        self.recalc_row(item.row())
        self.recalc_total()

    def recalc_row(self, row):
        price = to_float(self.table.item(row, 4).text() if self.table.item(row, 4) else '')
        qty = to_float(self.table.item(row, 6).text() if self.table.item(row, 6) else '')
        self._updating = True
        self.table.item(row, COL_TOTAL).setText(fmt_money(price * qty))
        self._updating = False

    def recalc_total(self):
        total = 0.0
        for i in range(self.table.rowCount()):
            it = self.table.item(i, COL_TOTAL)
            total += to_float(it.text() if it else '')
        self.lbl_upper.setText('合计金额（大写）：' + rmb_upper(total))
        self.lbl_lower.setText('合计（小写）：' + fmt_money(total))
        return total

    def collect(self):
        items = []
        for i in range(self.table.rowCount()):
            name = self.table.item(i, 1).text().strip() if self.table.item(i, 1) else ''
            code = self.table.item(i, 3).text().strip() if self.table.item(i, 3) else ''
            price = to_float(self.table.item(i, 4).text() if self.table.item(i, 4) else '')
            qty = to_float(self.table.item(i, 6).text() if self.table.item(i, 6) else '')
            if not name and not code and not price and not qty:
                continue
            items.append({
                'seq': len(items) + 1,
                'name': name,
                'spec': self.table.item(i, 2).text().strip() if self.table.item(i, 2) else '',
                'code': code,
                'price': price,
                'unit': self.table.item(i, 5).text().strip() if self.table.item(i, 5) else '',
                'qty': qty,
                'total': round(price * qty, 2),
                'remark': self.table.item(i, 8).text().strip() if self.table.item(i, 8) else '',
            })
        plan = self.ed_plan.toPlainText().strip()
        if len(plan) > 300:
            QMessageBox.warning(self, '提示', '方案内容超过300字，已截断')
            plan = plan[:300]
        seller = normalize_party_info(
            '\n'.join(self.ed_seller.toPlainText().split('\n')[:20]))
        buyer = normalize_party_info(
            '\n'.join(self.ed_buyer.toPlainText().split('\n')[:20]))
        self.ed_seller.setPlainText(seller)
        self.ed_buyer.setPlainText(buyer)
        return {
            'quote_date': self.dt.date().toString('yyyy-MM-dd'),
            'project_name': self.ed_project.text().strip() or DEFAULT_PROJECT,
            'plan': plan,
            'seller': seller,
            'buyer': buyer,
            'total': round(sum(i['total'] for i in items), 2),
        }, items

    def save(self, quiet=False):
        quote, items = self.collect()
        if not items:
            QMessageBox.warning(self, '提示', '请至少填写一行物料')
            return False
        conn = get_conn()
        if self.quote_id:
            conn.execute(
                'UPDATE quote SET quote_date=?,project_name=?,plan=?,seller=?,buyer=?,total=? WHERE id=?',
                (quote['quote_date'], quote['project_name'], quote['plan'],
                 quote['seller'], quote['buyer'], quote['total'], self.quote_id))
            conn.execute('DELETE FROM quote_item WHERE quote_id=?', (self.quote_id,))
            qid = self.quote_id
            row = conn.execute('SELECT contract_no FROM quote WHERE id=?', (qid,)).fetchone()
            contract_no = row['contract_no'] if row else ''
        else:
            cur = conn.execute(
                'INSERT INTO quote(quote_date,project_name,contract_no,plan,seller,buyer,total)'
                " VALUES(?,?,?,?,?,?,?)",
                (quote['quote_date'], quote['project_name'], '', quote['plan'],
                 quote['seller'], quote['buyer'], quote['total']))
            qid = cur.lastrowid
            self.quote_id = qid
            contract_no = ''
        for it in items:
            conn.execute(
                'INSERT INTO quote_item(quote_id,seq,name,spec,code,price,unit,qty,total,remark)'
                ' VALUES(?,?,?,?,?,?,?,?,?,?)',
                (qid, it['seq'], it['name'], it['spec'], it['code'], it['price'],
                 it['unit'], it['qty'], it['total'], it['remark']))
            exists = conn.execute(
                'SELECT 1 FROM material WHERE name=? AND spec=? AND code=? AND unit=?'
                ' AND price=? AND qty=? AND date=? AND contract_no=?',
                (it['name'], it['spec'], it['code'], it['unit'], it['price'],
                 it['qty'], quote['quote_date'], contract_no)).fetchone()
            if not exists:
                conn.execute(
                    'INSERT INTO material(customer,name,spec,code,unit,price,qty,date,contract_no,total)'
                    ' VALUES(?,?,?,?,?,?,?,?,?,?)',
                    ('', it['name'], it['spec'], it['code'], it['unit'], it['price'],
                     it['qty'], quote['quote_date'], contract_no, it['total']))
        conn.commit()
        conn.close()
        if not quiet:
            QMessageBox.information(self, '完成', '报价单已保存')
            self.accept()
        return True

    def save_and_export(self):
        if not self.save(quiet=True):
            return
        conn = get_conn()
        quote = dict(conn.execute('SELECT * FROM quote WHERE id=?', (self.quote_id,)).fetchone())
        items = [dict(r) for r in conn.execute(
            'SELECT * FROM quote_item WHERE quote_id=? ORDER BY seq', (self.quote_id,)).fetchall()]
        conn.close()
        path, _ = QFileDialog.getSaveFileName(
            self, '导出报价单', '报价单_{}.xlsx'.format(quote['quote_date']), 'Excel (*.xlsx)')
        if not path:
            return
        try:
            export_quote(quote, items, path)
        except Exception as e:
            QMessageBox.critical(self, '导出失败', str(e))
            return
        QMessageBox.information(self, '完成', '已导出：\n' + path)
        self.accept()
