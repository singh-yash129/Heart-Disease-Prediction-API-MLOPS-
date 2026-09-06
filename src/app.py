"""
app.py — FastAPI application for Heart Disease Prediction API
Deliverable 4: Dockerized API | Deliverable 5: Per-sample logging
"""
import os
import uuid
from datetime import datetime, timezone
from typing import List

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from src.predict import load_model, predict_single
from src.logging_config import get_logger

# ── App Setup ─────────────────────────────────────────────────────────────────
app = FastAPI(
    title="Heart Disease Prediction API",
    description="Production-ready ML API for heart disease classification on GKE",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Load model once at startup ────────────────────────────────────────────────
MODEL = None
FEATURE_COLS = None
logger = get_logger("heart-disease-api")


@app.on_event("startup")
def startup_event():
    global MODEL, FEATURE_COLS
    MODEL, FEATURE_COLS = load_model()
    logger.info("Model loaded successfully", feature_cols=FEATURE_COLS)


# ── Schemas ───────────────────────────────────────────────────────────────────
class PatientFeatures(BaseModel):
    age:      float = Field(..., example=63,    description="Age in years")
    gender:   str   = Field(..., example="male", description="male or female")
    cp:       float = Field(..., example=3,    description="Chest pain type (0-3)")
    trestbps: float = Field(..., example=145.0, description="Resting blood pressure (mmHg)")
    chol:     float = Field(..., example=233.0, description="Serum cholesterol (mg/dl)")
    fbs:      float = Field(..., example=1,    description="Fasting blood sugar >120 mg/dl (0/1)")
    restecg:  float = Field(..., example=0,    description="Resting ECG results (0/1/2)")
    thalach:  float = Field(..., example=150.0, description="Max heart rate achieved")
    exang:    float = Field(..., example=0,    description="Exercise induced angina (0/1)")
    oldpeak:  float = Field(..., example=2.3,  description="ST depression induced by exercise")
    slope:    float = Field(..., example=0,    description="Slope of peak exercise ST segment")
    ca:       float = Field(..., example=0,    description="Major vessels colored by fluoroscopy (0-3)")
    thal:     float = Field(..., example=1,    description="Thal: 0=normal; 1=fixed defect; 2=reversable defect")

    class Config:
        json_schema_extra = {
            "example": {
                "age": 63, "gender": "male", "cp": 3,
                "trestbps": 145.0, "chol": 233.0, "fbs": 1,
                "restecg": 0, "thalach": 150.0, "exang": 0,
                "oldpeak": 2.3, "slope": 0, "ca": 0, "thal": 1
            }
        }


class PredictionResponse(BaseModel):
    request_id:       str
    prediction:       int
    prediction_label: str
    probability:      float
    timestamp:        str


class BatchPredictionResponse(BaseModel):
    results: List[PredictionResponse]
    total:   int


# ── Endpoints ─────────────────────────────────────────────────────────────────
@app.get("/", tags=["Info"])
def root():
    return {
        "service": "Heart Disease Prediction API",
        "version": "1.0.0",
        "status": "running",
        "docs": "/docs",
    }


@app.get("/health", tags=["Health"])
def health_check():
    """Kubernetes liveness & readiness probe."""
    if MODEL is None:
        raise HTTPException(status_code=503, detail="Model not loaded")
    return {"status": "healthy", "model_loaded": True}


@app.post("/predict", response_model=PredictionResponse, tags=["Prediction"])
def predict(patient: PatientFeatures):
    """
    Single-sample prediction with GCP Cloud Logging.
    Deliverable 5: each call logs input features + output + timestamp.
    """
    request_id = str(uuid.uuid4())
    timestamp  = datetime.now(timezone.utc).isoformat()

    try:
        result = predict_single(MODEL, FEATURE_COLS, patient.model_dump())
    except Exception as e:
        logger.error("Prediction failed", request_id=request_id, error=str(e))
        raise HTTPException(status_code=500, detail=str(e))

    # ── Structured log for GCP Cloud Logging (Deliverable 5) ─────────────────
    log_payload = {
        "request_id":       request_id,
        "timestamp":        timestamp,
        "input_features":   patient.model_dump(),
        "prediction":       result["prediction"],
        "prediction_label": result["prediction_label"],
        "probability":      result["probability"],
    }
    logger.log_struct(log_payload, severity="INFO")

    return PredictionResponse(
        request_id=request_id,
        prediction=result["prediction"],
        prediction_label=result["prediction_label"],
        probability=result["probability"],
        timestamp=timestamp,
    )


@app.post("/predict/batch", response_model=BatchPredictionResponse, tags=["Prediction"])
def predict_batch(patients: List[PatientFeatures]):
    """Batch predictions — processes list of patients."""
    results = []
    for patient in patients:
        request_id = str(uuid.uuid4())
        timestamp  = datetime.now(timezone.utc).isoformat()
        try:
            result = predict_single(MODEL, FEATURE_COLS, patient.model_dump())
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

        log_payload = {
            "request_id":     request_id,
            "timestamp":      timestamp,
            "input_features": patient.model_dump(),
            **result,
        }
        logger.log_struct(log_payload, severity="INFO")

        results.append(PredictionResponse(
            request_id=request_id,
            prediction=result["prediction"],
            prediction_label=result["prediction_label"],
            probability=result["probability"],
            timestamp=timestamp,
        ))

    return BatchPredictionResponse(results=results, total=len(results))


@app.get("/features", tags=["Info"])
def get_features():
    """Return expected feature names and order."""
    return {"feature_columns": FEATURE_COLS}
