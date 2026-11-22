import sqlite3

for db_path in ['PBN-Dashboard-V2/pbn_matrix.db']:
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    cur.execute("SELECT id, name, type, host, username, password FROM servers WHERE type = 'cpanel' OR name LIKE '%cpanel%'")
    for r in cur.fetchall():
        pwd_masked = r[5][:3] + '***' + r[5][-3:] if r[5] else 'None'
        print(f"ID: {r[0]} | Name: {r[1]} | Host: {r[3]} | User: {r[4]} | Pass: {pwd_masked}")

