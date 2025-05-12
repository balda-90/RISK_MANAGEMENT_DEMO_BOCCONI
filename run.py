#!/usr/bin/env python
"""
Run script for the Automotive Risk Assessment application.
This script handles environment setup and launches the Streamlit application.
"""

import os
import sys
import subprocess
import platform
from pathlib import Path
from dotenv import load_dotenv

def check_env_file():
    """Check if .env file exists, create if not"""
    env_path = Path('.env')
    if not env_path.exists():
        print("Creating .env file. Please add your OpenAI API key to it.")
        with open(env_path, 'w') as f:
            f.write("OPENAI_API_KEY=your_openai_api_key_here\n")
        print(f".env file created at {env_path.absolute()}")
    else:
        # Check if API key is set
        load_dotenv()
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key or api_key == "your_openai_api_key_here":
            print("⚠️ Warning: OpenAI API key not set in .env file")
            print("Please edit the .env file and add your API key")

def check_directories():
    """Check if required directories exist, create if not"""
    dirs = ['data', 'config', 'agents', 'voice_commands']
    for dir_name in dirs:
        dir_path = Path(dir_name)
        if not dir_path.exists():
            dir_path.mkdir(exist_ok=True)
            print(f"Created directory: {dir_name}")

def activate_virtual_env():
    """Activate virtual environment if it exists"""
    venv_path = Path('venv')
    if venv_path.exists():
        if platform.system() == 'Windows':
            activate_script = venv_path / 'Scripts' / 'activate'
        else:
            activate_script = venv_path / 'bin' / 'activate'
        
        if activate_script.exists():
            print("Virtual environment found. Activating...")
            # Note: This doesn't actually work within this script context
            # due to subprocess limitations, but we provide instructions
            if platform.system() == 'Windows':
                print("To activate manually, run: .\\venv\\Scripts\\activate")
            else:
                print("To activate manually, run: source venv/bin/activate")

def run_app():
    """Run the Streamlit application"""
    try:
        print("Starting Automotive Risk Assessment application...")
        subprocess.run([sys.executable, "-m", "streamlit", "run", "app.py"])
    except KeyboardInterrupt:
        print("\nApplication stopped by user")
    except Exception as e:
        print(f"Error starting application: {e}")
        print("\nTry running manually with: streamlit run app.py")

def main():
    """Main function to run the application"""
    print("=== Automotive Risk Assessment Application ===")
    
    # Setup environment
    check_env_file()
    check_directories()
    activate_virtual_env()
    
    # Run the application
    run_app()

if __name__ == "__main__":
    main() 