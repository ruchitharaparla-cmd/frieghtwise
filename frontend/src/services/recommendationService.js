import { API_BASE_URL } from "./api";
import mockRecommendation from "../data/mockRecommendation";

const USE_MOCK_DATA =
  import.meta.env.VITE_USE_MOCK_DATA !== "false";

export async function getRecommendation(voyageInput) {
  // -----------------------------------------
  // DEVELOPMENT MODE
  // -----------------------------------------
  if (USE_MOCK_DATA) {
    return {
      success: true,
      data: mockRecommendation,
      source: "mock",
    };
  }

  // -----------------------------------------
  // BACKEND MODE
  // -----------------------------------------
  const response = await fetch(
    `${API_BASE_URL}/recommend`,
    {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(voyageInput),
    }
  );

  if (!response.ok) {
    const message = await response.text();

    throw new Error(
      message || `Recommendation request failed: ${response.status}`
    );
  }

  const data = await response.json();

  return {
    success: true,
    data,
    source: "backend",
  };
}
