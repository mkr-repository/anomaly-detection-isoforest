# Import os module for processing directory locations and filepath concatenations
import os
# Import joblib library to serialize (pickle) the trained model into a static binary file
import joblib
# Import pandas under pd alias to handle structured data matrices (DataFrames)
import pandas as pd
# Import unsupervised Isolation Forest algorithm class from scikit-learn ensemble module
from sklearn.ensemble import IsolationForest

# Define model fitting procedure receiving pre-loaded transactional data
def train_model_pipeline(df: pd.DataFrame):
    """
    Trains the Isolation Forest model using the columns of the passed DataFrame and saves model.joblib.
    """
    # List the exact 5 column names needed for training and inference
    required_features = [
        "seconds_since_page_load",
        "failed_attempts_past_hour",
        "unique_cards_per_ip",
        "is_datacenter_ip",
        "accounts_per_device_24h"
    ]
    
    # Identify any features defined above that are absent in the input dataset columns
    missing_cols = [col for col in required_features if col not in df.columns]
    # If any required fields are missing, halt operation and report error
    if missing_cols:
        # Raise ValueError stating exactly which features are missing from input dataset
        raise ValueError(f"DataFrame is missing required features: {missing_cols}")
        
    # Extract only the relevant validation feature columns to serve as training matrix
    X_train = df[required_features]
    # Output progress state to system logs for verification
    print(f"[Trainer] Fitting Isolation Forest model with {len(X_train)} samples...")
    
    # Instantiated scikit-learn Isolation Forest model:
    # contamination=0.10: expected anomaly rate in dataset (sets prediction threshold)
    # random_state=42: ensures identical splits and trees every run
    model = IsolationForest(contamination=0.10, random_state=42)
    # Feed data matrix into forest algorithm to build isolation trees
    model.fit(X_train)
    
    # Locate directory folder where this python file resides
    current_dir = os.path.dirname(os.path.abspath(__file__))
    # Build complete destination filepath for the serialized model binary
    model_path = os.path.join(current_dir, "model.joblib")
    # Save the trained model memory state onto the local disk as model.joblib
    joblib.dump(model, model_path)
    # Print status confirmation indicating model binary has been persisted
    print(f"[Trainer] Model serialized successfully to: {model_path}")
