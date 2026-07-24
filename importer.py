import csv

from utils import normalize_date, to_float

HEADER_MAP = {
    '签单日期': 'date',
    '销售合同号': 'contract_no',
    '客户': 'customer',
    '物料名称': 'name',
    '规格型号': 'spec',
    '物料编码': 'code',
    '销售单位': 'unit',
    '销售数量': 'qty',
    '单价': 'price',
    '价税合计': 'total',
    '价税合计（本位币）': 'total',
    '价税合计(本位币)': 'total',
}


def _norm_header(h):
    return ''.join(str(h or '').split())


def _map_headers(header_row):
    mapping = {}
    for idx, h in enumerate(header_row):
        key = HEADER_MAP.get(_norm_header(h))
        if key and key not in mapping.values():
            mapping[idx] = key
    return mapping


def _row_to_material(mapping, row):
    def get(idx):
        return row[idx] if idx < len(row) else ''
    m = {'customer': '', 'name': '', 'spec': '', 'code': '', 'unit': '',
         'price': 0.0, 'qty': 0.0, 'date': '', 'contract_no': '', 'total': 0.0}
    for idx, field in mapping.items():
        val = get(idx)
        if isinstance(val, str):
            val = val.strip()
        if field in ('price', 'qty', 'total'):
            m[field] = to_float(val)
        else:
            m[field] = '' if val is None else str(val)
    m['date'] = normalize_date(m['date'])
    if not m['total'] and m['price'] and m['qty']:
        m['total'] = round(m['price'] * m['qty'], 2)
    return m


def parse_csv(path):
    rows = []
    for enc in ('utf-8-sig', 'gbk'):
        try:
            with open(path, 'r', encoding=enc, newline='') as f:
                reader = csv.reader(f)
                all_rows = [r for r in reader if any(str(c).strip() for c in r)]
            break
        except UnicodeDecodeError:
            continue
    else:
        raise ValueError('无法识别CSV文件编码')
    if not all_rows:
        return rows
    mapping = _map_headers(all_rows[0])
    if 'name' not in mapping.values():
        raise ValueError('未找到"物料名称"列，请使用附件01模版')
    for r in all_rows[1:]:
        m = _row_to_material(mapping, r)
        if m['name'] or m['code']:
            rows.append(m)
    return rows


def parse_xlsx(path):
    import openpyxl
    wb = openpyxl.load_workbook(path, read_only=True, data_only=True)
    ws = wb.active
    all_rows = [[c for c in row] for row in ws.iter_rows(values_only=True)]
    wb.close()
    all_rows = [r for r in all_rows if any(str(c).strip() for c in r if c is not None)]
    if not all_rows:
        return []
    mapping = _map_headers(all_rows[0])
    if 'name' not in mapping.values():
        raise ValueError('未找到"物料名称"列，请使用附件01模版')
    rows = []
    for r in all_rows[1:]:
        m = _row_to_material(mapping, r)
        if m['name'] or m['code']:
            rows.append(m)
    return rows


def parse_material_file(path):
    lower = path.lower()
    if lower.endswith('.csv'):
        return parse_csv(path)
    if lower.endswith(('.xlsx', '.xlsm')):
        return parse_xlsx(path)
    raise ValueError('仅支持 .csv 或 .xlsx 文件')
