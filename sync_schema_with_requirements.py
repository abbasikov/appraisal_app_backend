#!/usr/bin/env python3
"""
Database schema sync based on the 21-day project requirements
"""

from sqlalchemy import create_engine, text, inspect
from app.core.config import settings

def sync_database_schema():
    """Sync database schema with the actual project requirements"""
    engine = create_engine(settings.DATABASE_URL)
    
    print("🔄 Syncing database schema with project requirements...")
    
    with engine.connect() as conn:
        try:
            # 1. Users table (Admin, Editor, Reader roles + OTP MFA)
            print("📝 Creating/updating Users table...")
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS users (
                    id SERIAL PRIMARY KEY,
                    username VARCHAR UNIQUE NOT NULL,
                    email VARCHAR UNIQUE NOT NULL,
                    password_hash VARCHAR NOT NULL,
                    first_name VARCHAR NOT NULL,
                    last_name VARCHAR NOT NULL,
                    phone VARCHAR,
                    role VARCHAR NOT NULL DEFAULT 'reader' CHECK (role IN ('admin', 'editor', 'reader')),
                    is_active BOOLEAN DEFAULT TRUE,
                    otp_secret VARCHAR,
                    otp_enabled BOOLEAN DEFAULT FALSE,
                    last_login TIMESTAMP WITH TIME ZONE,
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
                )
            """))
            
            # 2. Clients table (client accounts and sub-accounts)
            print("📝 Creating/updating Clients table...")
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS clients (
                    id SERIAL PRIMARY KEY,
                    name VARCHAR NOT NULL,
                    company VARCHAR,
                    email VARCHAR,
                    phone VARCHAR,
                    address TEXT,
                    city VARCHAR,
                    state VARCHAR,
                    zip_code VARCHAR,
                    parent_client_id INTEGER REFERENCES clients(id),
                    is_active BOOLEAN DEFAULT TRUE,
                    notes TEXT,
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
                )
            """))
            
            # 3. Projects table (appraisals with client info, Dropbox links, case details)
            print("📝 Creating/updating Projects table...")
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS projects (
                    id SERIAL PRIMARY KEY,
                    project_name VARCHAR NOT NULL,
                    client_id INTEGER REFERENCES clients(id) NOT NULL,
                    assigned_user_id INTEGER REFERENCES users(id) NOT NULL,
                    case_number VARCHAR,
                    appraisal_type VARCHAR NOT NULL CHECK (appraisal_type IN ('estate', 'divorce', 'insurance', 'donation', 'other')),
                    purpose TEXT,
                    inspection_date DATE,
                    report_date DATE,
                    dropbox_folder_link VARCHAR,
                    dropbox_folder_id VARCHAR,
                    status VARCHAR DEFAULT 'draft' CHECK (status IN ('draft', 'in_progress', 'review', 'completed', 'delivered')),
                    total_value DECIMAL(12,2) DEFAULT 0.00,
                    item_count INTEGER DEFAULT 0,
                    template_id INTEGER,
                    notes TEXT,
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
                )
            """))
            
            # 4. Photos table (with thumbnails, EXIF data, ordering)
            print("📝 Creating/updating Photos table...")
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS photos (
                    id SERIAL PRIMARY KEY,
                    project_id INTEGER REFERENCES projects(id) NOT NULL,
                    original_filename VARCHAR NOT NULL,
                    file_path VARCHAR NOT NULL,
                    thumbnail_path VARCHAR,
                    file_size INTEGER,
                    mime_type VARCHAR,
                    width INTEGER,
                    height INTEGER,
                    exif_date TIMESTAMP WITH TIME ZONE,
                    sort_order INTEGER DEFAULT 0,
                    is_deleted BOOLEAN DEFAULT FALSE,
                    dropbox_file_id VARCHAR,
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
                )
            """))
            
            # 5. Items table (appraisal line items with photos, descriptions, values)
            print("📝 Creating/updating Items table...")
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS items (
                    id SERIAL PRIMARY KEY,
                    project_id INTEGER REFERENCES projects(id) NOT NULL,
                    line_number INTEGER NOT NULL,
                    photo_id INTEGER REFERENCES photos(id),
                    room_area VARCHAR,
                    item_type VARCHAR,
                    description TEXT,
                    detailed_description TEXT,
                    estimated_value DECIMAL(10,2),
                    replacement_value DECIMAL(10,2),
                    market_value DECIMAL(10,2),
                    condition_notes TEXT,
                    sort_order INTEGER DEFAULT 0,
                    is_deleted BOOLEAN DEFAULT FALSE,
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                    UNIQUE(project_id, line_number)
                )
            """))
            
            # 6. Reports table (Word templates, draft/final versions)
            print("📝 Creating/updating Reports table...")
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS reports (
                    id SERIAL PRIMARY KEY,
                    project_id INTEGER REFERENCES projects(id) NOT NULL,
                    template_name VARCHAR NOT NULL,
                    report_type VARCHAR DEFAULT 'draft' CHECK (report_type IN ('draft', 'final')),
                    file_path VARCHAR,
                    pdf_path VARCHAR,
                    word_path VARCHAR,
                    has_watermark BOOLEAN DEFAULT TRUE,
                    generated_at TIMESTAMP WITH TIME ZONE,
                    dropbox_file_id VARCHAR,
                    is_current BOOLEAN DEFAULT TRUE,
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
                )
            """))
            
            # 7. Templates table (Word templates with dynamic fields)
            print("📝 Creating/updating Templates table...")
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS templates (
                    id SERIAL PRIMARY KEY,
                    name VARCHAR NOT NULL,
                    appraisal_type VARCHAR NOT NULL,
                    file_path VARCHAR NOT NULL,
                    description TEXT,
                    field_mappings JSONB,
                    is_active BOOLEAN DEFAULT TRUE,
                    version VARCHAR DEFAULT '1.0',
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
                )
            """))
            
            # 8. Metals Prices table (for gold, silver, platinum API integration)
            print("📝 Creating/updating Metals Prices table...")
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS metals_prices (
                    id SERIAL PRIMARY KEY,
                    metal_type VARCHAR NOT NULL CHECK (metal_type IN ('gold', 'silver', 'platinum', 'palladium')),
                    price_per_oz DECIMAL(10,2) NOT NULL,
                    currency VARCHAR DEFAULT 'USD',
                    price_date DATE NOT NULL,
                    source VARCHAR DEFAULT 'metals_api',
                    is_manual_override BOOLEAN DEFAULT FALSE,
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                    UNIQUE(metal_type, price_date)
                )
            """))
            
            # 9. Activity Log table (for audit trail)
            print("📝 Creating/updating Activity Log table...")
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS activity_log (
                    id SERIAL PRIMARY KEY,
                    user_id INTEGER REFERENCES users(id),
                    project_id INTEGER REFERENCES projects(id),
                    action VARCHAR NOT NULL,
                    details JSONB,
                    ip_address INET,
                    user_agent TEXT,
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
                )
            """))
            
            # Create indexes for better performance
            print("📝 Creating database indexes...")
            
            # Users indexes
            conn.execute(text("CREATE INDEX IF NOT EXISTS idx_users_role ON users(role)"))
            conn.execute(text("CREATE INDEX IF NOT EXISTS idx_users_active ON users(is_active)"))
            
            # Clients indexes
            conn.execute(text("CREATE INDEX IF NOT EXISTS idx_clients_parent ON clients(parent_client_id)"))
            conn.execute(text("CREATE INDEX IF NOT EXISTS idx_clients_active ON clients(is_active)"))
            
            # Projects indexes
            conn.execute(text("CREATE INDEX IF NOT EXISTS idx_projects_client ON projects(client_id)"))
            conn.execute(text("CREATE INDEX IF NOT EXISTS idx_projects_user ON projects(assigned_user_id)"))
            conn.execute(text("CREATE INDEX IF NOT EXISTS idx_projects_status ON projects(status)"))
            conn.execute(text("CREATE INDEX IF NOT EXISTS idx_projects_type ON projects(appraisal_type)"))
            
            # Photos indexes
            conn.execute(text("CREATE INDEX IF NOT EXISTS idx_photos_project ON photos(project_id)"))
            conn.execute(text("CREATE INDEX IF NOT EXISTS idx_photos_order ON photos(project_id, sort_order)"))
            conn.execute(text("CREATE INDEX IF NOT EXISTS idx_photos_exif_date ON photos(exif_date)"))
            
            # Items indexes
            conn.execute(text("CREATE INDEX IF NOT EXISTS idx_items_project ON items(project_id)"))
            conn.execute(text("CREATE INDEX IF NOT EXISTS idx_items_photo ON items(photo_id)"))
            conn.execute(text("CREATE INDEX IF NOT EXISTS idx_items_order ON items(project_id, sort_order)"))
            
            # Reports indexes
            conn.execute(text("CREATE INDEX IF NOT EXISTS idx_reports_project ON reports(project_id)"))
            conn.execute(text("CREATE INDEX IF NOT EXISTS idx_reports_current ON reports(is_current)"))
            
            # Metals prices indexes
            conn.execute(text("CREATE INDEX IF NOT EXISTS idx_metals_date ON metals_prices(price_date DESC)"))
            conn.execute(text("CREATE INDEX IF NOT EXISTS idx_metals_type_date ON metals_prices(metal_type, price_date DESC)"))
            
            # Activity log indexes
            conn.execute(text("CREATE INDEX IF NOT EXISTS idx_activity_user ON activity_log(user_id)"))
            conn.execute(text("CREATE INDEX IF NOT EXISTS idx_activity_project ON activity_log(project_id)"))
            conn.execute(text("CREATE INDEX IF NOT EXISTS idx_activity_date ON activity_log(created_at DESC)"))
            
            conn.commit()
            print("✅ Database schema sync completed successfully!")
            
        except Exception as e:
            print(f"❌ Error during schema sync: {e}")
            conn.rollback()
            raise

def verify_requirements_schema():
    """Verify the database schema matches the 21-day project requirements"""
    engine = create_engine(settings.DATABASE_URL)
    inspector = inspect(engine)
    
    print("\n🔍 Verifying schema against project requirements...")
    
    required_tables = {
        'users': ['username', 'email', 'role', 'otp_secret', 'otp_enabled'],
        'clients': ['name', 'parent_client_id', 'is_active'],
        'projects': ['project_name', 'client_id', 'appraisal_type', 'dropbox_folder_link', 'status'],
        'photos': ['project_id', 'file_path', 'thumbnail_path', 'exif_date', 'sort_order'],
        'items': ['project_id', 'line_number', 'photo_id', 'room_area', 'item_type', 'description', 'estimated_value'],
        'reports': ['project_id', 'template_name', 'report_type', 'has_watermark'],
        'templates': ['name', 'appraisal_type', 'field_mappings'],
        'metals_prices': ['metal_type', 'price_per_oz', 'price_date'],
        'activity_log': ['user_id', 'action', 'details']
    }
    
    existing_tables = inspector.get_table_names()
    
    for table, required_cols in required_tables.items():
        if table in existing_tables:
            print(f"  ✅ Table '{table}' exists")
            
            columns = [col['name'] for col in inspector.get_columns(table)]
            
            for col in required_cols:
                if col in columns:
                    print(f"    ✅ Column '{col}' exists")
                else:
                    print(f"    ❌ Column '{col}' missing")
        else:
            print(f"  ❌ Table '{table}' missing")
    
    print("✅ Requirements verification completed!")

if __name__ == "__main__":
    sync_database_schema()
    verify_requirements_schema()