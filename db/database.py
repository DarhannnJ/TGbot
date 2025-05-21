import sqlite3

class DB:
    def __init__(self, db_path="transactions.db"):
        self.db_path = db_path
        self.init_db()

    def init_db(self):
        conn = sqlite3.connect(self.db_path)
        cur = conn.cursor()
        
        # Таблица переводов
        cur.execute("""
            CREATE TABLE IF NOT EXISTS transfers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                file_unique_id TEXT UNIQUE,
                serial_number TEXT UNIQUE,
                amount REAL NOT NULL,
                recipient TEXT NOT NULL,
                date TEXT NOT NULL
            )
        """)
        
        # Таблица кредитных заявок
        cur.execute("""
            CREATE TABLE IF NOT EXISTS credit_applications (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                amount REAL NOT NULL,
                term INTEGER NOT NULL,
                status TEXT DEFAULT 'pending'
            )
        """)
        conn.commit()
        conn.close()

    def add_transfer(self, user_id, file_unique_id, serial, amount, recipient, date):
        conn = sqlite3.connect(self.db_path)
        cur = conn.cursor()
        try:
            cur.execute(
                "INSERT INTO transfers (user_id, file_unique_id, serial_number, amount, recipient, date) "
                "VALUES (?, ?, ?, ?, ?, ?)",
                (user_id, file_unique_id, serial, amount, recipient, date)
            )
            conn.commit()
            return True
        except sqlite3.IntegrityError:
            return False
        finally:
            conn.close()

    def get_transactions(self, user_id):
        conn = sqlite3.connect(self.db_path)
        cur = conn.cursor()
        cur.execute(
            "SELECT date, amount, recipient, serial_number FROM transfers "
            "WHERE user_id = ? ORDER BY date DESC",
            (user_id,)
        )
        transactions = [
            {"date": row[0], "amount": row[1], "recipient": row[2], "serial": row[3]}
            for row in cur.fetchall()
        ]
        conn.close()
        return transactions

    def is_duplicate(self, file_unique_id, serial):
        conn = sqlite3.connect(self.db_path)
        cur = conn.cursor()
        cur.execute(
            "SELECT 1 FROM transfers WHERE file_unique_id = ? OR serial_number = ?",
            (file_unique_id, serial)
        )
        result = cur.fetchone()
        conn.close()
        return bool(result)

    def get_total_sum(self, user_id):
        conn = sqlite3.connect(self.db_path)
        cur = conn.cursor()
        cur.execute(
            "SELECT SUM(amount) FROM transfers WHERE user_id = ?",
            (user_id,)
        )
        total = cur.fetchone()[0] or 0.0
        conn.close()
        return total

    def check_credit_eligibility(self, user_id):
        transactions = self.get_transactions(user_id)
        rating = calculate_reliability(transactions)
        return len(transactions) >= 3 and rating >= 80

    def save_credit_application(self, user_id, amount, term):
        conn = sqlite3.connect(self.db_path)
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO credit_applications (user_id, amount, term) VALUES (?, ?, ?)",
            (user_id, amount, term)
        )
        conn.commit()
        conn.close()