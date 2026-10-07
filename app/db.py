import pyodbc


def get_db_connection():
    try:
        conn = pyodbc.connect(
            "DRIVER={ODBC Driver 18 for SQL Server};"
            "SERVER=(local);"
            "DATABASE=quan_ly_giay_dep;"
            "Trusted_Connection=yes;"
            "TrustServerCertificate=yes;"
        )

        print("Kết nối SQL Server thành công!")
        return conn

    except pyodbc.Error as e:
        print("Lỗi kết nối SQL Server:", e)
        return None