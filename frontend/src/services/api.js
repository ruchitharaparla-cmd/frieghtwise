export const API_BASE_URL =
  import.meta.env.VITE_API_URL || "http://localhost:8000";

async function request(endpoint, options = {}) {
  const response = await fetch(`${API_BASE_URL}${endpoint}`, {
    headers: {
      "Content-Type": "application/json",
      ...(options.headers || {}),
    },
    ...options,
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({}));

    throw new Error(
      error.detail || `Request failed: ${response.status}`
    );
  }

  return response.json();
}

export async function getPorts() {
  return request("/ports");
}

export async function getVessels() {
  return request("/vessels");
}

export async function getForecast(data) {
  return request("/forecast", {
    method: "POST",
    body: JSON.stringify(data),
  });
}

export async function getRecommendation(data) {
  return request("/recommend", {
    method: "POST",
    body: JSON.stringify(data),
  });
}

export async function createVoyage(data) {
  return request("/voyages", {
    method: "POST",
    body: JSON.stringify(data),
  });
}
