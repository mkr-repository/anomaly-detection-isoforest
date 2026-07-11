# Import pandas under pd alias to structure request dictionary data into model-compatible DataFrames
import pandas as pd
# Import asynccontextmanager decorator to register server startup and shutdown lifespan hooks
from contextlib import asynccontextmanager
# Import FastAPI application class, HTTPException handler, and status codes module
from fastapi import FastAPI, HTTPException, status
# Import Pydantic schemas from schemas.py to validate API input requests and output responses
from schemas import CardAnalyzeRequest, CardAnalyzeResponse
# Import load_model function to handle deserialization of the saved model.joblib file
from model_loader import load_model

# Define lifespan async context manager to handle startup model loading and server shutdown cleanup
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Try loading the saved model file on application start
    try:
        # Load model and assign to app.state.model so it persists in-memory globally
        app.state.model = load_model()
    # Catch any exception if model.joblib is missing or corrupted
    except Exception as e:
        # Print diagnostic warning details to standard output logs
        print(f"[App Lifespan] WARNING: Could not load trained model on startup: {e}")
        print("[App Lifespan] Please run the main.py pipeline first to train and generate model.joblib.")
        # Store model state as None so endpoints report unavailable status instead of crashing
        app.state.model = None
    # Yield control to FastAPI app to begin serving client requests
    yield
    # Log shutdown confirmation once uvicorn shuts down
    print("[App Lifespan] Server shutting down, releasing model resources.")

# Instantiate FastAPI application, applying custom metadata and startup lifespan manager
app = FastAPI(
    title="Card-Testing Fraud Detection API",
    description="Real-time card fraud detection using unsupervised Isolation Forest.",
    version="1.0.0",
    lifespan=lifespan
)

# Route definitions: Root URL GET endpoint returning API status information
@app.get("/", tags=["General"])
async def root():
    # Return service availability flag and model loading state
    return {
        "message": "Welcome to the Card-Testing Fraud Detection API",
        "status": "active",
        # Evaluate if the Isolation Forest model has been successfully loaded into memory
        "model_loaded": hasattr(app.state, "model") and app.state.model is not None,
        "docs_url": "/docs"
    }

# Route definitions: Card analysis POST endpoint receiving input data and returning model scoring
@app.post(
    "/add-card/analyze", 
    response_model=CardAnalyzeResponse, # Asserts response matches output schema rules
    status_code=status.HTTP_200_OK,     # Sets default response header status code
    tags=["Fraud Detection"]            # Categorizes route within Swagger UI
)
async def analyze_card(request: CardAnalyzeRequest):
    # Verify model is available in application state memory
    if not hasattr(app.state, "model") or app.state.model is None:
        # Return HTTP 503 if API client requests evaluation before model is trained
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Model is not trained or loaded. Please run the main.py pipeline first."
        )
    
    # Construct a single-row DataFrame using keys matching model feature expectation
    features_df = pd.DataFrame([{
        "seconds_since_page_load": request.seconds_since_page_load,
        "failed_attempts_past_hour": request.failed_attempts_past_hour,
        "unique_cards_per_ip": request.unique_cards_per_ip,
        "is_datacenter_ip": request.is_datacenter_ip,
        "accounts_per_device_24h": request.accounts_per_device_24h
    }])
    
    # Process prediction variables in error-handling block
    try:
        # Fetch decision boundary distance from Isolation Forest model (outliers yield negative values)
        raw_anomaly_score = float(app.state.model.decision_function(features_df)[0])
        
        # Isolation Forest prediction: normal instances yield 1, abnormal yield -1
        clf_prediction = app.state.model.predict(features_df)[0]
        
        # Map predictions: assign 1 if outlier (-1), assign 0 if inlier (1)
        prediction = 1 if clf_prediction == -1 else 0
        
        # Business logic rule: issue CAPTCHA challenge if flagged as anomaly, else ALLOW
        action_required = "CHALLENGE_CAPTCHA" if clf_prediction < -0.02 else "ALLOW"
        
        # Construct and return validated response payload
        return CardAnalyzeResponse(
            raw_anomaly_score=raw_anomaly_score,
            prediction=prediction,
            action_required=action_required
        )
    # Catch any scoring runtime errors
    except Exception as e:
        # Raise HTTP 500 indicating code encountered a model calculation failure
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Inference error: {str(e)}"
        )
