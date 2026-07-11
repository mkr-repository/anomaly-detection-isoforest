# Import os module to check for CSV training file existence
import os
# Import sys module to control exit code statuses on validation failures
import sys
# Import csv module to parse transaction records from the training CSV
import csv
# Import httpx library to make high-performance HTTP requests to the FastAPI endpoints
import httpx

# Define helper to extract real payloads directly from the training CSV file
def load_payloads_from_csv(csv_filename="iso-training-data.csv"):
    """
    Reads the training CSV file and extracts one standard user sample
    and one malicious bad user sample to be used as test inputs.
    """
    # Initialize default search target path
    csv_path = csv_filename
    # If the file is not in current directory, check script absolute directory
    if not os.path.exists(csv_path):
        # Calculate absolute directory location of this script
        script_dir = os.path.dirname(os.path.abspath(__file__))
        # Build path pointing to CSV file inside the script folder
        csv_path = os.path.join(script_dir, csv_filename)
        
    # Check if the training CSV remains missing
    if not os.path.exists(csv_path):
        # Log missing file error description and terminate process
        print(f"❌ Error: Cannot find '{csv_filename}' in current directory or script folder.")
        sys.exit(1)
        
    # Initialize variables to hold test cases
    standard_user = None
    bad_user = None
    
    # Open CSV file using standard context manager
    with open(csv_path, mode="r", encoding="utf-8") as f:
        # Instantiate DictReader to automatically parse header row
        reader = csv.DictReader(f)
        # Iterate over each row dictionary in the CSV
        for row in reader:
            # Map string cell values to corresponding float and integer types
            mapped_row = {
                "seconds_since_page_load": float(row["seconds_since_page_load"]),
                "failed_attempts_past_hour": int(row["failed_attempts_past_hour"]),
                "unique_cards_per_ip": int(row["unique_cards_per_ip"]),
                "is_datacenter_ip": int(row["is_datacenter_ip"]),
                "accounts_per_device_24h": int(row["accounts_per_device_24h"])
            }
            
            # Condition for Standard User: 0 failed attempts, residential/mobile IP, and 1 card
            if (mapped_row["failed_attempts_past_hour"] == 0 and 
                mapped_row["is_datacenter_ip"] == 0 and 
                mapped_row["unique_cards_per_ip"] == 1 and 
                standard_user is None):
                # Save standard user test case payload
                standard_user = mapped_row
                
            # Condition for Malicious User: high failed attempts (>= 15), high cards (>= 5), and datacenter IP
            if (mapped_row["failed_attempts_past_hour"] >= 15 and 
                mapped_row["unique_cards_per_ip"] >= 5 and 
                mapped_row["is_datacenter_ip"] == 1 and 
                bad_user is None):
                # Save malicious bad user test case payload
                bad_user = mapped_row
                
            # Break early if both test cases have been identified
            if standard_user is not None and bad_user is not None:
                break
                
    # Fallback to defaults if standard user sample is not found in CSV
    if not standard_user:
        standard_user = {
            "seconds_since_page_load": 13.16,
            "failed_attempts_past_hour": 0,
            "unique_cards_per_ip": 1,
            "is_datacenter_ip": 0,
            "accounts_per_device_24h": 1
        }
    # Fallback to defaults if malicious user sample is not found in CSV
    if not bad_user:
        bad_user = {
            "seconds_since_page_load": 0.91,
            "failed_attempts_past_hour": 23,
            "unique_cards_per_ip": 10,
            "is_datacenter_ip": 1,
            "accounts_per_device_24h": 1
        }
        
    # Return both extracted test payload dictionaries
    return standard_user, bad_user

# Define testing routine taking target server location URL
def run_tests(base_url="http://127.0.0.1:8000"):
    # Output testing header information to logs
    print("====================================================")
    print(f"Testing live FastAPI Server at {base_url}")
    print("====================================================\n")
    
    # Load dynamically parsed payloads from the training CSV
    standard_payload, bad_payload = load_payloads_from_csv("iso-training-data.csv")
    print(f"✔ Successfully extracted test samples from 'iso-training-data.csv'.")
    
    # Initialize connection logic to communicate with FastAPI server
    try:
        # Instantiate HTTPX client setting base URL and 5 second connection timeout limit
        with httpx.Client(base_url=base_url, timeout=5.0) as client:
            
            # Test Case 1: Status Health-check
            print("[Test 1/3] Testing GET / ...")
            # Issue GET request to API root status URL
            response = client.get("/")
            # Verify server successfully answered with HTTP status 200 OK
            assert response.status_code == 200, f"Failed with status: {response.status_code}"
            # Extract returned status variables dict from response body
            root_data = response.json()
            # Output server root data details to testing log
            print(f"Response: {root_data}")
            # Confirm API status is reporting active
            assert root_data.get("status") == "active", "Service status should be active"
            # Confirm model startup lifecycle completed and loaded model in memory
            assert root_data.get("model_loaded") is True, "Model should be loaded on the server"
            # Print verification completion check
            print("✔ Root endpoint validation successful.\n")
            
            # Test Case 2: Standard user behavior check (expected to be allowed)
            print("[Test 2/3] Testing Standard User (Expecting ALLOW) ...")
            # Log exact payload values being posted
            print(f"Payload: {standard_payload}")
            # Send payload via POST request to evaluation endpoint
            response = client.post("/add-card/analyze", json=standard_payload)
            # Confirm HTTP status code is 200
            assert response.status_code == 200, f"Failed with status: {response.status_code} - {response.text}"
            # Parse output dict values
            std_data = response.json()
            # Log API output variables
            print(f"Response: {std_data}")
            # Assert model prediction is normal (prediction = 0)
            assert std_data["prediction"] == 0, f"Expected prediction 0, got {std_data['prediction']}"
            # Assert mitigation recommendation allows transaction (action_required = 'ALLOW')
            assert std_data["action_required"] == "ALLOW", f"Expected action 'ALLOW', got {std_data['action_required']}"
            # Log success status
            print("✔ Standard user validation successful.\n")
            
            # Test Case 3: Bad user card-testing fraud behavior (expected to be blocked)
            print("[Test 3/3] Testing Advanced Bad User (Expecting CHALLENGE_CAPTCHA) ...")
            # Log bad transaction payload inputs
            print(f"Payload: {bad_payload}")
            # Send mock bot payload data via POST request
            response = client.post("/add-card/analyze", json=bad_payload)
            # Confirm HTTP status code is 200
            assert response.status_code == 200, f"Failed with status: {response.status_code} - {response.text}"
            # Parse evaluation outputs
            bad_data = response.json()
            # Log server output variables
            print(f"Response: {bad_data}")
            # Assert model prediction flags anomaly (prediction = 1)
            assert bad_data["prediction"] == 1, f"Expected prediction 1, got {bad_data['prediction']}"
            # Assert security rules block transaction with CAPTCHA (action_required = 'CHALLENGE_CAPTCHA')
            assert bad_data["action_required"] == "CHALLENGE_CAPTCHA", f"Expected action 'CHALLENGE_CAPTCHA', got {bad_data['action_required']}"
            # Log success status
            print("✔ Advanced bad user validation successful.\n")
            
        # Output final test suite success statement
        print("🎉 All API server integration tests passed successfully!")
        
    # Catch networking failure if local server is offline
    except httpx.ConnectError:
        # Output troubleshooting suggestion to logs
        print(f"❌ Connection Error: Could not connect to FastAPI server at {base_url}.")
        print("Please verify the server is running by executing: python main.py")
        # Exit process with error code
        sys.exit(1)
    # Catch validation assertion mismatches
    except AssertionError as ae:
        # Print failure output details
        print(f"❌ Assert Failure: {ae}")
        # Exit process with error code
        sys.exit(1)
    # Catch unexpected code failures
    except Exception as e:
        # Log failure message
        print(f"❌ Unexpected error occurred during tests: {e}")
        # Exit process with error code
        sys.exit(1)

# Check if script executed directly in shell
if __name__ == "__main__":
    # Read target location url if passed in CLI args; otherwise connect to localhost port 8000
    url_arg = sys.argv[1] if len(sys.argv) > 1 else "http://127.0.0.1:8000"
    # Initiate testing client execution flow
    run_tests(url_arg)
