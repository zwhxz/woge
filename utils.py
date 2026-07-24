import re

_PARTY_KEYS = ('法定代表人', '地址', '开户银行', '帐　　号', '账　　号',
               '帐号', '账号', '电　　话', '电话', '传    真', '传真')
_PARTY_RE = re.compile(r'(?<=[^\n])(?=' + '|'.join(_PARTY_KEYS) + ')')


def normalize_party_info(text):
    if not text:
        return text
    return _PARTY_RE.sub('\n', text)


def rmb_upper(amount):
    try:
        amount = float(amount)
    except (TypeError, ValueError):
        return ''
    negative = amount < 0
    amount = round(abs(amount), 2)
    digit = '零壹贰叁肆伍陆柒捌玖'
    unit_int = ['', '拾', '佰', '仟']
    unit_grp = ['', '万', '亿', '万亿']
    integer = int(amount)
    cents = int(round((amount - integer) * 100))
    jiao, fen = divmod(cents, 10)
    int_str = ''
    if integer:
        s = str(integer)
        groups = []
        while s:
            groups.insert(0, s[-4:])
            s = s[:-4]
        prev_empty = False
        for gi, g in enumerate(groups):
            grp_unit = unit_grp[len(groups) - 1 - gi]
            seg = ''
            zero_pending = False
            for i, ch in enumerate(g):
                n = int(ch)
                pos = len(g) - 1 - i
                if n == 0:
                    zero_pending = True
                else:
                    if zero_pending and seg:
                        seg += '零'
                    seg += digit[n] + unit_int[pos]
                    zero_pending = False
            if seg:
                if prev_empty and int_str:
                    int_str += '零'
                int_str += seg + grp_unit
                prev_empty = False
            else:
                prev_empty = True
    out = '负' if negative else ''
    if integer:
        out += int_str + '元'
    if jiao == 0 and fen == 0:
        if integer:
            out += '整'
        else:
            out += '零元整'
    else:
        if jiao:
            out += digit[jiao] + '角'
        elif integer and fen:
            out += '零'
        if fen:
            out += digit[fen] + '分'
    return out


def fmt_money(v):
    try:
        return '{:,.2f}'.format(float(v))
    except (TypeError, ValueError):
        return '0.00'


def normalize_date(s):
    s = (s or '').strip().replace('/', '-').replace('.', '-')
    parts = s.split('-')
    if len(parts) == 3 and all(p.isdigit() for p in parts):
        y, m, d = parts
        return '{}-{:02d}-{:02d}'.format(y, int(m), int(d))
    return s


def to_float(v, default=0.0):
    if v is None:
        return default
    if isinstance(v, (int, float)):
        return float(v)
    s = str(v).strip().replace(',', '')
    if not s:
        return default
    try:
        return float(s)
    except ValueError:
        return default
