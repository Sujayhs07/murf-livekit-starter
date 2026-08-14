import sqlite3
import json
import os
import sys
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "dashboard.db")

def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Drop profile table if exists since it is unnecessary
    cursor.execute("DROP TABLE IF EXISTS profile")
    
    # Transactions table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            type TEXT,
            amount REAL,
            timestamp TEXT
        )
    """)

    # Escalations table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS escalations (
            reference_id TEXT PRIMARY KEY,
            reason TEXT,
            summary TEXT,
            what_was_checked TEXT,
            urgency TEXT,
            language TEXT,
            preferred_followup TEXT,
            status TEXT,
            timestamp TEXT
        )
    """)

    # Calls table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS calls (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            call_id TEXT UNIQUE,
            started_at TEXT,
            ended_at TEXT,
            duration_seconds INTEGER,
            language TEXT,
            channel TEXT,
            outcome TEXT,
            failure_reason TEXT,
            success_reason TEXT,
            active_agent TEXT DEFAULT 'Dia',
            handoff_occurred INTEGER DEFAULT 0,
            handoff_count INTEGER DEFAULT 0,
            specialist_agent TEXT
        )
    """)
    
    # Ensure new columns exist in case calls table already exists
    cursor.execute("PRAGMA table_info(calls)")
    columns = [col[1] for col in cursor.fetchall()]
    if "active_agent" not in columns:
        cursor.execute("ALTER TABLE calls ADD COLUMN active_agent TEXT DEFAULT 'Dia'")
    if "handoff_occurred" not in columns:
        cursor.execute("ALTER TABLE calls ADD COLUMN handoff_occurred INTEGER DEFAULT 0")
    if "handoff_count" not in columns:
        cursor.execute("ALTER TABLE calls ADD COLUMN handoff_count INTEGER DEFAULT 0")
    if "specialist_agent" not in columns:
        cursor.execute("ALTER TABLE calls ADD COLUMN specialist_agent TEXT")
        
    conn.commit()
    conn.close()

def get_data():
    init_db()
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
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

    # Escalations
    cursor.execute("SELECT reference_id, reason, summary, what_was_checked, urgency, language, preferred_followup, status, timestamp FROM escalations ORDER BY timestamp DESC")
    esc_rows = cursor.fetchall()
    esc_list = []
    for row in esc_rows:
        esc_list.append({
            "reference_id": row[0],
            "reason": row[1],
            "summary": row[2],
            "what_was_checked": row[3],
            "urgency": row[4],
            "language": row[5],
            "preferred_followup": row[6],
            "status": row[7],
            "timestamp": row[8]
        })
        
    conn.close()
    
    return {
        "balance": balance,
        "transactions": tx_list,
        "escalations": esc_list
    }

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

def add_escalation(reference_id, reason, summary, what_was_checked, urgency, language, preferred_followup, status="OPEN"):
    init_db()
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    cursor.execute("""
        INSERT OR REPLACE INTO escalations (reference_id, reason, summary, what_was_checked, urgency, language, preferred_followup, status, timestamp)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (reference_id, reason, summary, what_was_checked, urgency, language, preferred_followup, status, timestamp))
    conn.commit()
    conn.close()

def add_call_start(call_id, language="English", channel="browser"):
    init_db()
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    started_at = datetime.now().isoformat()
    cursor.execute("""
        INSERT INTO calls (call_id, started_at, language, channel, outcome, active_agent, handoff_occurred, handoff_count)
        VALUES (?, ?, ?, ?, 'IN_PROGRESS', 'Dia', 0, 0)
    """, (call_id, started_at, language, channel))
    conn.commit()
    conn.close()

def record_handoff(call_id, to_agent, specialist_agent=None):
    init_db()
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE calls
        SET handoff_occurred = 1,
            handoff_count = handoff_count + 1,
            active_agent = ?,
            specialist_agent = COALESCE(?, specialist_agent)
        WHERE call_id = ?
    """, (to_agent, specialist_agent, call_id))
    conn.commit()
    conn.close()

def update_call_end(call_id, duration_seconds, outcome, language, failure_reason=None, success_reason=None):
    init_db()
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    ended_at = datetime.now().isoformat()
    cursor.execute("""
        UPDATE calls
        SET ended_at = ?, duration_seconds = ?, outcome = ?, language = ?, failure_reason = ?, success_reason = ?
        WHERE call_id = ?
    """, (ended_at, int(duration_seconds), outcome, language, failure_reason, success_reason, call_id))
    conn.commit()
    conn.close()

def get_analytics():
    init_db()
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM calls WHERE outcome IN ('SUCCESS', 'FAILED')")
    total_calls = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM calls WHERE outcome = 'SUCCESS'")
    successful_calls = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM calls WHERE outcome = 'FAILED'")
    failed_calls = cursor.fetchone()[0]
    
    # Handoff metrics
    cursor.execute("SELECT SUM(handoff_count) FROM calls")
    res_handoffs = cursor.fetchone()[0]
    total_handoffs = res_handoffs if res_handoffs is not None else 0
    
    cursor.execute("SELECT COUNT(*) FROM calls WHERE specialist_agent IS NOT NULL")
    specialist_handoffs = cursor.fetchone()[0]
    
    conn.close()
    return {
        "total_calls": total_calls,
        "successful_calls": successful_calls,
        "failed_calls": failed_calls,
        "total_handoffs": total_handoffs,
        "specialist_handoffs": specialist_handoffs
    }

def get_calls_history():
    init_db()
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT call_id, started_at, duration_seconds, language, channel, outcome, active_agent, handoff_occurred, specialist_agent
        FROM calls 
        WHERE outcome IN ('SUCCESS', 'FAILED')
        ORDER BY started_at DESC
    """)
    rows = cursor.fetchall()
    conn.close()
    history = []
    for r in rows:
        history.append({
            "call_id": r[0],
            "started_at": r[1],
            "duration_seconds": r[2],
            "language": r[3],
            "channel": r[4],
            "outcome": r[5],
            "active_agent": r[6],
            "handoff_occurred": r[7],
            "specialist_agent": r[8]
        })
    return history

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(json.dumps(get_data()))
        sys.exit(0)
        
    cmd = sys.argv[1]
    if cmd == "get":
        print(json.dumps(get_data()))
    elif cmd == "get_analytics":
        print(json.dumps(get_analytics()))
    elif cmd == "get_calls":
        print(json.dumps(get_calls_history()))
    elif cmd == "add_transaction" and len(sys.argv) >= 4:
        add_transaction(sys.argv[2], sys.argv[3])
        print(json.dumps({"status": "success"}))
    elif cmd == "add_escalation" and len(sys.argv) >= 9:
        status_val = sys.argv[9] if len(sys.argv) > 9 else "OPEN"
        add_escalation(sys.argv[2], sys.argv[3], sys.argv[4], sys.argv[5], sys.argv[6], sys.argv[7], sys.argv[8], status_val)
        print(json.dumps({"status": "success"}))
    else:
        print(json.dumps({"error": "invalid command"}))
