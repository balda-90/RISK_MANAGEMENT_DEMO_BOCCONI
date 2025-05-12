import os
import mysql.connector
from mysql.connector import Error
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def create_database():
    """Create the database if it doesn't exist"""
    try:
        # Connect to MySQL server
        connection = mysql.connector.connect(
            host=os.getenv('DB_HOST', 'localhost'),
            user=os.getenv('DB_USER', 'root'),
            password=os.getenv('DB_PASSWORD', '')
        )
        
        if connection.is_connected():
            cursor = connection.cursor()
            
            # Create database if it doesn't exist
            cursor.execute(f"CREATE DATABASE IF NOT EXISTS {os.getenv('DB_NAME', 'risk_assessment')}")
            print("Database created successfully")
            
            cursor.close()
            connection.close()
            
    except Error as e:
        print(f"Error creating database: {e}")

def create_tables():
    """Create the necessary tables"""
    try:
        # Connect to the database
        connection = mysql.connector.connect(
            host=os.getenv('DB_HOST', 'localhost'),
            user=os.getenv('DB_USER', 'root'),
            password=os.getenv('DB_PASSWORD', ''),
            database=os.getenv('DB_NAME', 'risk_assessment')
        )
        
        if connection.is_connected():
            cursor = connection.cursor()
            
            # Create risks table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS risks (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    risk_id VARCHAR(10) UNIQUE NOT NULL,
                    level ENUM('strategic', 'project', 'operational') NOT NULL,
                    project VARCHAR(100) NOT NULL,
                    risk_title VARCHAR(200) NOT NULL,
                    risk_description TEXT,
                    risk_probability DECIMAL(3,2),
                    cost_impact DECIMAL(15,2),
                    time_impact INT,
                    detection DECIMAL(3,2),
                    mitigation_plan TEXT,
                    owner VARCHAR(100),
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
                )
            """)
            print("Risks table created successfully")
            
            cursor.close()
            connection.close()
            
    except Error as e:
        print(f"Error creating tables: {e}")

def load_initial_data():
    """Load the initial risk data from SQL file"""
    try:
        # Connect to the database
        connection = mysql.connector.connect(
            host=os.getenv('DB_HOST', 'localhost'),
            user=os.getenv('DB_USER', 'root'),
            password=os.getenv('DB_PASSWORD', ''),
            database=os.getenv('DB_NAME', 'risk_assessment')
        )
        
        if connection.is_connected():
            cursor = connection.cursor()
            
            # Read and execute the SQL file
            with open('database/initial_risks.sql', 'r') as file:
                sql_commands = file.read()
                
                # Split the commands by semicolon and execute each one
                for command in sql_commands.split(';'):
                    if command.strip():
                        cursor.execute(command)
            
            connection.commit()
            print("Initial data loaded successfully")
            
            cursor.close()
            connection.close()
            
    except Error as e:
        print(f"Error loading initial data: {e}")

def main():
    """Main function to initialize the database"""
    print("Starting database initialization...")
    
    # Create database
    create_database()
    
    # Create tables
    create_tables()
    
    # Load initial data
    load_initial_data()
    
    print("Database initialization completed!")

if __name__ == "__main__":
    main() 