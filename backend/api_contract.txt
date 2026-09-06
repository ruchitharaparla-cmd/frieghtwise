# FreightWise API Contract

**Status:** Initial Development Contract  
**Version:** 1.0  
**Backend:** FastAPI  
**Frontend:** React  
**Database:** PostgreSQL  
**Purpose:** Define the interface between the FreightWise frontend, backend, decision engine, and ML components.

---

# 1. API Overview

FreightWise uses the following architecture:

```text
React Frontend
      |
      | HTTP / JSON
      ↓
FastAPI Backend
      |
      ├── Authentication
      ├── Voyage Management
      ├── Port Intelligence
      ├── Vessel Intelligence
      ├── Freight Forecasting
      ├── Cost Engine
      ├── Risk Engine
      ├── Decision Engine
      └── What-if Simulation
      |
      ├───────────────┐
      ↓               ↓
PostgreSQL        ML Models
                    |
                    ↓
              Forecast Results
```

The frontend must communicate with the backend through the APIs defined in this document.

The frontend must **not** directly access PostgreSQL.

---

# 2. Base URL

## Development

```text
http://127.0.0.1:8000
```

## Production

The production URL will be defined during deployment.

Example:

```text
https://api.freightwise.example
```

The frontend should use an environment variable:

```env
VITE_API_URL=http://127.0.0.1:8000
```

---

# 3. API Format

All request and response bodies use JSON unless otherwise specified.

```http
Content-Type: application/json
```

Successful responses use standard HTTP status codes.

Common status codes:

| Status | Meaning |
|---|---|
| 200 | Successful request |
| 201 | Resource created |
| 400 | Invalid request |
| 401 | Authentication required/invalid |
| 403 | Insufficient permission |
| 404 | Resource not found |
| 409 | Resource conflict |
| 422 | Validation error |
| 500 | Internal server error |
| 503 | External service unavailable |

---

# 4. Authentication

FreightWise uses JWT-based authentication.

Authenticated requests should include:

```http
Authorization: Bearer <access_token>
```

Authentication endpoints:

```text
POST /auth/register
POST /auth/login
GET  /users/me
```

---

# 5. Health API

## GET /health

Checks whether the backend is running.

### Request

No request body.

### Response

```json
{
  "status": "ok"
}
```

### Status

```text
200 OK
```

---

# 6. Authentication API

## POST /auth/register

Creates a new FreightWise user.

### Request

```json
{
  "email": "user@example.com",
  "password": "secure-password",
  "full_name": "Example User"
}
```

### Fields

| Field | Type | Required | Description |
|---|---|---:|---|
| email | string | Yes | User email |
| password | string | Yes | User password |
| full_name | string | No | User's display name |

### Response

```json
{
  "id": 1,
  "email": "user@example.com",
  "full_name": "Example User",
  "is_active": true
}
```

### Status

```text
201 Created
```

---

# 7. Login API

## POST /auth/login

Authenticates a user and returns a JWT access token.

### Request

```json
{
  "email": "user@example.com",
  "password": "secure-password"
}
```

### Response

```json
{
  "access_token": "<jwt-token>",
  "token_type": "bearer"
}
```

### Status

```text
200 OK
```

---

# 8. Current User API

## GET /users/me

Returns information about the currently authenticated user.

### Headers

```http
Authorization: Bearer <access_token>
```

### Response

```json
{
  "id": 1,
  "email": "user@example.com",
  "full_name": "Example User",
  "is_active": true
}
```

---

# 9. Voyage API

A voyage represents the cargo movement scenario that FreightWise is evaluating.

## POST /voyages

Creates a new voyage scenario.

### Request

```json
{
  "cargo_type": "coal",
  "quantity_tonnes": 75000,
  "origin_country": "Australia",
  "destination_region": "East Coast India",
  "arrival_date": "2026-09-20",
  "charter_start_date": "2026-09-10",
  "charter_end_date": "2026-09-15"
}
```

### Fields

| Field | Type | Required | Description |
|---|---|---:|---|
| cargo_type | string | Yes | Type of bulk cargo |
| quantity_tonnes | number | Yes | Cargo quantity in tonnes |
| origin_country | string | Yes | Cargo loading country/region |
| destination_region | string | Yes | Target destination region |
| arrival_date | date | Yes | Required cargo arrival date |
| charter_start_date | date | No | Earliest acceptable charter date |
| charter_end_date | date | No | Latest acceptable charter date |

### Response

```json
{
  "id": 1,
  "cargo_type": "coal",
  "quantity_tonnes": 75000,
  "origin_country": "Australia",
  "destination_region": "East Coast India",
  "arrival_date": "2026-09-20",
  "status": "created"
}
```

---

# 10. Port API

Ports are evaluated using operational and physical constraints.

## GET /ports

Returns available ports.

### Optional Query Parameters

```text
?region=East Coast India
?cargo_type=coal
```

### Example

```http
GET /ports?region=East%20Coast%20India&cargo_type=coal
```

### Response

```json
{
  "ports": [
    {
      "id": 1,
      "name": "Visakhapatnam",
      "code": "INVTZ",
      "state": "Andhra Pradesh",
      "country": "India"
    }
  ]
}
```

---

# 11. Port Details API

## GET /ports/{port_id}

Returns detailed information about a port.

### Example

```http
GET /ports/1
```

### Response

```json
{
  "id": 1,
  "name": "Visakhapatnam",
  "code": "INVTZ",
  "state": "Andhra Pradesh",
  "country": "India",
  "latitude": 17.7,
  "longitude": 83.3,
  "max_draft_m": null,
  "max_loa_m": null,
  "max_beam_m": null,
  "annual_capacity_tonnes": null,
  "utilization_percent": null,
  "average_waiting_hours": null
}
```

Values should be `null` when reliable data is unavailable.

**The backend must not fabricate missing port data.**

---

# 12. Vessel API

## GET /vessels

Returns vessels or vessel candidates available to the decision engine.

### Optional Parameters

```text
?vessel_class=Panamax
?cargo_type=coal
?quantity_tonnes=75000
```

### Response

```json
{
  "vessels": [
    {
      "id": 1,
      "name": "Example Vessel",
      "vessel_class": "Panamax",
      "dwt": 75000,
      "loa_m": 225,
      "beam_m": 32,
      "draft_m": 13.5
    }
  ]
}
```

---

# 13. Vessel-Port Compatibility API

This is a deterministic rule-based component.

## POST /compatibility

Checks whether a vessel can physically and operationally use a selected port.

### Request

```json
{
  "vessel_id": 1,
  "port_id": 1,
  "cargo_type": "coal"
}
```

### Response

```json
{
  "vessel_id": 1,
  "port_id": 1,
  "feasible": true,
  "checks": {
    "loa": true,
    "beam": true,
    "draft": true,
    "cargo": true
  },
  "reasons": []
}
```

---

# 14. Incompatible Vessel Example

If a vessel fails a hard constraint:

```json
{
  "vessel_id": 2,
  "port_id": 1,
  "feasible": false,
  "checks": {
    "loa": true,
    "beam": true,
    "draft": false,
    "cargo": true
  },
  "reasons": [
    {
      "factor": "draft",
      "message": "Vessel draft exceeds the permitted port draft."
    }
  ]
}
```

A vessel that fails a hard physical constraint should not be ranked as a feasible candidate.

---

# 15. Freight Forecast API

The freight forecast API provides the predicted freight-rate signal used by the decision engine.

## POST /forecast

### Request

```json
{
  "origin_country": "Australia",
  "destination_region": "East Coast India",
  "cargo_type": "coal",
  "vessel_class": "Panamax",
  "forecast_date": "2026-09-20"
}
```

### Response

```json
{
  "forecast_rate": null,
  "currency": "USD",
  "unit": "per_metric_tonne",
  "forecast_date": "2026-09-20",
  "model_version": null,
  "confidence": null
}
```

The values remain `null` until the ML pipeline provides validated predictions.

---

# 16. Forecast Model Interface

The backend should treat the ML model as a separate component.

The backend should not contain model-training logic.

Conceptually:

```text
Backend
   |
   | prediction request
   ↓
ML prediction interface
   |
   ↓
Forecast result
```

Expected prediction structure:

```json
{
  "forecast_rate": 0.0,
  "confidence": 0.0,
  "model_version": "xgboost-v1"
}
```

The actual model interface will be finalized after the ML team completes the first validated model.

---

# 17. Cost Calculation API

## POST /cost

Calculates estimated total voyage cost.

### Request

```json
{
  "quantity_tonnes": 75000,
  "freight_rate": null,
  "bunker_cost": null,
  "port_cost": null,
  "expected_delay_hours": null,
  "demurrage_rate_per_day": null
}
```

### Response

```json
{
  "freight_cost": null,
  "bunker_cost": null,
  "port_cost": null,
  "expected_delay_cost": null,
  "expected_demurrage": null,
  "total_landed_cost": null,
  "currency": "USD"
}
```

Missing values should remain `null` until reliable data is available.

---

# 18. Risk API

## POST /risk

Evaluates operational risks affecting the voyage.

### Request

```json
{
  "port_id": 1,
  "arrival_date": "2026-09-20",
  "vessel_id": 1
}
```

### Response

```json
{
  "overall_risk": null,
  "risk_level": null,
  "factors": [
    {
      "factor": "congestion",
      "score": null,
      "impact": null
    },
    {
      "factor": "weather",
      "score": null,
      "impact": null
    },
    {
      "factor": "demurrage",
      "score": null,
      "impact": null
    }
  ]
}
```

Possible risk levels:

```text
LOW
MEDIUM
HIGH
```

The scoring methodology will be documented separately.

---

# 19. Recommendation API

This is the primary FreightWise decision endpoint.

## POST /recommend

The endpoint evaluates the voyage and returns the recommended chartering strategy.

### Request

```json
{
  "cargo_type": "coal",
  "quantity_tonnes": 75000,
  "origin_country": "Australia",
  "destination_region": "East Coast India",
  "arrival_date": "2026-09-20"
}
```

### Response

```json
{
  "recommendation": {
    "strategy": null,
    "vessel_id": null,
    "port_id": null
  },
  "forecast": {
    "forecast_rate": null,
    "currency": "USD",
    "unit": "per_metric_tonne",
    "confidence": null
  },
  "cost": {
    "total_landed_cost": null,
    "currency": "USD"
  },
  "risk": {
    "overall_risk": null,
    "risk_level": null
  },
  "reasons": [],
  "alternatives": []
}
```

---

# 20. Recommendation Strategies

The decision engine may return one of the following strategies:

```text
BOOK_NOW
WAIT
ALTERNATIVE_PORT
ALTERNATIVE_VESSEL
MULTI_VOYAGE
```

The final strategy must be based on the decision-engine calculations.

It must not be hard-coded simply to produce a demo result.

---

# 21. Recommendation Explanation

Every recommendation should contain reasons.

Example:

```json
{
  "reasons": [
    {
      "factor": "freight",
      "message": "Forecast indicates a potentially higher freight rate closer to the required arrival window."
    },
    {
      "factor": "port",
      "message": "Selected port has suitable vessel restrictions for the candidate vessel."
    },
    {
      "factor": "congestion",
      "message": "Expected waiting exposure is lower than the compared alternative."
    }
  ]
}
```

The frontend will display these reasons to the user.

---

# 22. Alternatives

The recommendation should provide rejected or lower-ranked alternatives whenever sufficient data is available.

Example:

```json
{
  "alternatives": [
    {
      "vessel_id": 2,
      "port_id": 1,
      "strategy": "BOOK_NOW",
      "rank": 2,
      "total_landed_cost": null,
      "risk_level": null,
      "rejection_reasons": [
        "Higher expected delay exposure"
      ]
    }
  ]
}
```

This allows FreightWise to answer:

> Why this option?

and:

> Why not the other option?

---

# 23. What-If Simulation API

The simulator allows the user to modify assumptions and compare scenarios.

## POST /simulation

### Request

```json
{
  "base_scenario": {
    "cargo_type": "coal",
    "quantity_tonnes": 75000,
    "origin_country": "Australia",
    "destination_region": "East Coast India",
    "arrival_date": "2026-09-20"
  },
  "changes": {
    "port_id": 2,
    "vessel_class": "Panamax",
    "charter_date": "2026-09-12"
  }
}
```

### Response

```json
{
  "base_scenario": {
    "total_landed_cost": null,
    "risk_level": null,
    "strategy": null
  },
  "modified_scenario": {
    "total_landed_cost": null,
    "risk_level": null,
    "strategy": null
  },
  "difference": {
    "cost_difference": null,
    "risk_difference": null
  },
  "recommendation_changed": false
}
```

---

# 24. Decision Engine Internal Flow

The recommendation endpoint should conceptually follow this pipeline:

```text
Voyage Input
     |
     ↓
Generate Candidate Vessels
     |
     ↓
Generate Candidate Ports
     |
     ↓
Freight Forecast
     |
     ↓
Vessel-Port Compatibility
     |
     ├── Infeasible → Reject
     |
     ↓
Port Conditions
     |
     ↓
Congestion / Waiting Analysis
     |
     ↓
Weather / External Risk
     |
     ↓
Voyage Cost Calculation
     |
     ↓
Candidate Ranking
     |
     ↓
Charter Strategy
     |
     ↓
Recommendation + Explanation
```

---

# 25. Candidate Ranking

Only feasible candidates should enter the final ranking stage.

Potential ranking factors:

```text
Total Landed Cost
Expected Delay
Operational Risk
Freight Forecast
Port Suitability
Arrival Feasibility
```

The exact weighting must be documented in:

```text
docs/methodology/decision-engine.md
```

Weights must not be silently changed inside frontend code.

---

# 26. Data Availability Rules

FreightWise must distinguish between:

```text
KNOWN
ESTIMATED
UNAVAILABLE
```

Example:

```json
{
  "value": null,
  "status": "UNAVAILABLE"
}
```

or:

```json
{
  "value": 53.41,
  "status": "KNOWN",
  "source": "official_port_statistics"
}
```

Estimated values must be explicitly labelled.

The system must never fabricate missing maritime or port statistics.

---

# 27. Source Metadata

Where practical, data returned by the backend should include source metadata.

Example:

```json
{
  "value": 53.41,
  "unit": "percent",
  "source": {
    "name": "Official Port Statistics",
    "year": "2024-25"
  }
}
```

This is especially important for:

- Port capacity
- Port utilization
- Waiting time
- Cargo traffic
- Vessel restrictions
- Freight data
- Weather data

---

# 28. Error Response Format

All API errors should follow a consistent structure where possible.

Example:

```json
{
  "error": {
    "code": "PORT_NOT_FOUND",
    "message": "The requested port does not exist.",
    "details": null
  }
}
```

Example validation error:

```json
{
  "error": {
    "code": "INVALID_CARGO_QUANTITY",
    "message": "Cargo quantity must be greater than zero.",
    "details": {
      "field": "quantity_tonnes"
    }
  }
}
```

---

# 29. External Service Failures

External services such as weather or maritime-data providers may become unavailable.

The backend should not crash the entire recommendation pipeline when an optional external source fails.

Example:

```json
{
  "weather": {
    "status": "UNAVAILABLE",
    "message": "Weather service temporarily unavailable."
  }
}
```

The recommendation engine should indicate when a recommendation was generated with incomplete external information.

---

# 30. Frontend Integration Rules

The React frontend should:

1. Call FastAPI endpoints.
2. Never connect directly to PostgreSQL.
3. Never contain database credentials.
4. Never contain backend API secrets.
5. Read the API base URL from environment configuration.
6. Handle loading states.
7. Handle API errors.
8. Display unavailable data as unavailable rather than inventing values.

Example:

```javascript
const API_URL = import.meta.env.VITE_API_URL;
```

---

# 31. ML Integration Rules

The ML team owns:

```text
Model training
Feature engineering
Model evaluation
Model serialization
Prediction logic
Model performance tracking
```

The backend owns:

```text
API integration
Input validation
Calling the prediction interface
Storing prediction results
Returning predictions to frontend
```

The backend must not duplicate ML model-training logic.

---

# 32. Authentication Rules

Protected endpoints should require:

```http
Authorization: Bearer <token>
```

Potentially protected endpoints:

```text
POST /voyages
POST /forecast
POST /compatibility
POST /cost
POST /risk
POST /recommend
POST /simulation
```

Public endpoints may include:

```text
GET /health
POST /auth/register
POST /auth/login
```

The exact authentication policy can be adjusted during development.

---

# 33. API Development Status

| Endpoint | Owner | Status |
|---|---|---|
| GET /health | Backend Core | Done |
| POST /auth/register | Backend Core | Done |
| POST /auth/login | Backend Core | Done |
| GET /users/me | Backend Core | Done |
| POST /voyages | Backend Intelligence | Planned |
| GET /ports | Backend Intelligence | Planned |
| GET /ports/{id} | Backend Intelligence | Planned |
| GET /vessels | Backend Intelligence | Planned |
| POST /compatibility | Backend Intelligence | Planned |
| POST /forecast | Backend + ML | Planned |
| POST /cost | Backend Intelligence | Planned |
| POST /risk | Backend Intelligence | Planned |
| POST /recommend | Backend Intelligence | Planned |
| POST /simulation | Backend Intelligence | Planned |

---

# 34. Contract Change Rules

This document is the shared contract between:

```text
Frontend
Backend
ML
Decision Engine
```

Before changing:

- Endpoint names
- Request field names
- Response field names
- Required fields
- Data types
- Recommendation strategy values

the affected team members should be informed.

Breaking API changes should be reviewed before implementation.

---

# 35. Current Development Principle

FreightWise should not return a recommendation merely because the interface expects one.

If required data is unavailable, the API should clearly communicate:

```text
UNAVAILABLE
INSUFFICIENT_DATA
LOW_CONFIDENCE
```

rather than fabricate a confident result.

The objective is to build a technically credible decision-support system, not a system that produces arbitrary numbers.

---

# 36. Primary Product Flow

The main FreightWise user journey is:

```text
User enters cargo requirement
             ↓
        Create Voyage
             ↓
     Forecast freight
             ↓
     Find feasible vessels
             ↓
     Evaluate candidate ports
             ↓
     Calculate operational risk
             ↓
     Calculate landed cost
             ↓
       Rank candidates
             ↓
    Recommend strategy
             ↓
      Explain WHY
             ↓
     Compare alternatives
             ↓
       What-if simulation
```

The core product question is:

> **When should we charter, which vessel should we use, which port should we choose, and why?**