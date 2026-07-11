# Import os module to handle file checks and find files relative to this loader
import os
# Import joblib library to unpack/deserialize the persisted binary file model.joblib
import joblib

# Determine absolute path to model binary file (model.joblib) in the current directory
MODEL_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "model.joblib")

# Define deserialization routine to pull the saved model into active memory
def load_model():
    """
    Loads the serialized Isolation Forest model from disk.
    """
    # Check if model.joblib file exists at the expected directory path
    if not os.path.exists(MODEL_PATH):
        # Raise descriptive FileNotFoundError advising user how to generate model
        raise FileNotFoundError(
            f"Model file not found at '{MODEL_PATH}'. "
            f"Please run 'python train.py' first to train and save the model."
        )
    # Log loading progress message with source path details
    print(f"Loading trained Isolation Forest model from {MODEL_PATH}...")
    # Load the saved model memory image from disk and return its object reference
    model = joblib.load(MODEL_PATH)
    # Return the deserialized IsolationForest model ready for inference
    return model
