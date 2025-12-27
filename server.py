import sqlite3
from contextlib import contextmanager
from fastmcp import FastMCP
from pathlib import Path

mcp = FastMCP("Banking MCP Server")

DB_PATH = Path(__file__).parent / "db.sqlite"

@contextmanager
def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()

def init_db():
    with get_db() as conn:
        cursor = conn.cursor()
        
        # Accounts table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS accounts (
                account_id INTEGER PRIMARY KEY AUTOINCREMENT,
                account_name TEXT NOT NULL,
                balance REAL NOT NULL DEFAULT 0.0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Transactions table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS transactions (
                transaction_id INTEGER PRIMARY KEY AUTOINCREMENT,
                account_id INTEGER NOT NULL,
                transaction_type TEXT NOT NULL,
                amount REAL NOT NULL,
                balance_after REAL NOT NULL,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                description TEXT,
                FOREIGN KEY (account_id) REFERENCES accounts (account_id)
            )
        """)
        
        conn.commit()

# Initialize database
init_db()


@mcp.tool()
def create_account(account_name: str, initial_deposit: float = 0.0) -> str:
    """Create a new bank account with an optional initial deposit.
    
    Args:
        account_name: Name for the account holder
        initial_deposit: Initial deposit amount (defaults to 0)
    
    Returns:
        Success message with account details
    """
    if initial_deposit < 0:
        return "Error: Initial deposit cannot be negative"
    
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO accounts (account_name, balance) VALUES (?, ?)",
            (account_name, initial_deposit)
        )
        account_id = cursor.lastrowid
        
        if initial_deposit > 0:
            cursor.execute(
                """INSERT INTO transactions 
                   (account_id, transaction_type, amount, balance_after, description)
                   VALUES (?, ?, ?, ?, ?)""",
                (account_id, "DEPOSIT", initial_deposit, 
                 initial_deposit, "Initial deposit")
            )
        
        conn.commit()
        
        return (f"Account created successfully!\n"
                f"Account ID: {account_id}\n"
                f"Account Name: {account_name}\n"
                f"Initial Balance: ${initial_deposit:.2f}")

@mcp.tool()
def deposit(account_id: int, amount: float, description: str = None) -> str:
    """Deposit money into an existing account.
    
    Args:
        account_id: The account ID to deposit into
        amount: Amount to deposit (must be positive)
        description: Optional description for the transaction
    
    Returns:
        Success message with new balance
    """
    if amount <= 0:
        return "Error: Deposit amount must be positive"
    
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM accounts WHERE account_id = ?", 
                      (account_id,))
        account = cursor.fetchone()
        
        if not account:
            return f"Error: Account {account_id} not found"
        
        new_balance = account["balance"] + amount
        
        cursor.execute(
            "UPDATE accounts SET balance = ? WHERE account_id = ?",
            (new_balance, account_id)
        )
        
        cursor.execute(
            """INSERT INTO transactions 
               (account_id, transaction_type, amount, balance_after, description)
               VALUES (?, ?, ?, ?, ?)""",
            (account_id, "DEPOSIT", amount, new_balance, description)
        )
        
        conn.commit()
        
        return (f"Deposit successful!\n"
                f"Account ID: {account_id}\n"
                f"Amount Deposited: ${amount:.2f}\n"
                f"New Balance: ${new_balance:.2f}")

@mcp.tool()
def withdraw(account_id: int, amount: float, description: str = None) -> str:
    """Withdraw money from an existing account.
    
    Args:
        account_id: The account ID to withdraw from
        amount: Amount to withdraw (must be positive)
        description: Optional description for the transaction
    
    Returns:
        Success message with new balance
    """
    if amount <= 0:
        return "Error: Withdrawal amount must be positive"
    
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM accounts WHERE account_id = ?", 
                      (account_id,))
        account = cursor.fetchone()
        
        if not account:
            return f"Error: Account {account_id} not found"
        
        if account["balance"] < amount:
            return (f"Error: Insufficient funds\n"
                   f"Current Balance: ${account['balance']:.2f}\n"
                   f"Requested Withdrawal: ${amount:.2f}")
        
        new_balance = account["balance"] - amount
        
        cursor.execute(
            "UPDATE accounts SET balance = ? WHERE account_id = ?",
            (new_balance, account_id)
        )
        
        cursor.execute(
            """INSERT INTO transactions 
               (account_id, transaction_type, amount, balance_after, description)
               VALUES (?, ?, ?, ?, ?)""",
            (account_id, "WITHDRAWAL", amount, new_balance, description)
        )
        
        conn.commit()
        
        return (f"Withdrawal successful!\n"
                f"Account ID: {account_id}\n"
                f"Amount Withdrawn: ${amount:.2f}\n"
                f"New Balance: ${new_balance:.2f}")

@mcp.tool()
def get_balance(account_id: int) -> str:
    """Get the current balance of an account.
    
    Args:
        account_id: The account ID to check
    
    Returns:
        Account balance information
    """
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM accounts WHERE account_id = ?", 
                      (account_id,))
        account = cursor.fetchone()
        
        if not account:
            return f"Error: Account {account_id} not found"
        
        return (f"Account Balance:\n"
                f"Account ID: {account['account_id']}\n"
                f"Account Name: {account['account_name']}\n"
                f"Balance: ${account['balance']:.2f}\n"
                f"Created: {account['created_at']}")

@mcp.tool()
def get_transaction_history(account_id: int, limit: int = 10) -> str:
    """Get transaction history for an account.
    
    Args:
        account_id: The account ID to get history for
        limit: Maximum number of transactions to return (default 10)
    
    Returns:
        List of recent transactions
    """
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM accounts WHERE account_id = ?", 
                      (account_id,))
        if not cursor.fetchone():
            return f"Error: Account {account_id} not found"
        
        cursor.execute(
            """SELECT * FROM transactions 
               WHERE account_id = ? 
               ORDER BY timestamp DESC 
               LIMIT ?""",
            (account_id, limit)
        )
        
        transactions = cursor.fetchall()
        
        if not transactions:
            return f"No transactions found for account {account_id}"
        
        result = f"Transaction History for Account {account_id}:\n\n"
        for tx in transactions:
            result += f"ID: {tx['transaction_id']} | "
            result += f"{tx['transaction_type']} | "
            result += f"${tx['amount']:.2f} | "
            result += f"Balance After: ${tx['balance_after']:.2f} | "
            result += f"{tx['timestamp']}"
            if tx['description']:
                result += f" | {tx['description']}"
            result += "\n"
        
        return result

@mcp.tool()
def list_accounts() -> str:
    """List all bank accounts in the system.
    
    Returns:
        List of all accounts with their details
    """
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM accounts ORDER BY account_id")
        accounts = cursor.fetchall()
        
        if not accounts:
            return "No accounts found in the system"
        
        result = "All Bank Accounts:\n\n"
        for acc in accounts:
            result += f"ID: {acc['account_id']} | "
            result += f"Name: {acc['account_name']} | "
            result += f"Balance: ${acc['balance']:.2f} | "
            result += f"Created: {acc['created_at']}\n"
        
        return result

if __name__ == "__main__":
    mcp.run(transport="streamable-http", host="127.0.0.1", port=8000)