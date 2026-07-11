# Import os module to handle file checks and dynamic folder navigation for payload loading
import os
# Import sys module to control exit codes on test assertion failures
import sys
# Import json library to parse test payload properties from the static JSON file
import json
# Import httpx library to make HTTP requests (GET/POST) to query the FastAPI server endpoints
import httpx

# Define testing routine taking target server location URL
def run_tests(base_url="http://127.0.0.1:8000"):
    # Output testing header information to logs
    print("====================================================")
    print(f"Testing live FastAPI Server at {base_url}")
    print("====================================================\n")
    
    # Establish target name of the payloads metadata file
    payload_file = "sample_payloads.json"
    # If the file doesn't exist in current directory, check script absolute directory path
    if not os.path.exists(payload_file):
        # Calculate absolute directory location of this script
        script_dir = os.path.dirname(os.path.abspath(__file__))
        # Build path pointing to payload file inside the script folder
        payload_file = os.path.join(script_dir, "sample_payloads.json")
        
    # Check if payload file remains missing after path scans
    if not os.path.exists(payload_file):
        # Log missing file error description and terminate process
        print(f"❌ Error: Cannot find 'sample_payloads.json' in current directory or script folder.")
        sys.exit(1)
        
    # Read and decode JSON file containing sample inputs
    try:
        # Load file stream in read-only mode
        with open(payload_file, "r") as f:
            # Parse payload data text as JSON object dictionary
            payloads = json.load(f)
    # Catch syntax error or IO read error
    except Exception as e:
        # Log parse error details to the test outputs
        print(f"❌ Error reading JSON payload file: {e}")
        # Exit process with failure status code
        sys.exit(1)
        
    # Extract standard and malicious user dict structures from parent dictionary
    standard_payload = payloads.get("standard_user")
    bad_payload = payloads.get("bad_user")
    
    # Check if either test case payload was missing from JSON structure
    if not standard_payload or not bad_payload:
        # Print warning indicating missing keys
        print("❌ Error: Sample payloads must contain keys 'standard_user' and 'bad_user'.")
        # Exit process
        sys.exit(1)
        
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
        # Output failure details
        print(f"❌ Assert Failure: {ae}")
        # Exit process with error code
        sys.exit(1)
    # Catch unexpected code failures
    except Exception as e:
        # Output general troubleshooting log
        print(f"❌ Unexpected error occurred during tests: {e}")
        # Exit process with error code
        sys.exit(1)

# Check if script executed directly in shell
if __name__ == "__main__":
    # Read target location url if passed in CLI args; otherwise connect to localhost port 8000
    url_arg = sys.argv[1] if len(sys.argv) > 1 else "http://127.0.0.1:8000"
    # Initiate testing client execution flow
    run_tests(url_arg)
