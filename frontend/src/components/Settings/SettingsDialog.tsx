import React, { useState } from 'react';
import { X } from 'lucide-react';
import { ConnectionStatus } from '../../hooks/useApiStatus';

interface ApiSettings {
  kitApiKey: string;
  claudeApiKey: string;
}

interface ApiStatusProps {
  status: ConnectionStatus;
  retry: () => void;
}

interface SettingsDialogProps {
  isOpen: boolean;
  onClose: () => void;
  apiSettings: ApiSettings;
  onSave: (settings: ApiSettings) => void;
  kitApiStatus: ApiStatusProps;
  claudeApiStatus: ApiStatusProps;
}

const SettingsDialog: React.FC<SettingsDialogProps> = ({
  isOpen,
  onClose,
  apiSettings,
  onSave,
  kitApiStatus,
  claudeApiStatus
}) => {
  const [localSettings, setLocalSettings] = useState<ApiSettings>(apiSettings);

  if (!isOpen) return null;

  const handleSave = () => {
    onSave(localSettings);
    onClose();
  };

  const getStatusColor = (status: ConnectionStatus) => {
    switch (status) {
      case 'connected':
        return 'text-green-500';
      case 'connecting':
        return 'text-yellow-500';
      case 'error':
        return 'text-red-500';
      default:
        return 'text-gray-500';
    }
  };

  const getStatusText = (status: ConnectionStatus) => {
    switch (status) {
      case 'connected':
        return 'Connected';
      case 'connecting':
        return 'Connecting...';
      case 'error':
        return 'Connection Error';
      default:
        return 'Not Connected';
    }
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow-lg w-full max-w-md">
        <div className="flex justify-between items-center p-4 border-b dark:border-gray-700">
          <h2 className="text-xl font-bold">API Settings</h2>
          <button
            onClick={onClose}
            className="p-1 rounded-full hover:bg-gray-200 dark:hover:bg-gray-700"
            aria-label="Close"
          >
            <X size={20} />
          </button>
        </div>
        
        <div className="p-4 space-y-4">
          <div className="space-y-2">
            <label htmlFor="kitApiKey" className="block text-sm font-medium">
              Kit.com API Key
            </label>
            <div className="flex space-x-2">
              <input
                id="kitApiKey"
                type="password"
                value={localSettings.kitApiKey}
                onChange={(e) => setLocalSettings({ ...localSettings, kitApiKey: e.target.value })}
                className="flex-1 border rounded-md p-2 dark:bg-gray-700 dark:border-gray-600"
                placeholder="Enter your Kit.com API key"
              />
              <div className="flex items-center">
                <span className={`text-sm ${getStatusColor(kitApiStatus.status)}`}>
                  {getStatusText(kitApiStatus.status)}
                </span>
                {kitApiStatus.status === 'error' && (
                  <button
                    onClick={kitApiStatus.retry}
                    className="ml-2 text-xs text-blue-500 hover:underline"
                  >
                    Retry
                  </button>
                )}
              </div>
            </div>
            <p className="text-xs text-gray-500 dark:text-gray-400">
              You can find your Kit.com API key in your account settings.
            </p>
          </div>
          
          <div className="space-y-2">
            <label htmlFor="claudeApiKey" className="block text-sm font-medium">
              Claude API Key
            </label>
            <div className="flex space-x-2">
              <input
                id="claudeApiKey"
                type="password"
                value={localSettings.claudeApiKey}
                onChange={(e) => setLocalSettings({ ...localSettings, claudeApiKey: e.target.value })}
                className="flex-1 border rounded-md p-2 dark:bg-gray-700 dark:border-gray-600"
                placeholder="Enter your Claude API key"
              />
              <div className="flex items-center">
                <span className={`text-sm ${getStatusColor(claudeApiStatus.status)}`}>
                  {getStatusText(claudeApiStatus.status)}
                </span>
                {claudeApiStatus.status === 'error' && (
                  <button
                    onClick={claudeApiStatus.retry}
                    className="ml-2 text-xs text-blue-500 hover:underline"
                  >
                    Retry
                  </button>
                )}
              </div>
            </div>
            <p className="text-xs text-gray-500 dark:text-gray-400">
              You can get a Claude API key from Anthropic's website.
            </p>
          </div>
        </div>
        
        <div className="flex justify-end p-4 border-t dark:border-gray-700">
          <button
            onClick={handleSave}
            className="px-4 py-2 bg-blue-500 text-white rounded-md hover:bg-blue-600"
          >
            Save
          </button>
        </div>
      </div>
    </div>
  );
};

export default SettingsDialog;
