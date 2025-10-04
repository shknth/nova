import { useState, useEffect, useCallback } from 'react';
import { dataService } from '../services/dataService';

// Generic API hook for data fetching
export const useApi = (apiFunction, dependencies = [], options = {}) => {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const {
    immediate = true, // Whether to fetch immediately
    onSuccess = null, // Success callback
    onError = null    // Error callback
  } = options;

  const fetchData = useCallback(async (...args) => {
    try {
      setLoading(true);
      setError(null);
      
      const result = await apiFunction(...args);
      setData(result);
      
      if (onSuccess) {
        onSuccess(result);
      }
    } catch (err) {
      const errorMessage = err.message || 'An error occurred';
      setError(errorMessage);
      
      if (onError) {
        onError(err);
      }
      
      console.error('API Error:', err);
    } finally {
      setLoading(false);
    }
  }, [apiFunction, onSuccess, onError]);

  useEffect(() => {
    if (immediate) {
      fetchData();
    }
  }, dependencies);

  // Manual refetch function
  const refetch = useCallback((...args) => {
    return fetchData(...args);
  }, [fetchData]);

  return {
    data,
    loading,
    error,
    refetch
  };
};

// Specific hooks for different data types
export const useCurrentAirQuality = (location = null) => {
  return useApi(
    () => dataService.getCurrentAirQuality(location),
    [location]
  );
};

export const useAirQualityForecast = (location = null, days = 7) => {
  return useApi(
    () => dataService.getAirQualityForecast(location, days),
    [location, days]
  );
};

export const useQueryData = (query) => {
  return useApi(
    () => dataService.getQuerySpecificData(query),
    [query],
    { immediate: !!query } // Only fetch if query exists
  );
};

export const useRegionalData = (bounds = null) => {
  return useApi(
    () => dataService.getRegionalData(bounds),
    [bounds]
  );
};

export const useAdvancedData = () => {
  return useApi(() => dataService.getAdvancedData());
};

// Hook for submitting queries (doesn't auto-fetch)
export const useQuerySubmission = () => {
  const [response, setResponse] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const submitQuery = useCallback(async (query) => {
    try {
      setLoading(true);
      setError(null);
      
      const result = await dataService.submitQuery(query);
      setResponse(result.response);
      
      return result.response;
    } catch (err) {
      const errorMessage = err.message || 'Failed to process query';
      setError(errorMessage);
      throw err;
    } finally {
      setLoading(false);
    }
  }, []);

  return {
    response,
    loading,
    error,
    submitQuery,
    clearResponse: () => setResponse(null)
  };
};

export default useApi;
