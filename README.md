# SQL-MCP Banking Server

A lightweight banking MCP server built with [`fastmcp`](https://pypi.org/project/fastmcp/) and SQLite. It exposes account and transaction tools via [`FastMCP`](server.py) in [server.py](server.py).

## Requirements

- Python 3.11+
- `fastmcp` (installed automatically below)

## Setup

```sh
python -m venv .venv
source .venv/bin/activate    # On Windows: .venv\Scripts\activate
pip install -e .
```

If you prefer without editable mode:

```sh
pip install fastmcp
```

## Run the server

```sh
python server.py
```

The SQLite database `banking.db` is created and seeded automatically by [`init_db`](server.py#L13). The server listens on `127.0.0.1:8000` using the `streamable-http` transport.

## Available MCP tools

- [`create_account`](server.py#L31): Create a new account with an optional initial deposit.
- [`deposit`](server.py#L65): Deposit funds into an account.
- [`withdraw`](server.py#L103): Withdraw funds with balance checks.
- [`get_balance`](server.py#L144): Retrieve account balance and metadata.
- [`get_transaction_history`](server.py#L171): Fetch recent transactions (default limit 10).
- [`list_accounts`](server.py#L213): List all accounts with balances and creation timestamps.

## Data model

- **accounts**: `account_id`, `account_name`, `balance`, `created_at`.
- **transactions**: `transaction_id`, `account_id`, `transaction_type`, `amount`, `balance_after`, `timestamp`, `description`.

## Notes

- All tools share a SQLite connection via [`get_db`](server.py#L17).
- Transactions are recorded automatically for deposits and withdrawals.
- To reset the database, delete `banking.db` and restart the server.
