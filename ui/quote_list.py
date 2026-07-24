from PyQt5.QtCore import Qt, QDate
from PyQt5.QtWidgets import (QComboBox, QDateEdit, QFileDialog, QHBoxLayout,
                             QHeaderView, QInputDialog, QLabel, QLineEdit,
                             QMessageBox, QPushButton, QTableWidget,
                             QTableWidgetItem, QVBoxLayout, QWidget)

from db import get_conn
from export_excel import export_quote
from utils import fmt_money


class QuoteListWidget(QWidget):
    def __init__(self):
        super().__init__()
        lay = QVBoxLayout(self)

        bar = QHBoxLayout()
        self.f_from = QDateEdit(QDate.currentDate().addYears(-1))
        self.f_from.setCalendarPopup(True)
        self.f_from.setDisplayFormat('yyyy-MM-dd')
        self.f_to = QDateEdit(QDate.currentDate())
        self.f_to.setCalendarPopup(True)
        self.f_to.setDisplayFormat('yyyy-MM-dd')
        self.f_status = QComboBox()
        self.f_status.addItems(['全部', '已成交', '未成交'])
        self.f_project = QLineEdit()
        self.f_project.setPlaceholderText('项目名称')
        btn_search = QPushButton('查询')
        btn_search.clicked.connect(self.reload)
        btn_new = QPushButton('新增报价单')
        btn_new.clicked.connect(self.new_quote)
        for w in [QLabel('报价日期'), self.f_from, QLabel('至'), self.f_to,
                  QLabel('是否成交'), self.f_status, self.f_project, btn_search]:
            bar.addWidget(w)
        bar.addStretch()
        bar.addWidget(btn_new)
        lay.addLayout(bar)

        self.table = QTableWidget(0, 6)
        self.table.setHorizontalHeaderLabels(
            ['报价日期', '项目名称', '报价合计', '合同号', '是否成交', '操作'])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        lay.addWidget(self.table)
        self.reload()

    def reload(self):
        sql = 'SELECT * FROM quote WHERE quote_date BETWEEN ? AND ?'
        args = [self.f_from.date().toString('yyyy-MM-dd'),
                self.f_to.date().toString('yyyy-MM-dd')]
        st = self.f_status.currentText()
        if st == '已成交':
            sql += " AND contract_no != ''"
        elif st == '未成交':
            sql += " AND contract_no = ''"
        if self.f_project.text().strip():
            sql += ' AND project_name LIKE ?'
            args.append('%' + self.f_project.text().strip() + '%')
        sql += ' ORDER BY quote_date DESC, id DESC'
        conn = get_conn()
        rows = conn.execute(sql, args).fetchall()
        conn.close()
        self.table.setRowCount(0)
        self.table.setRowCount(len(rows))
        for i, r in enumerate(rows):
            qid = r['id']
            done = bool(r['contract_no'])
            for j, v in enumerate([r['quote_date'], r['project_name'],
                                   fmt_money(r['total']), r['contract_no'],
                                   '已成交' if done else '未成交']):
                self.table.setItem(i, j, QTableWidgetItem(str(v)))
            cell = QWidget()
            h = QHBoxLayout(cell)
            h.setContentsMargins(2, 2, 2, 2)
            b_contract = QPushButton('合同号录入/编辑')
            b_contract.clicked.connect(lambda _, q=qid, c=r['contract_no']: self.edit_contract(q, c))
            b_copy = QPushButton('复制新增')
            b_copy.clicked.connect(lambda _, q=qid: self.copy_quote(q))
            b_edit = QPushButton('编辑')
            b_edit.clicked.connect(lambda _, q=qid: self.edit_quote(q))
            b_export = QPushButton('导出')
            b_export.clicked.connect(lambda _, q=qid: self.export_quote(q))
            b_del = QPushButton('删除')
            b_del.clicked.connect(lambda _, q=qid: self.delete_quote(q))
            for b in [b_contract, b_copy, b_edit, b_export, b_del]:
                h.addWidget(b)
            self.table.setCellWidget(i, 5, cell)
            self.table.setRowHeight(i, 34)

    def edit_contract(self, qid, current):
        text, ok = QInputDialog.getText(self, '合同号录入/编辑', '合同号：', text=current or '')
        if ok:
            text = text.strip()
            conn = get_conn()
            conn.execute('UPDATE quote SET contract_no=? WHERE id=?', (text, qid))
            q = conn.execute('SELECT quote_date FROM quote WHERE id=?', (qid,)).fetchone()
            if q and text:
                items = conn.execute(
                    'SELECT name, code FROM quote_item WHERE quote_id=?', (qid,)).fetchall()
                for it in items:
                    conn.execute(
                        "UPDATE material SET contract_no=? WHERE contract_no=''"
                        ' AND date=? AND name=? AND code=?',
                        (text, q['quote_date'], it['name'], it['code']))
            conn.commit()
            conn.close()
            self.reload()

    def new_quote(self):
        from ui.quote_edit import QuoteEditDialog
        dlg = QuoteEditDialog(self)
        if dlg.exec_():
            self.reload()

    def edit_quote(self, qid):
        from ui.quote_edit import QuoteEditDialog
        dlg = QuoteEditDialog(self, quote_id=qid)
        if dlg.exec_():
            self.reload()

    def copy_quote(self, qid):
        from ui.quote_edit import QuoteEditDialog
        dlg = QuoteEditDialog(self, copy_from=qid)
        if dlg.exec_():
            self.reload()

    def delete_quote(self, qid):
        if QMessageBox.question(self, '确认', '确定删除该报价单？') != QMessageBox.Yes:
            return
        conn = get_conn()
        conn.execute('DELETE FROM quote_item WHERE quote_id=?', (qid,))
        conn.execute('DELETE FROM quote WHERE id=?', (qid,))
        conn.commit()
        conn.close()
        self.reload()

    def export_quote(self, qid):
        conn = get_conn()
        quote = dict(conn.execute('SELECT * FROM quote WHERE id=?', (qid,)).fetchone())
        items = [dict(r) for r in conn.execute(
            'SELECT * FROM quote_item WHERE quote_id=? ORDER BY seq', (qid,)).fetchall()]
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
