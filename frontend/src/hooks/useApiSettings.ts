import { useState, useEffect } from 'react';

interface ApiSettings {
  kitApiKey: string;
  claudeApiKey: string;
}

const LOCAL_STORAGE_KEY = 'mcp_api_settings';

export const useApiSettings = () => {
  const [apiSettings, setApiSettings] = useState<ApiSettings>({
    kitApiKey: '',
    claudeApiKey: ''
  });

  useEffect(() => {
    const savedSettings = localStorage.getItem(LOCAL_STORAGE_KEY);
    if (savedSettings) {
      try {
        const parsedSettings = JSON.parse(savedSettings);
        setApiSettings(parsedSettings);
      } catch (error) {
        console.error('Error parsing saved API settings:', error);
        localStorage.removeItem(LOCAL_STORAGE_KEY);
      }
    }
  }, []);

  const saveApiSettings = (settings: ApiSettings) => {
    setApiSettings(settings);
    localStorage.setItem(LOCAL_STORAGE_KEY, JSON.stringify(settings));
  };

  const clearApiSettings = () => {
    setApiSettings({
      kitApiKey: '',
      claudeApiKey: ''
    });
    localStorage.removeItem(LOCAL_STORAGE_KEY);
  };

  return {
    apiSettings,
    saveApiSettings,
    clearApiSettings
  };
};
