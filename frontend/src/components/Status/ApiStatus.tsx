import React from 'react';
import { RefreshCw } from 'lucide-react';
import { ConnectionStatus } from '../../hooks/useApiStatus';

interface ApiStatusProps {
  name: string;
  status: ConnectionStatus;
  onRetry: () => void;
}

const ApiStatus: React.FC<ApiStatusProps> = ({ name, status, onRetry }) => {
  const getStatusColor = () => {
    switch (status) {
      case 'connected':
        return 'bg-green-500';
      case 'connecting':
        return 'bg-yellow-500';
      case 'error':
        return 'bg-red-500';
      default:
        return 'bg-gray-500';
    }
  };

  const getStatusText = () => {
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
    <div className="flex items-center space-x-2 bg-gray-700 rounded-md px-3 py-1">
      <div className={`w-2 h-2 rounded-full ${getStatusColor()}`} />
      <span className="text-sm text-gray-200">{name}: {getStatusText()}</span>
      {status === 'error' && (
        <button
          onClick={onRetry}
          className="p-1 rounded-full hover:bg-gray-600 transition-colors"
          aria-label="Retry connection"
        >
          <RefreshCw size={14} className="text-gray-300" />
        </button>
      )}
    </div>
  );
};

export default ApiStatus;
