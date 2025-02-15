# run_frontend.py (place in project root)
import sys
from pathlib import Path

# Add the project root to Python path
root_dir = Path(__file__).parent
sys.path.append(str(root_dir))

# Import and run the Streamlit app
from app.frontend.app import main

if __name__ == "__main__":
    main()
