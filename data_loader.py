# Import os module to handle file paths and directory navigation dynamically
import os
# Import glob module to search the directory tree for files matching pattern criteria
import glob
# Import pandas under pd alias to load and manipulate structured tabular datasets
import pandas as pd

# Define a function to find and read a local CSV file into memory
def load_csv_data():
    """
    Scans the current directory for any CSV files and loads the first one into a pandas DataFrame.
    """
    # Determine the absolute directory path where this loader script resides
    current_dir = os.path.dirname(os.path.abspath(__file__))
    # Compile a list of all files ending with .csv in that folder path
    csv_files = glob.glob(os.path.join(current_dir, "*.csv"))
    
    # If the list is empty, search for CSVs in the active shell directory
    if not csv_files:
        # Scan current working directory for matching wildcard filenames
        csv_files = glob.glob("iso-training-data.csv")
        
    # If still no CSV files exist, abort operation and notify caller
    if not csv_files:
        # Raise standard FileNotFoundError indicating no data source was found
        raise FileNotFoundError("No CSV file found in the current directory.")
        
    # Extract the path string of the first found CSV file in the list
    csv_path = csv_files[0]
    # Output the loaded file path to the server logs for diagnostics
    print(f"[DataLoader] Reading CSV file from: {csv_path}")
    # Read the file's data into a pandas DataFrame and store in memory
    df = pd.read_csv(csv_path)
    print(f"[DataLoader] Successfully loaded {len(df)} samples.")
    # Return the populated DataFrame containing transaction records
    return df
