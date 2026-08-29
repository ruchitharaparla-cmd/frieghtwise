# FreightWise

AI-powered freight forecasting and vessel chartering
decision-support system for bulk cargo to India's East Coast.

> 🚧 Project under development — SIH 2026

## Overview

FreightWise aims to help bulk-cargo operators make better chartering
decisions by combining freight-rate forecasting with vessel, port,
route, and market information.

## Status

Currently in the research and development phase.

## Team

SIH 2026 Team

---

# Dataset Documentation

## 1. India Bulk Import Data — DGCIS

**Dataset:** India's Import by Principal Commodity Group

**Source:** Directorate General of Commercial Intelligence and Statistics (DGCIS), Government of India

**URL:** https://ftddp.dgciskol.gov.in/dgcis/principalcommditysearch.html

**Date range:** 2022–2026 (January–May for 2026)

**Frequency:** Yearly / period-wise

**Units:** Tonnes (TON), INR, US$

**Variables:** Year, Commodity, Country of Consignment, Port, Unit, Quantity, Value (INR), Value (US $)

**License:** Government of India data; refer to DGCIS terms of use

**Why we use it:** To measure India's bulk-cargo import demand by commodity, origin country, and Indian port. This supports bulk-cargo procurement and East Coast port analysis.

**Limitations:** 2026 contains only January–May data. The dataset contains selected bulk commodities rather than all commodities. Port-level congestion and vessel compatibility are not directly provided.

---

## 2. Freight Rates

**Dataset:** Shipping Rates Dataset

**Source:** kaggle

**URL:** 

**Date range:** 2000–2024

**Frequency:** Monthly

**Units:** BDI index, USD/day, percentage

**Variables:** Date, Baltic Dry Index, Handysize Bulk Carrier Rate, Aframax Tanker Rate, Supply Chain Pressure Index, On-Time Delivery Percentage, BDI MoM Change, Container YoY Change

**License:** [Original license]

**Why we use it:** To analyze historical freight-market behavior and support freight-rate forecasting.

**Limitations:** Data ends in December 2024. Some variables are not directly related to dry bulk shipping.

---

## 3. Commodity Prices

**Dataset:** Commodity Prices Supply Chain Dataset

**Source:** Kaggle

**URL:** [Original Kaggle URL]

**Date range:** 2010–2026

**Frequency:** Daily in raw data; monthly averages in processed data

**Units:** Dataset-specific commodity price units

**Variables:** Date, Commodity, Category, Unit, Currency, Average Price

**License:** [Kaggle license]

**Why we use it:** To capture commodity-market conditions that may influence cargo demand and freight rates.

**Limitations:** No iron-ore price series is available in this dataset. Commodity coverage is limited to the available price series.

---

## 4. Oil, Fuel & Geopolitics

**Dataset:** Oil Geopolitics Dataset 2010–2026

**Source:** [Original source]

**URL:** [Original URL]

**Date range:** 2010–2026

**Frequency:** Daily

**Units:** Oil prices, market indices, percentages, volatility measures

**Variables:** Brent Price, WTI Price, DXY Index, VIX, GPR Index, Returns, Lag Variables, Volatility, Brent-WTI Spread, Event Type, Event Severity, Event Flag

**License:** [Original license]

**Why we use it:** To capture fuel-price movements, market volatility, and geopolitical conditions that may influence freight costs.

**Limitations:** Global indicators rather than India-specific fuel prices or port-level geopolitical impacts.

---

## 5. Port Congestion

**Dataset:** Port Congestion Dataset

**Source:** [Original source]

**URL:** [Original URL]

**Date range:** 2019–2024

**Frequency:** Weekly

**Units:** TEU million, vessels, days, index, percentage, hours

**Variables:** Week Start, Year, Month, Port, Country, Region, Throughput, Vessels at Anchor, Average Waiting Days, Congestion Index, Port Utilization, Berth Delay

**License:** [Original license]

**Why we use it:** To analyze congestion, vessel waiting time, berth delays, and port utilization.

**Limitations:** The dataset does not contain Indian ports and therefore cannot represent actual congestion at Visakhapatnam or other Indian East Coast ports.

---

## 6. Vessel Performance

**Dataset:** Ship Performance Dataset

**Source:** Kaggle

**URL:** [Original Kaggle URL]

**Date range:** June 2023–June 2024

**Frequency:** Weekly

**Units:** Knots, kW, nautical miles, metres, tonnes, USD, hours, percentage

**Variables:** Date, Ship Type, Route Type, Engine Type, Maintenance Status, Speed Over Ground, Engine Power, Distance Traveled, Draft, Weather Condition, Cargo Weight, Operational Cost, Revenue per Voyage, Turnaround Time, Efficiency, Seasonal Impact Score, Weekly Voyage Count, Average Load Percentage

**License:** [Kaggle license]

**Why we use it:** To compare vessel performance and support prototype vessel-selection recommendations.

**Limitations:** No vessel IDs, DWT, LOA, beam, or complete real-world vessel specifications. Some categorical fields contain missing values.

---

## 7. Global Trade Flows

**Dataset:** Trade Flows Dataset

**Source:** [Original source]

**URL:** [Original URL]

**Date range:** 2000–2024

**Frequency:** Yearly

**Units:** Billion USD, percentage

**Variables:** Year, Exporter, Importer, Trade Category, Key Goods, Trade Value, YoY Growth, Effective Tariff Rate, Trade Active, Supply Chain Integrated, Concentration Risk

**License:** [Original license]

**Why we use it:** To provide global trade-demand context and identify trade growth and concentration risk.

**Limitations:** Not port-level data and has limited India-specific records compared with the DGCIS dataset.
