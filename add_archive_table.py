"""
Add archive table for tracking archived client-account pairs
"""

def migrate_up(connection):
    """
    Create the archive table with:
    - client_id (FK to clients)
    - account_id (FK to accounts)
    - archive_status (boolean)
    - Unique constraint on (client_id, account_id)
    """
    connection.execute("""
        CREATE TABLE IF NOT EXISTS archives (
            id SERIAL PRIMARY KEY,
            client_id INTEGER NOT NULL REFERENCES clients(id),
            account_id INTEGER NOT NULL REFERENCES accounts(id),
            archive_status BOOLEAN NOT NULL DEFAULT TRUE,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
            CONSTRAINT unique_client_account_archive UNIQUE(client_id, account_id)
        )
    """)
    connection.execute("CREATE INDEX idx_archives_client_id ON archives(client_id)")
    connection.execute("CREATE INDEX idx_archives_account_id ON archives(account_id)")
    connection.execute("CREATE INDEX idx_archives_status ON archives(archive_status)")
    print("Archive table created successfully")


def migrate_down(connection):
    """
    Drop the archive table
    """
    connection.execute("DROP TABLE IF EXISTS archives CASCADE")
    print("Archive table dropped successfully")


if __name__ == "__main__":
    from app.db.database import engine
    with engine.connect() as connection:
        migrate_up(connection)
        connection.commit()
