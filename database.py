# database.py - SQLite Version (Replace Entire File)
import sqlite3
import pandas as pd
import hashlib
from contextlib import contextmanager
from datetime import datetime

class DatabaseManager:
    def __init__(self):
        self.db_path = 'mobile_analytics.db'
        self.init_database()
    
    def init_database(self):
        """Initialize database with all tables"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                # Users table
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS users (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        username TEXT UNIQUE NOT NULL,
                        password_hash TEXT NOT NULL,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        last_login TIMESTAMP,
                        role TEXT DEFAULT 'user'
                    )
                ''')
                
                # Mobile data table
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS mobile_data (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        company_name TEXT,
                        model_name TEXT,
                        launched_year INTEGER,
                        ram TEXT,
                        storage TEXT,
                        battery_capacity TEXT,
                        screen_size TEXT,
                        front_camera TEXT,
                        back_camera TEXT,
                        processor TEXT,
                        mobile_weight TEXT,
                        price_pakistan REAL,
                        price_india REAL,
                        price_usa REAL,
                        price_china REAL,
                        price_dubai REAL,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
                
                # Create indexes
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_company ON mobile_data(company_name)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_year ON mobile_data(launched_year)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_price ON mobile_data(price_pakistan)')
                
                # Predictions history
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS predictions_history (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        user_id INTEGER,
                        company TEXT,
                        model_name TEXT,
                        launch_year INTEGER,
                        ram_gb INTEGER,
                        storage_gb INTEGER,
                        battery_mah INTEGER,
                        screen_size_inch REAL,
                        front_camera_mp INTEGER,
                        back_camera_mp INTEGER,
                        processor TEXT,
                        weight_grams INTEGER,
                        predicted_price REAL,
                        confidence REAL,
                        price_lower_bound REAL,
                        price_upper_bound REAL,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
                
                # User activity
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS user_activity (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        user_id INTEGER,
                        activity_type TEXT,
                        activity_details TEXT,
                        ip_address TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
                
                # Insert default users
                default_users = [
                    ('admin', hashlib.sha256('admin123'.encode()).hexdigest(), 'admin'),
                    ('analyst', hashlib.sha256('analyst123'.encode()).hexdigest(), 'analyst'),
                    ('user', hashlib.sha256('user123'.encode()).hexdigest(), 'user')
                ]
                
                for username, pwd_hash, role in default_users:
                    cursor.execute('''
                        INSERT OR IGNORE INTO users (username, password_hash, role)
                        VALUES (?, ?, ?)
                    ''', (username, pwd_hash, role))
                
                conn.commit()
                print("Database initialized successfully")
                
        except Exception as e:
            print(f"Database initialization error: {e}")
    
    @contextmanager
    def get_connection(self):
        """Context manager for database connections"""
        conn = None
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            yield conn
        except Exception as e:
            print(f"Database connection error: {e}")
            raise
        finally:
            if conn:
                conn.close()
    
    def test_connection(self):
        """Test database connection"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT 1")
                result = cursor.fetchone()
                return result[0] == 1
        except Exception as e:
            print(f"Connection test failed: {e}")
            return False
    
    def create_user(self, username, password, role='user'):
        """Create new user in database"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                password_hash = hashlib.sha256(password.encode()).hexdigest()
                
                cursor.execute('''
                    INSERT INTO users (username, password_hash, role)
                    VALUES (?, ?, ?)
                ''', (username, password_hash, role))
                
                conn.commit()
                return True, "User created successfully"
        except sqlite3.IntegrityError:
            return False, "Username already exists"
        except Exception as e:
            return False, f"Database error: {e}"
    
    def verify_user(self, username, password):
        """Verify user credentials"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                password_hash = hashlib.sha256(password.encode()).hexdigest()
                
                cursor.execute('''
                    SELECT id, username, role, last_login 
                    FROM users 
                    WHERE username = ? AND password_hash = ?
                ''', (username, password_hash))
                
                user = cursor.fetchone()
                
                if user:
                    # Update last login
                    cursor.execute('''
                        UPDATE users 
                        SET last_login = CURRENT_TIMESTAMP 
                        WHERE id = ?
                    ''', (user['id'],))
                    conn.commit()
                    
                    return True, dict(user)
                return False, "Invalid credentials"
        except Exception as e:
            print(f"User verification error: {e}")
            return False, f"Database error: {e}"
    
    def load_mobile_data(self):
        """Load mobile data from CSV and save to database"""
        try:
            # First load from CSV
            df = self.load_data_from_csv()
            
            # Save to database
            if not df.empty:
                success, message = self.save_mobile_data(df)
                if success:
                    print(f"Data loaded to database: {message}")
                else:
                    print(f"Failed to save data: {message}")
            
            # Now load from database
            with self.get_connection() as conn:
                query = '''
                    SELECT 
                        company_name as "Company Name",
                        model_name as "Model Name",
                        launched_year as "Launched Year",
                        ram as "RAM",
                        storage as "Storage",
                        battery_capacity as "Battery Capacity",
                        screen_size as "Screen Size",
                        front_camera as "Front Camera",
                        back_camera as "Back Camera",
                        processor as "Processor",
                        mobile_weight as "Mobile Weight",
                        price_pakistan as "Launched Price (Pakistan)",
                        price_india as "Launched Price (India)",
                        price_usa as "Launched Price (USA)",
                        price_china as "Launched Price (China)",
                        price_dubai as "Launched Price (Dubai)"
                    FROM mobile_data
                    ORDER BY launched_year DESC, company_name
                '''
                df = pd.read_sql_query(query, conn)
                return df
        except Exception as e:
            print(f"Load mobile data error: {e}")
            return pd.DataFrame()
    
    def load_data_from_csv(self):
        """Load data from CSV file"""
        try:
            encodings = ['latin-1', 'cp1252', 'iso-8859-1', 'utf-8', 'utf-16']
            
            for encoding in encodings:
                try:
                    df = pd.read_csv('Mobiles Dataset (2025).csv', encoding=encoding, on_bad_lines='skip')
                    break
                except:
                    continue
            else:
                try:
                    df = pd.read_csv('Mobiles Dataset (2025).csv', encoding='latin-1', engine='python', on_bad_lines='skip')
                except:
                    df = pd.read_csv('Mobiles Dataset (2025).csv', encoding='latin-1', sep=',', on_bad_lines='skip')
            
            # Clean price columns
            price_columns = ['Launched Price (Pakistan)', 'Launched Price (India)', 
                           'Launched Price (China)', 'Launched Price (USA)', 
                           'Launched Price (Dubai)']
            
            for col in price_columns:
                if col in df.columns:
                    df[col] = df[col].astype(str)
                    df[col] = df[col].str.replace('PKR ', '', regex=False)
                    df[col] = df[col].str.replace('INR ', '', regex=False)
                    df[col] = df[col].str.replace('CNY ', '', regex=False)
                    df[col] = df[col].str.replace('USD ', '', regex=False)
                    df[col] = df[col].str.replace('AED ', '', regex=False)
                    df[col] = df[col].str.replace(',', '', regex=False)
                    df[col] = df[col].str.replace('"', '', regex=False)
                    df[col] = pd.to_numeric(df[col], errors='coerce')
            
            return df
        except Exception as e:
            print(f"Load CSV error: {e}")
            return pd.DataFrame()
    
    def save_mobile_data(self, df):
        """Save mobile data to database"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                # Clear existing data
                cursor.execute("DELETE FROM mobile_data")
                
                # Prepare data for insertion
                for _, row in df.iterrows():
                    cursor.execute('''
                        INSERT INTO mobile_data (
                            company_name, model_name, launched_year,
                            ram, storage, battery_capacity,
                            screen_size, front_camera, back_camera,
                            processor, mobile_weight,
                            price_pakistan, price_india, price_usa,
                            price_china, price_dubai
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (
                        str(row.get('Company Name', '')),
                        str(row.get('Model Name', '')),
                        int(row.get('Launched Year', 2023)) if pd.notna(row.get('Launched Year')) else 2023,
                        str(row.get('RAM', '')),
                        str(row.get('Storage', '')),
                        str(row.get('Battery Capacity', '')),
                        str(row.get('Screen Size', '')),
                        str(row.get('Front Camera', '')),
                        str(row.get('Back Camera', '')),
                        str(row.get('Processor', '')),
                        str(row.get('Mobile Weight', '')),
                        float(row.get('Launched Price (Pakistan)', 0) or 0),
                        float(row.get('Launched Price (India)', 0) or 0),
                        float(row.get('Launched Price (USA)', 0) or 0),
                        float(row.get('Launched Price (China)', 0) or 0),
                        float(row.get('Launched Price (Dubai)', 0) or 0)
                    ))
                
                conn.commit()
                return True, f"Inserted {len(df)} records"
        except Exception as e:
            print(f"Save mobile data error: {e}")
            return False, f"Database error: {e}"
    
    def get_filtered_data(self, companies=None, years=None, price_range=None):
        """Get filtered data based on criteria"""
        try:
            with self.get_connection() as conn:
                query = "SELECT * FROM mobile_data WHERE 1=1"
                params = []
                
                if companies:
                    placeholders = ','.join(['?'] * len(companies))
                    query += f" AND company_name IN ({placeholders})"
                    params.extend(companies)
                
                if years:
                    query += " AND launched_year BETWEEN ? AND ?"
                    params.extend([years[0], years[1]])
                
                if price_range:
                    query += " AND price_pakistan BETWEEN ? AND ?"
                    params.extend([price_range[0], price_range[1]])
                
                query += " ORDER BY price_pakistan DESC"
                
                df = pd.read_sql_query(query, conn, params=params)
                return df
        except Exception as e:
            print(f"Get filtered data error: {e}")
            return pd.DataFrame()
    
    def get_company_stats(self):
        """Get company statistics"""
        try:
            with self.get_connection() as conn:
                query = '''
                    SELECT 
                        company_name,
                        COUNT(*) as model_count,
                        AVG(price_pakistan) as avg_price,
                        MAX(price_pakistan) as max_price,
                        MIN(price_pakistan) as min_price,
                        MAX(launched_year) as latest_year
                    FROM mobile_data
                    GROUP BY company_name
                    ORDER BY model_count DESC
                '''
                df = pd.read_sql_query(query, conn)
                return df
        except Exception as e:
            print(f"Get company stats error: {e}")
            return pd.DataFrame()
    
    def get_yearly_stats(self):
        """Get yearly statistics"""
        try:
            with self.get_connection() as conn:
                query = '''
                    SELECT 
                        launched_year,
                        AVG(price_pakistan) as avg_price,
                        COUNT(*) as model_count
                    FROM mobile_data
                    GROUP BY launched_year
                    ORDER BY launched_year
                '''
                df = pd.read_sql_query(query, conn)
                return df
        except Exception as e:
            print(f"Get yearly stats error: {e}")
            return pd.DataFrame()
    
    def save_prediction(self, user_id, prediction_data):
        """Save prediction to history"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                    INSERT INTO predictions_history (
                        user_id, company, model_name, launch_year,
                        ram_gb, storage_gb, battery_mah, screen_size_inch,
                        front_camera_mp, back_camera_mp, processor, weight_grams,
                        predicted_price, confidence, price_lower_bound, price_upper_bound
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    user_id,
                    prediction_data.get('company'),
                    prediction_data.get('model_name'),
                    prediction_data.get('launch_year'),
                    prediction_data.get('ram'),
                    prediction_data.get('storage_used'),
                    prediction_data.get('battery'),
                    prediction_data.get('screen_size'),
                    prediction_data.get('front_camera'),
                    prediction_data.get('back_camera'),
                    prediction_data.get('processor'),
                    prediction_data.get('weight'),
                    prediction_data.get('predicted_price'),
                    prediction_data.get('confidence'),
                    prediction_data.get('price_range')[0],
                    prediction_data.get('price_range')[1]
                ))
                
                conn.commit()
                return True, "Prediction saved"
        except Exception as e:
            print(f"Save prediction error: {e}")
            return False, f"Database error: {e}"
    
    def get_user_predictions(self, user_id, limit=10):
        """Get user's prediction history"""
        try:
            with self.get_connection() as conn:
                query = '''
                    SELECT 
                        company, model_name, launch_year,
                        ram_gb, storage_gb, predicted_price,
                        confidence, created_at
                    FROM predictions_history
                    WHERE user_id = ?
                    ORDER BY created_at DESC
                    LIMIT ?
                '''
                df = pd.read_sql_query(query, conn, params=[user_id, limit])
                return df
        except Exception as e:
            print(f"Get user predictions error: {e}")
            return pd.DataFrame()
    
    def log_activity(self, user_id, activity_type, details, ip_address=None):
        """Log user activity"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO user_activity (user_id, activity_type, activity_details, ip_address)
                    VALUES (?, ?, ?, ?)
                ''', (user_id, activity_type, details, ip_address))
                conn.commit()
                return True
        except Exception as e:
            print(f"Log activity error: {e}")
            return False

# Global database instance
db = DatabaseManager()