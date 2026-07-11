## 💳 Real-Time Card-Testing Detection Layer

### 💡 Concept

This microservice provides a real-time, unsupervised anomaly detection layer designed to catch card-testing fraud during the "Add Card" flow. By evaluating user behavior and network footprint simultaneously, it identifies automated botnets and advanced fraudsters before a transaction is attempted.

### 🌲 Why Isolation Forest?

* **Unsupervised Advantage:** Fraud tactics change constantly. Isolation Forest doesn't rely on historical labels of "known fraud"; instead, it explicitly isolates unusual data points by randomly partitioning features.
* **Speed:** It has a low memory footprint and fast inference time, making it ideal for blocking attacks in the synchronous checkout path.
* **Linear Scaling:** It handles high-dimensional data efficiently, allowing us to easily add more behavioral features later.

### 📊 Feature Engineering

The model evaluates 5 distinct dimensions to score an incoming request:

1. `seconds_since_page_load` ⏱️: Identifies rapid, script-driven bot behavior versus human pacing.
2. `failed_attempts_past_hour` ❌: Tracks velocity of errors on the payment gateway.
3. `unique_cards_per_ip` 💳: Catches distributed card-testing attacks originating from a single node.
4. `is_datacenter_ip` 🏢: Instantly flags non-residential infrastructure (VPNs, cloud servers).
5. `accounts_per_device_24h` 📱: Detects device fingerprint recycling across multiple user accounts.

### ⚙️ Core Hyperparameters & Scoring

* **Contamination (`0.10`)**: Anchors the model to flag the top 10% most anomalous traffic by default.
* **Decision Boundary (`0.0`)**: The mathematical cutoff where scores below `0.0` represent anomalies.
* **Dynamic Thresholding**: The backend utilizes the raw `decision_function` score rather than a binary prediction. This allows the engineering team to shift the threshold dynamically (e.g., relaxing it to `-0.02` during peak shopping hours) to minimize False Positives without retraining the model.

# Walkthrough: Decoupled FastAPI & Model Pipeline

The fraud detection codebase is modularized so that the web framework, schemas, data-handling pipelines, and validation scripts are entirely decoupled.

## Decoupled Architecture

The files in `/Users/manishkumar/ML-projects/anomaly-detection-isoforest` are organized as follows:

1. **[schemas.py](file:///Users/manishkumar/ML-projects/anomaly-detection-isoforest/schemas.py)**: Contains the Pydantic data schemas `CardAnalyzeRequest` and `CardAnalyzeResponse`.
2. **[data_loader.py](file:///Users/manishkumar/ML-projects/anomaly-detection-isoforest/data_loader.py)**: Scans the workspace directory and loads the training CSV file into a pandas DataFrame.
3. **[train.py](file:///Users/manishkumar/ML-projects/anomaly-detection-isoforest/train.py)**: Fits the scikit-learn `IsolationForest` model on the loaded DataFrame and saves it as `model.joblib`.
4. **[model_loader.py](file:///Users/manishkumar/ML-projects/anomaly-detection-isoforest/model_loader.py)**: Loads `model.joblib` from disk into memory.
5. **[app.py](file:///Users/manishkumar/ML-projects/anomaly-detection-isoforest/app.py)**: Implements the FastAPI web application, defines the endpoint routing, and utilizes `model_loader` inside its lifespan startup event.
6. **[main.py](file:///Users/manishkumar/ML-projects/anomaly-detection-isoforest/main.py)**: The main pipeline runner. When executed, it performs:
   - **Step 1**: Load CSV data.
   - **Step 2**: Train the Isolation Forest model.
   - **Step 3**: Verify loading the model.
   - **Step 4**: Starts the Uvicorn web server programmatically.
7. **[iso-training-data.csv](file:///Users/manishkumar/ML-projects/anomaly-detection-isoforest/iso-training-data.csv)**: Training dataset containing normal and carding transaction entries.
8. **[test_api.py](file:///Users/manishkumar/ML-projects/anomaly-detection-isoforest/test_api.py)**: A test client that dynamically reads `iso-training-data.csv` to find real standard and bad user records, and issues HTTP requests to verify classification output.

---

## Testing with Swagger UI (Interactive Testing)

FastAPI provides an out-of-the-box interactive Swagger interface. Follow these steps to manually test endpoints in your web browser:

### Step 1: Start the API server
From your terminal, activate the environment and run:
```bash
python main.py
```
This will train the model, save the `model.joblib` file, and start hosting the API at `http://127.0.0.1:8000`.

### Step 2: Open Swagger UI in Browser
Open your browser and navigate to:
[http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)

### Step 3: Expand the `/add-card/analyze` Endpoint
* Under the **Fraud Detection** group, click on the **POST `/add-card/analyze`** bar. This will expand a detailed panel showing the request requirements, parameter descriptions, constraints (e.g. `is_datacenter_ip` values must be between `0` and `1`), and the response schema layout.

### Step 4: Click the "Try it out" Button
* In the expanded panel, click the **"Try it out"** button in the upper right. This enables the request body JSON text field.
* A default template payload is pre-filled:
  ```json
  {
    "seconds_since_page_load": 12.4,
    "failed_attempts_past_hour": 1,
    "unique_cards_per_ip": 1,
    "is_datacenter_ip": 0,
    "accounts_per_device_24h": 1
  }
  ```

### Step 5: Edit the Payload and Execute
You can simulate different scenarios directly in the JSON editor box:
* **Standard User simulation**: Set `seconds_since_page_load` to `15.0`, `failed_attempts_past_hour` to `0`, and `is_datacenter_ip` to `0`.
* **Carding Bot simulation**: Set `seconds_since_page_load` to `0.2`, `failed_attempts_past_hour` to `20`, and `is_datacenter_ip` to `1`.
Click the blue **"Execute"** button below the text box.

### Step 6: Inspect the Response
Scroll down to the **Responses** section to view:
* **Response Body**: The API's response payload containing the `raw_anomaly_score` (from `decision_function`), the binary `prediction` (outlier = `1`, normal = `0`), and the `action_required` (e.g. `"CHALLENGE_CAPTCHA"` or `"ALLOW"`).
* **Server Headers & Latency**: Details about response content-type, encoding, and the transaction execution duration.

---

## Dynamic Verification Suite (`test_api.py`)

Rather than relying on static mock payloads, `test_api.py` reads [iso-training-data.csv](file:///Users/manishkumar/ML-projects/anomaly-detection-isoforest/iso-training-data.csv) dynamically to extract real test cases from your training dataset:
1. **Standard User extraction**: It scans the CSV for a record where `failed_attempts_past_hour == 0`, `is_datacenter_ip == 0`, and `unique_cards_per_ip == 1`.
2. **Bad User extraction**: It scans the CSV for a record where `failed_attempts_past_hour >= 15`, `unique_cards_per_ip >= 5`, and `is_datacenter_ip == 1`.
3. **HTTP post and verification**: Once these records are parsed and mapped to floats/integers, they are sent to the running API server using `httpx` to verify model performance and business action routing.

### To Run the Verification tests:
With the server running in one terminal window, open a separate terminal window and run:
```bash
source .venv/bin/activate
python test_api.py
```
This will print confirmation logs showing the extracted CSV values and the validation outcomes.
