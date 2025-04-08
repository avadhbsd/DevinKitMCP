import { useState, useEffect, useCallback } from 'react';

export type ConnectionStatus = 'idle' | 'connecting' | 'connected' | 'error';

interface UseApiStatusProps {
  apiUrl: string;
  endpoint: string;
  apiKey: string;
  enabled?: boolean;
}

interface ApiStatusResult {
  status: ConnectionStatus;
  error: string | null;
  retry: () => void;
  data: any;
}

export const useApiStatus = ({
  apiUrl,
  endpoint,
  apiKey,
  enabled = true
}: UseApiStatusProps): ApiStatusResult => {
  const [status, setStatus] = useState<ConnectionStatus>('idle');
  const [error, setError] = useState<string | null>(null);
  const [data, setData] = useState<any>(null);

  const checkApiStatus = useCallback(async () => {
    if (!apiKey || !enabled) {
      setStatus('idle');
      setError(null);
      return;
    }

    setStatus('connecting');
    setError(null);

    try {
      const headers: Record<string, string> = {
        'Content-Type': 'application/json'
      };

      if (endpoint.includes('/kit')) {
        headers['X-Kit-API-Key'] = apiKey;
      } else if (endpoint.includes('/claude')) {
        headers['X-Claude-API-Key'] = apiKey;
      }

      const response = await fetch(`${apiUrl}${endpoint}`, {
        method: 'GET',
        headers
      });

      if (!response.ok) {
        const errorText = await response.text();
        throw new Error(`API error (${response.status}): ${errorText}`);
      }

      const result = await response.json();
      setData(result);
      setStatus('connected');
    } catch (err) {
      console.error('API status check failed:', err);
      setStatus('error');
      setError(err instanceof Error ? err.message : String(err));
    }
  }, [apiUrl, endpoint, apiKey, enabled]);

  useEffect(() => {
    if (enabled) {
      checkApiStatus();
    } else {
      setStatus('idle');
      setError(null);
    }
  }, [apiKey, enabled, checkApiStatus]);

  const retry = useCallback(() => {
    checkApiStatus();
  }, [checkApiStatus]);

  return {
    status,
    error,
    retry,
    data
  };
};
