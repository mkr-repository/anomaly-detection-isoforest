# Walkthrough: FastAPI Card-Testing Fraud Detection API

We have built and verified a production-ready, Python-native FastAPI application that deploys an unsupervised Isolation Forest model for real-time card-testing fraud detection. The model is trained on startup and stored in memory for rapid, low-latency inference.

## Project Structure

All files have been successfully created and configured in the `/Users/manishkumar/ML-projects/anomaly-detection-isoforest` directory:

- [requirements.txt](file:///Users/manishkumar/ML-projects/anomaly-detection-isoforest/requirements.txt): Lists necessary python dependencies (`fastapi`, `uvicorn`, `scikit-learn`, `pandas`, `pydantic`, `httpx`).
- [card_fraud_data.csv](file:///Users/manishkumar/ML-projects/anomaly-detection-isoforest/card_fraud_data.csv): A synthetic dataset with 200 samples (90% normal, 10% anomalies/bots) to train the unsupervised Isolation Forest model.
- [main.py](file:///Users/manishkumar/ML-projects/anomaly-detection-isoforest/main.py): The core FastAPI application that implements schema validation, trains the model on startup, and exposes `/add-card/analyze`.
- [test_api.py](file:///Users/manishkumar/ML-projects/anomaly-detection-isoforest/test_api.py): A test script implementing automated testing for standard and advanced bad users.

---

## File Details

### 1. [main.py](file:///Users/manishkumar/ML-projects/anomaly-detection-isoforest/main.py)
This file defines:
- **Input Validation**: Uses Pydantic to validate `seconds_since_page_load`, `failed_attempts_past_hour`, `unique_cards_per_ip`, `is_datacenter_ip`, and `accounts_per_device_24h`.
- **Model Training**: On startup, using the lifespan event context manager, FastAPI loads the `.csv` file found in the current directory and fits an `IsolationForest` classifier with a contamination parameter of `0.10`.
- **Prediction Mapping**: Maps scikit-learn's prediction results (`-1` for anomalies, `1` for normal) to the user-requested output schema:
  - `prediction = 1` and `action_required = "CHALLENGE_CAPTCHA"` (for anomalies)
  - `prediction = 0` and `action_required = "ALLOW"` (for normal behavior)

### 2. [test_api.py](file:///Users/manishkumar/ML-projects/anomaly-detection-isoforest/test_api.py)
This test script verifies the logic in-process via `TestClient` and can also run against a live running server when passed an HTTP URL argument.

---

## Test Results and Verification

Running the test script inside the folder outputted:
```bash
$ .venv/bin/python test_api.py
Running tests IN-PROCESS using FastAPI's TestClient inside lifespan context...
Loading training data from /Users/manishkumar/ML-projects/anomaly-detection-isoforest/card_fraud_data.csv...
Training unsupervised Isolation Forest model (contamination=0.10) with 200 samples...
Model training completed successfully.
✔ Root Endpoint response: {'message': 'Welcome to the Card-Testing Fraud Detection API', 'status': 'active', 'model_loaded': True, 'docs_url': '/docs'}
✔ Root endpoint checks passed!

--- Testing Standard User (Expecting ALLOW) ---
Payload: {'seconds_since_page_load': 18.5, 'failed_attempts_past_hour': 0, 'unique_cards_per_ip': 1, 'is_datacenter_ip': 0, 'accounts_per_device_24h': 1}
Response: {'raw_anomaly_score': 0.19924461623448608, 'prediction': 0, 'action_required': 'ALLOW'}
✔ Standard User Test Passed: User was ALLOWED.

--- Testing Advanced Bad User (Expecting CHALLENGE_CAPTCHA) ---
Payload: {'seconds_since_page_load': 0.45, 'failed_attempts_past_hour': 15, 'unique_cards_per_ip': 8, 'is_datacenter_ip': 1, 'accounts_per_device_24h': 6}
Response: {'raw_anomaly_score': -0.048444853651749664, 'prediction': 1, 'action_required': 'CHALLENGE_CAPTCHA'}
✔ Advanced Bad User Test Passed: User was CHALLENGED with CAPTCHA.

Shutting down and freeing model resources.
🎉 All tests passed successfully!
```

---

## How to Run & Deploy

Follow these steps to run the application locally:

### 1. Activate the Virtual Environment
Navigate to `/Users/manishkumar/ML-projects/anomaly-detection-isoforest` in your terminal and run:
```bash
source .venv/bin/activate
```

### 2. Run the FastAPI Server
Launch the FastAPI development server using `uvicorn`:
```bash
uvicorn main:app --reload
```
Once started, the API is available at `http://127.0.0.1:8000`. You can visit `http://127.0.0.1:8000/docs` to view the interactive Swagger UI API documentation.

### 3. Verify Live API with `test_api.py`
With the uvicorn server running in one terminal, run the test script in another terminal against the running server:
```bash
python test_api.py http://127.0.0.1:8000
```

### 4. Swapping out the Training Data
To train the model on your actual transactional records, simply replace the `/Users/manishkumar/ML-projects/anomaly-detection-isoforest/card_fraud_data.csv` file with your dataset. Ensure that it contains these 5 header columns:
1. `seconds_since_page_load`
2. `failed_attempts_past_hour`
3. `unique_cards_per_ip`
4. `is_datacenter_ip`
5. `accounts_per_device_24h`
Whenever the FastAPI server restarts, the updated CSV data will be automatically read and the model retrained.
