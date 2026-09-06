import { useCallback, useEffect, useState } from "react";
import { getRecommendation } from "../services/recommendationService";

export default function useRecommendation(voyageInput = null) {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const fetchRecommendation = useCallback(
    async (input = voyageInput) => {
      if (!input) return;

      setLoading(true);
      setError(null);

      try {
        const result = await getRecommendation(input);
        setData(result.data);
      } catch (err) {
        console.error("Recommendation error:", err);
        setError(err.message || "Unable to load recommendation");
      } finally {
        setLoading(false);
      }
    },
    [voyageInput]
  );

  useEffect(() => {
    if (voyageInput) {
      fetchRecommendation(voyageInput);
    }
  }, [voyageInput, fetchRecommendation]);

  return {
    data,
    loading,
    error,
    refetch: fetchRecommendation,
  };
}
