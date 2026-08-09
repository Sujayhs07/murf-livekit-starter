import sqlite3
import json
import os
import sys
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "dashboard.db")

def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Profile table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS profile (
            id INTEGER PRIMARY KEY DEFAULT 1,
            name TEXT,
            email TEXT,
            phone TEXT,
            is_logged_in INTEGER DEFAULT 1
        )
    """)
    
    # Insert default profile row if empty
    cursor.execute("SELECT COUNT(*) FROM profile")
    if cursor.fetchone()[0] == 0:
        cursor.execute("""
            INSERT INTO profile (id, name, email, phone, is_logged_in)
            VALUES (1, 'Jayesh Patel', 'jayesh.patel@gmail.com', '+91 98765 43210', 1)
        """)
        
    # Transactions table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            type TEXT,
            amount REAL,
            timestamp TEXT
        )
    """)
    
    conn.commit()
    conn.close()

def get_data():
    init_db()
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Profile
    cursor.execute("SELECT name, email, phone, is_logged_in FROM profile WHERE id = 1")
    prof = cursor.fetchone()
    profile = {
        "name": prof[0],
        "email": prof[1],
        "phone": prof[2],
        "is_logged_in": bool(prof[3])
    }
    
    # Transactions
    cursor.execute("SELECT id, type, amount, timestamp FROM transactions ORDER BY id DESC")
    txs = cursor.fetchall()
    tx_list = []
    balance = 12345
    
    for row in reversed(txs):
        if row[1] == 'add':
            balance += row[2]
        else:
            balance -= row[2]
            
    for row in txs:
        tx_list.append({
            "id": row[0],
            "type": row[1],
            "amount": row[2],
            "time": row[3]
        })
        
    conn.close()
    
    return {
        "profile": profile,
        "balance": balance,
        "transactions": tx_list
    }

def update_profile(name, email, phone, is_logged_in):
    init_db()
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE profile
        SET name = ?, email = ?, phone = ?, is_logged_in = ?
        WHERE id = 1
    """, (name, email, phone, 1 if is_logged_in else 0))
    conn.commit()
    conn.close()

def add_transaction(tx_type, amount):
    init_db()
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    timestamp = datetime.now().strftime("%H:%M:%S")
    cursor.execute("""
        INSERT INTO transactions (type, amount, timestamp)
        VALUES (?, ?, ?)
    """, (tx_type, float(amount), timestamp))
    conn.commit()
    conn.close()

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(json.dumps(get_data()))
        sys.exit(0)
        
    cmd = sys.argv[1]
    if cmd == "get":
        print(json.dumps(get_data()))
    elif cmd == "update_profile" and len(sys.argv) >= 6:
        # python db_dashboard.py update_profile name email phone is_logged_in
        update_profile(sys.argv[2], sys.argv[3], sys.argv[4], sys.argv[5].lower() == 'true')
        print(json.dumps({"status": "success"}))
    elif cmd == "add_transaction" and len(sys.argv) >= 4:
        # python db_dashboard.py add_transaction type amount
        add_transaction(sys.argv[2], sys.argv[3])
        print(json.dumps({"status": "success"}))
    else:
        print(json.dumps({"error": "invalid command"}))
