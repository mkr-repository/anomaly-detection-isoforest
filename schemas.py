# Import the BaseModel class from Pydantic for standard JSON schema object modeling
from pydantic import BaseModel
# Import Field helper from Pydantic to apply validation constraints and metadata to fields
from pydantic import Field

# Define the Pydantic input request validation schema inheriting from BaseModel
class CardAnalyzeRequest(BaseModel):
    # Validate 'seconds_since_page_load' as float with description; '...' specifies this field is required
    seconds_since_page_load: float = Field(
        ..., 
        description="Seconds since page load. Lower values may indicate programmatic bot activity."
    )
    # Validate 'failed_attempts_past_hour' as integer with description; '...' specifies this field is required
    failed_attempts_past_hour: int = Field(
        ..., 
        description="Number of failed attempts in the past hour. High values indicate carding attempts."
    )
    # Validate 'unique_cards_per_ip' as integer with description; '...' specifies this field is required
    unique_cards_per_ip: int = Field(
        ..., 
        description="Number of unique card numbers seen from this IP. High values indicate card-testing."
    )
    # Validate 'is_datacenter_ip' as integer; '...' specifies required; constraints limit input to 0 or 1
    is_datacenter_ip: int = Field(
        ..., 
        description="1 if the IP belongs to a datacenter, 0 otherwise.",
        ge=0, # Must be greater than or equal to 0
        le=1  # Must be less than or equal to 1
    )
    # Validate 'accounts_per_device_24h' as integer with description; '...' specifies this field is required
    accounts_per_device_24h: int = Field(
        ..., 
        description="Number of distinct accounts accessed from this device in the last 24h."
    )

    # Configuration mapping for Pydantic schema generation
    model_config = {
        # Custom mock payload example displayed in FastAPI Swagger UI docs
        "json_schema_extra": {
            "example": {
                "seconds_since_page_load": 12.4,
                "failed_attempts_past_hour": 1,
                "unique_cards_per_ip": 1,
                "is_datacenter_ip": 0,
                "accounts_per_device_24h": 1
            }
        }
    }

# Define the Pydantic response serialization schema inheriting from BaseModel
class CardAnalyzeResponse(BaseModel):
    # Validate 'raw_anomaly_score' as float; represents raw distance from forest split frontier
    raw_anomaly_score: float = Field(
        ..., 
        description="Raw anomaly score from the Isolation Forest's decision_function. Lower is more anomalous."
    )
    # Validate 'prediction' as integer; represents final class assignment (1 = flagged, 0 = normal)
    prediction: int = Field(
        ..., 
        description="Prediction: 1 means anomaly/flagged (fraudulent pattern), 0 means normal."
    )
    # Validate 'action_required' as string; represents business rule outcome ('CHALLENGE_CAPTCHA' or 'ALLOW')
    action_required: str = Field(
        ..., 
        description="Recommended fraud mitigation action: 'CHALLENGE_CAPTCHA' or 'ALLOW'."
    )

    # Configuration mapping for Pydantic response schema generation
    model_config = {
        # Custom mock response structure displayed in FastAPI Swagger UI docs
        "json_schema_extra": {
            "example": {
                "raw_anomaly_score": 0.1245,
                "prediction": 0,
                "action_required": "ALLOW"
            }
        }
    }
