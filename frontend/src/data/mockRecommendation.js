const mockRecommendation = {
  voyage: {
    cargoType: "Coal",
    quantityTonnes: 75000,
    origin: "Hay Point, Australia",
    destination: "Paradip, India",
    startDate: "12 Sep 2026",
    endDate: "18 Sep 2026",
  },

  recommendation: {
    action: "CHARTER",
    vesselName: "MV Ocean Star",
    vesselDwt: 76000,
    vesselType: "Bulk Carrier",
    port: "Paradip",
    confidence: 87,
    summary:
      "Best balance of cost, risk and availability.",
  },

  cost: {
    total: 64200000,
    savings: 1840000,
    currency: "INR",
  },

  forecast: {
    currentRate: 18.2,
    predictedRate: 17.4,
    unit: "USD/MT",
    trend: "DOWN",
  },

  risk: {
    overall: 28,
    weather: 18,
    congestion: 31,
    vessel: 12,
  },

  delay: {
    expectedDays: 1.4,
  },

  congestion: {
    current: 42,
    predicted: 36,
    trend: "DOWN",
  },

  reasons: [
    "Freight rate expected to decrease moderately",
    "Vessel matches cargo requirement",
    "Paradip has acceptable draft and port infrastructure",
    "Lower congestion compared to alternative ports",
    "Low weather risk during the booking window",
    "Lower expected demurrage",
    "Better overall voyage cost and availability",
  ],

  alternatives: [
    {
      vesselName: "MV Eastern Star",
      port: "Gangavaram",
      estimatedCost: 65100000,
      risk: 32,
    },
    {
      vesselName: "MV Pacific Trader",
      port: "Visakhapatnam",
      estimatedCost: 65800000,
      risk: 35,
    },
  ],
};

export default mockRecommendation;
