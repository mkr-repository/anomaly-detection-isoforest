# Import sys module to control execution flow and handle errors by exiting script processes
import sys
# Import uvicorn to handle programmatic web server hosting for the FastAPI application
import uvicorn
# Import data loader function to discover and parse the CSV training records
from data_loader import load_csv_data
# Import train script logic to build the Isolation Forest model using the parsed data
from train import train_model_pipeline
# Import model loader helper to verify file loading prior to launching web server
from model_loader import load_model

# Define the central pipeline orchestration function that chains steps 1 to 4
def run_pipeline():
    # Print orchestrator interface header divider to the console
    print("====================================================")
    print("Fraud Detection System Pipeline Orchestrator")
    print("====================================================")
    
    # 1. Step 1: Discover and Load CSV Data
    print("\n[Step 1/4] Loading CSV Data...")
    try:
        # Load local folder CSV files into pandas DataFrame
        df = load_csv_data()
        # Log success confirmation status indicating sample count loaded
        print(f"✔ Successfully loaded {len(df)} samples.")
    # Trap errors if data files are missing or unreadable
    except Exception as e:
        # Print failure output details to the log
        print(f"❌ Step 1 (Load CSV) Failed: {e}")
        # Exit execution workflow immediately to block training errors
        sys.exit(1)
        
    # 2. Step 2: Fit model on data and save to disk
    print("\n[Step 2/4] Training Isolation Forest Model...")
    try:
        # Call training code, building tree structures and exporting model.joblib
        train_model_pipeline(df)
        # Log model generation completion status
        print("✔ Model training complete.")
    # Trap mathematical fitting or file exporting exceptions
    except Exception as e:
        # Print failure status details to the console log
        print(f"❌ Step 2 (Train Model) Failed: {e}")
        # Abort pipeline execution before next pipeline sequence
        sys.exit(1)
        
    # 3. Step 3: Deserialization test check
    print("\n[Step 3/4] Verifying Model Loading in Memory...")
    try:
        # Test loading serialized model file into memory to confirm validity
        model = load_model()
        # Log confirmation showing memory loading was successful
        print(f"✔ Model verified in memory: {model}")
    # Trap deserialization failures (e.g. library version mismatch or corrupt file)
    except Exception as e:
        # Print warning details to the console logs
        print(f"❌ Step 3 (Load Model) Failed: {e}")
        # Halt application start before initializing the web server
        sys.exit(1)
        
    # 4. Step 4: Run server deployment
    print("\n[Step 4/4] Starting FastAPI Server on http://127.0.0.1:8000 ...")
    try:
        # Deploy FastAPI server on localhost interface (127.0.0.1) on port 8000
        # reload=False is explicitly set to prevent infinite training loops from file change watcher
        uvicorn.run("app:app", host="127.0.0.1", port=8000, reload=False)
    # Trap socket connection failures or port conflicts
    except Exception as e:
        # Print server startup failure details
        print(f"❌ Step 4 (Start Server) Failed: {e}")
        # Exit running process with error code status
        sys.exit(1)

# Check if script is run directly in terminal via shell command
if __name__ == "__main__":
    # Start pipeline orchestrator execution flow
    run_pipeline()
