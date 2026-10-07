from app.db import get_db_connection

conn = get_db_connection()

if conn:
    cursor = conn.cursor()

    cursor.execute("""
        SELECT ma_danh_muc, ten_danh_muc
        FROM danh_muc
    """)

    rows = cursor.fetchall()

    print("Du lieu danh muc:")

    for row in rows:
        print(row)

    conn.close()
else:
    print("Khong the ket noi database.")