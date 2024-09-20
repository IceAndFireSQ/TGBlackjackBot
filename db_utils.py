import sqlite3

def connect_db():
    conn = sqlite3.connect('blackjack.db')
    return conn

def create_tables():
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS balances (
            user_id INTEGER PRIMARY KEY,
            balance REAL DEFAULT 0
        )
    ''')
    conn.commit()
    conn.close()

def get_balance(user_id):
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute('SELECT balance FROM balances WHERE user_id = ?', (user_id,))
    balance = cursor.fetchone()
    conn.close()
    return balance[0] if balance else 0

def update_balance(user_id, amount):
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute('INSERT INTO balances (user_id, balance) VALUES (?, ?) ON CONFLICT(user_id) DO UPDATE SET balance = balance + ?',
                   (user_id, amount, amount))
    conn.commit()
    conn.close()

if __name__ == '__main__':
    create_tables()
