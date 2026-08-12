import sqlite3
import json
import os
import sys
import io

if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8")


DB_CALLERS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "callers.db")
DB_DASHBOARD = os.path.join(os.path.dirname(os.path.abspath(__file__)), "dashboard.db")


def execute_query(db_path, query, params=(), fetch=False, commit=True):
    if not os.path.exists(db_path):
        print(
            f"Database {os.path.basename(db_path)} does not exist yet. Please run the app or a tool first."
        )
        return None
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    try:
        cursor.execute(query, params)
        if commit:
            conn.commit()
        if fetch:
            return cursor.fetchall()
    except Exception as e:
        print("SQL Error:", e)
    finally:
        conn.close()
    return None


def show_help():
    print("""
Finora AI Database Utility CLI
------------------------------
Usage:
  python src/db_util.py <command> [args]

Commands for Callers Memory (callers.db):
  show-callers                     Show all returning voice assistant profiles
  clear-callers                    Clear all returning voice assistant profiles
  delete-caller <name>             Delete a specific caller profile by name

Commands for Frontend Dashboard (dashboard.db):
  show-dashboard                   Show current transaction balance
  clear-transactions               Clear all transactions (resets balance to default 12,345)
  set-balance <amount>             Set a clean custom balance in the dashboard
""")


def main():
    if len(sys.argv) < 2:
        show_help()
        sys.exit(0)

    cmd = sys.argv[1]

    if cmd == "show-callers":
        rows = execute_query(
            DB_CALLERS,
            "SELECT user_id, name, language_preference, facts, last_interaction FROM callers",
            fetch=True,
        )
        if rows:
            print(f"\n--- Returning Callers ({len(rows)} records) ---")
            for r in rows:
                print(f"ID: {r[0]}")
                print(f"Name: {r[1]}")
                print(f"Language: {r[2]}")
                print(f"Facts: {r[3]}")
                print(f"Last Seen: {r[4]}")
                print("-" * 40)
        else:
            print("No voice assistant caller profiles found.")

    elif cmd == "clear-callers":
        execute_query(DB_CALLERS, "DELETE FROM callers")
        print("Cleared all voice assistant caller memory.")

    elif cmd == "delete-caller":
        if len(sys.argv) < 3:
            print(
                "Please specify caller name. Example: python src/db_util.py delete-caller Ramesh"
            )
            sys.exit(1)
        name = sys.argv[2]
        execute_query(
            DB_CALLERS, "DELETE FROM callers WHERE LOWER(name) = LOWER(?)", (name,)
        )
        print(f"Deleted caller '{name}' from memory.")

    elif cmd == "show-dashboard":
        txs = execute_query(
            DB_DASHBOARD,
            "SELECT id, type, amount, timestamp FROM transactions",
            fetch=True,
        )
        balance = 12345
        if txs:
            print(f"\n--- Dashboard Transactions ({len(txs)} records) ---")
            for t in txs:
                print(
                    f"  [{t[3]}] {'Deposit' if t[1] == 'add' else 'Withdrawal'}: ₹{t[2]}"
                )
                if t[1] == "add":
                    balance += t[2]
                else:
                    balance -= t[2]
            print(f"\nCalculated Current Balance: ₹{balance:,}")
        else:
            print("\nNo transaction history. Balance is at default ₹12,345")

    elif cmd == "clear-transactions":
        execute_query(DB_DASHBOARD, "DELETE FROM transactions")
        print("Cleared all transaction records from the dashboard database.")

    elif cmd == "set-balance":
        if len(sys.argv) < 3:
            print(
                "Please specify target balance. Example: python src/db_util.py set-balance 50000"
            )
            sys.exit(1)
        try:
            target = float(sys.argv[2])
            # Reset transactions first
            execute_query(DB_DASHBOARD, "DELETE FROM transactions")
            # Create a single transaction matching the difference from baseline (12345)
            diff = target - 12345
            if diff != 0:
                tx_type = "add" if diff > 0 else "withdraw"
                execute_query(
                    DB_DASHBOARD,
                    "INSERT INTO transactions (type, amount, timestamp) VALUES (?, ?, '00:00:00')",
                    (tx_type, abs(diff)),
                )
            print(f"Successfully set dashboard balance to ₹{target:,}")
        except ValueError:
            print("Please provide a valid numeric value.")

    # update-profile removed

    else:
        print(f"Unknown command: {cmd}")
        show_help()


if __name__ == "__main__":
    main()
