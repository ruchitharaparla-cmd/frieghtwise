# FreightWise Decision Engine

## 1. Objective

FreightWise evaluates multiple vessel, port and chartering options for a bulk-cargo voyage and recommends the most economical and reliable option.

The system should answer:

- When should the vessel be chartered?
- Which vessel is suitable?
- Which port/route is preferable?
- What is the expected total landed cost?
- What are the major risks?
- Why was this option recommended?

---

## 2. User Input

Example:

- Cargo type: Coal
- Quantity: 75,000 tonnes
- Origin: Australia
- Destination region: East Coast India
- Required arrival date: 2026-09-20
- Charter flexibility: [define later]

---

## 3. Decision Pipeline

User Input
↓
Freight Forecast
↓
Candidate Vessel Generation
↓
Vessel-Port Compatibility
↓
Port/Congestion Analysis
↓
Weather/Operational Risk
↓
Voyage Cost Calculation
↓
Candidate Ranking
↓
Final Recommendation

---

## 4. Freight Forecasting

Input:
- Historical freight rates
- Date
- Route
- Vessel class
- Relevant market indicators

Output:
- Forecast freight rate
- Forecast horizon
- Confidence/evaluation information

Model:
- Baseline: naive / moving average
- Candidate ML model: XGBoost

Evaluation:
- MAE
- RMSE
- MAPE

Do not report numerical model performance until experiments produce it.

---

## 5. Vessel-Port Compatibility

A vessel is feasible only if hard constraints are satisfied.

Check:

- LOA
- Beam
- Draft
- Cargo compatibility
- Vessel size/class
- Port-specific restrictions

Output:

FEASIBLE / NOT FEASIBLE

Rejected options must include a reason.

Example:

Vessel A → NOT FEASIBLE
Reason → Draft exceeds port limit

---

## 6. Port Evaluation

Evaluate candidate ports using:

- Vessel restrictions
- Cargo handling capability
- Historical throughput
- Waiting time
- Congestion
- Utilization
- Storage/handling capability
- Weather/operational conditions

Output:

Port score + reasons

---

## 7. Risk Engine

Potential risk factors:

- Port congestion
- Waiting time
- Weather
- Bunker/fuel uncertainty
- Demurrage exposure
- Route disruption

Each risk should be converted into an estimated impact where data allows.

Do not invent risk values when data is unavailable.

---

## 8. Total Landed Cost

For each candidate:

Total Cost =
Freight Cost
+ Bunker Cost
+ Port Charges
+ Expected Delay Cost
+ Expected Demurrage
+ Other Applicable Costs

The exact formulas and data sources will be documented separately.

---

## 9. Candidate Ranking

The system compares feasible candidates.

Possible factors:

- Total landed cost
- Expected delay
- Operational risk
- Freight forecast
- Port suitability

The ranking method must be documented and reproducible.

---

## 10. Recommendation

Possible strategies:

BOOK NOW
WAIT
ALTERNATIVE PORT
ALTERNATIVE VESSEL
MULTI-VOYAGE

Recommendation must include:

- Selected vessel
- Selected port
- Charter strategy
- Expected cost
- Risk
- Main reasons
- Important rejected alternatives

---

## 11. Explainability

Every recommendation should answer:

WHY this option?

WHY NOT the alternatives?

Example:

Recommended:
Vessel B + Port X

Reasons:
1. Compatible with port draft restriction
2. Lower expected landed cost
3. Lower congestion exposure
4. Arrival requirement satisfied

Rejected:
Vessel A

Reason:
Draft exceeds port restriction.