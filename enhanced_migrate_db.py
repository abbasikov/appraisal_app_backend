#!/usr/bin/env python3
"""
Enhanced database migration script to sync schema with requirements
"""

from sqlalchemy import create_engine, text, inspect
from app.core.config import settings
from app.db.init_db import create_tables

def check_column_exists(engine, table_name, column_name):
    """Check if a column exists in a table"""
    inspector = inspect(engine)
    columns = [col['name'] for col in inspector.get_columns(table_name)]
    return column_name in columns

def check_table_exists(engine, table_name):
    """Check if a table exists"""
    inspector = inspect(engine)
    return table_name in inspector.get_table_names()

def migrate_database():
    """Enhanced migration to sync database with requirements"""
    engine = create_engine(settings.DATABASE_URL)
    
    print("🔄 Starting enhanced database migration...")
    
    # Create all tables first
    print("🏗️  Creating missing tables...")
    create_tables()
    
    with engine.connect() as conn:
        try:
            # Users table enhancements
            if check_table_exists(engine, 'users'):
                print("📝 Enhancing users table...")
                
                # Add missing columns if they don't exist
                if not check_column_exists(engine, 'users', 'is_email_verified'):
                    conn.execute(text("""
                        ALTER TABLE users 
                        ADD COLUMN is_email_verified BOOLEAN DEFAULT FALSE
                    """))
                    print("  ✅ Added is_email_verified column")
                
                if not check_column_exists(engine, 'users', 'is_active'):
                    conn.execute(text("""
                        ALTER TABLE users 
                        ADD COLUMN is_active BOOLEAN DEFAULT TRUE
                    """))
                    print("  ✅ Added is_active column")
                
                # Update existing users to have verified emails for backward compatibility
                conn.execute(text("""
                    UPDATE users 
                    SET is_email_verified = TRUE 
                    WHERE role = 'admin' AND (is_email_verified IS NULL OR is_email_verified = FALSE)
                """))
                print("  ✅ Set admin users as email verified")
            
            # Properties table enhancements
            if check_table_exists(engine, 'properties'):
                print("📝 Enhancing properties table...")
                
                if not check_column_exists(engine, 'properties', 'owner_name'):
                    conn.execute(text("""
                        ALTER TABLE properties 
                        ADD COLUMN owner_name VARCHAR
                    """))
                    print("  ✅ Added owner_name column")
                
                if not check_column_exists(engine, 'properties', 'owner_phone'):
                    conn.execute(text("""
                        ALTER TABLE properties 
                        ADD COLUMN owner_phone VARCHAR
                    """))
                    print("  ✅ Added owner_phone column")
                
                if not check_column_exists(engine, 'properties', 'owner_email'):
                    conn.execute(text("""
                        ALTER TABLE properties 
                        ADD COLUMN owner_email VARCHAR
                    """))
                    print("  ✅ Added owner_email column")
            
            # Appraisals table enhancements
            if check_table_exists(engine, 'appraisals'):
                print("📝 Enhancing appraisals table...")
                
                if not check_column_exists(engine, 'appraisals', 'inspection_date'):
                    conn.execute(text("""
                        ALTER TABLE appraisals 
                        ADD COLUMN inspection_date DATE
                    """))
                    print("  ✅ Added inspection_date column")
                
                if not check_column_exists(engine, 'appraisals', 'report_date'):
                    conn.execute(text("""
                        ALTER TABLE appraisals 
                        ADD COLUMN report_date DATE
                    """))
                    print("  ✅ Added report_date column")
                
                if not check_column_exists(engine, 'appraisals', 'intended_use'):
                    conn.execute(text("""
                        ALTER TABLE appraisals 
                        ADD COLUMN intended_use VARCHAR
                    """))
                    print("  ✅ Added intended_use column")
                
                if not check_column_exists(engine, 'appraisals', 'property_rights'):
                    conn.execute(text("""
                        ALTER TABLE appraisals 
                        ADD COLUMN property_rights VARCHAR DEFAULT 'Fee Simple'
                    """))
                    print("  ✅ Added property_rights column")
            
            # Form templates enhancements
            if check_table_exists(engine, 'form_templates'):
                print("📝 Enhancing form_templates table...")
                
                if not check_column_exists(engine, 'form_templates', 'description'):
                    conn.execute(text("""
                        ALTER TABLE form_templates 
                        ADD COLUMN description TEXT
                    """))
                    print("  ✅ Added description column")
                
                if not check_column_exists(engine, 'form_templates', 'category'):
                    conn.execute(text("""
                        ALTER TABLE form_templates 
                        ADD COLUMN category VARCHAR DEFAULT 'General'
                    """))
                    print("  ✅ Added category column")
            
            # Create indexes for better performance
            print("📝 Creating database indexes...")
            
            # Users indexes
            conn.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_users_email ON users(email)
            """))
            conn.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_users_role ON users(role)
            """))
            
            # Appraisals indexes
            conn.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_appraisals_status ON appraisals(status)
            """))
            conn.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_appraisals_appraiser ON appraisals(appraiser_id)
            """))
            conn.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_appraisals_client ON appraisals(client_id)
            """))
            conn.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_appraisals_property ON appraisals(property_id)
            """))
            
            # Properties indexes
            conn.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_properties_type ON properties(property_type)
            """))
            conn.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_properties_location ON properties(city, state)
            """))
            
            # Verification codes indexes
            conn.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_verification_codes_email ON verification_codes(email)
            """))
            conn.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_verification_codes_type ON verification_codes(code_type)
            """))
            
            print("  ✅ Database indexes created")
            
            conn.commit()
            print("✅ Enhanced database migration completed successfully!")
            
        except Exception as e:
            print(f"❌ Error during migration: {e}")
            conn.rollback()
            raise

def verify_schema():
    """Verify the database schema matches requirements"""
    engine = create_engine(settings.DATABASE_URL)
    inspector = inspect(engine)
    
    print("\n🔍 Verifying database schema...")
    
    required_tables = [
        'users', 'verification_codes', 'properties', 'appraisals',
        'comparable_sales', 'property_photos', 'reports', 
        'form_templates', 'form_fields'
    ]
    
    existing_tables = inspector.get_table_names()
    
    for table in required_tables:
        if table in existing_tables:
            print(f"  ✅ Table '{table}' exists")
            
            # Check key columns for each table
            columns = [col['name'] for col in inspector.get_columns(table)]
            
            if table == 'users':
                required_cols = ['id', 'username', 'email', 'role', 'is_email_verified']
                for col in required_cols:
                    if col in columns:
                        print(f"    ✅ Column '{col}' exists")
                    else:
                        print(f"    ❌ Column '{col}' missing")
            
            elif table == 'appraisals':
                required_cols = ['id', 'property_id', 'appraiser_id', 'client_id', 'status']
                for col in required_cols:
                    if col in columns:
                        print(f"    ✅ Column '{col}' exists")
                    else:
                        print(f"    ❌ Column '{col}' missing")
        else:
            print(f"  ❌ Table '{table}' missing")
    
    print("✅ Schema verification completed!")

if __name__ == "__main__":
    migrate_database()
    verify_schema()