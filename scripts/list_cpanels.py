import sqlite3

for db_path in ['PBN-Dashboard-V2/pbn_matrix.db', 'PBN-Dashboard/server/pbn_matrix.db']:
    try:
        conn = sqlite3.connect(db_path)
        cur = conn.cursor()
        print('=== DB:', db_path)
        cur.execute("SELECT id, name, type, host, username, password FROM servers WHERE type = 'cpanel' OR name LIKE '%cpanel%'")
        for r in cur.fetchall():
            print(f"ID: {r[0]} | Name: {r[1]} | Type: {r[2]} | Host: {r[3]} | User: {r[4]}")
    except Exception as e:
        print(f"Error {db_path}: {e}")

