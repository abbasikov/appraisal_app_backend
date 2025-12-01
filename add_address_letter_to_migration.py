"""
Database migration to add address_letter_to column to projects table
"""
from sqlalchemy import text
from app.db.database import engine

def upgrade():
    """Add address_letter_to column"""
    with engine.connect() as conn:
        conn.execute(text("""
            ALTER TABLE projects 
            ADD COLUMN IF NOT EXISTS address_letter_to VARCHAR
        """))
        conn.commit()
    print("✅ Added address_letter_to column to projects table")

def downgrade():
    """Remove address_letter_to column"""
    with engine.connect() as conn:
        conn.execute(text("""
            ALTER TABLE projects 
            DROP COLUMN IF EXISTS address_letter_to
        """))
        conn.commit()
    print("✅ Removed address_letter_to column from projects table")

if __name__ == "__main__":
    print("Running migration: add address_letter_to column")
    upgrade()
    print("Migration complete!")
