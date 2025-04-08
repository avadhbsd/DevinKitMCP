import React, { useState, useEffect, useRef } from 'react';
import { Settings } from 'lucide-react';
import ChatMessage from './ChatMessage';
import ChatInput from './ChatInput';
import SettingsDialog from '../Settings/SettingsDialog';
import { useApiSettings } from '../../hooks/useApiSettings';
import { useApiStatus } from '../../hooks/useApiStatus';

interface Message {
  content: string;
  role: 'user' | 'assistant';
  timestamp?: string;
}

const ChatContainer: React.FC = () => {
  const [messages, setMessages] = useState<Message[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [conversationId, setConversationId] = useState<string | null>(null);
  const [isSettingsOpen, setIsSettingsOpen] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const ws = useRef<WebSocket | null>(null);
  const { apiSettings, saveApiSettings } = useApiSettings();
  
  const kitApiStatus = useApiStatus({
    apiUrl: import.meta.env.VITE_API_URL || 'http://localhost:8000',
    endpoint: '/api/status/kit',
    apiKey: apiSettings.kitApiKey,
    enabled: !!apiSettings.kitApiKey,
  });
  
  const claudeApiStatus = useApiStatus({
    apiUrl: import.meta.env.VITE_API_URL || 'http://localhost:8000',
    endpoint: '/api/status/claude',
    apiKey: apiSettings.claudeApiKey,
    enabled: !!apiSettings.claudeApiKey,
  });

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  useEffect(() => {
    if (!apiSettings.kitApiKey || !apiSettings.claudeApiKey) {
      setIsSettingsOpen(true);
    }
  }, [apiSettings]);
  
  useEffect(() => {
    if (apiSettings.kitApiKey && apiSettings.claudeApiKey) {
      if (kitApiStatus.status === 'connected' && claudeApiStatus.status === 'connected') {
        if (messages.length === 0) {
          setMessages([{
            content: "Connected successfully with API keys. You can now interact with Kit.com using natural language.",
            role: 'assistant',
            timestamp: new Date().toISOString()
          }]);
        }
      } else if ((kitApiStatus.status === 'error' || claudeApiStatus.status === 'error') && messages.length === 0) {
        let errorMessage = "There was an error connecting to the APIs. Please check your API keys in settings.";
        
        if (kitApiStatus.status === 'error' && claudeApiStatus.status === 'error') {
          errorMessage = "Failed to connect to both Kit.com and Claude APIs. Please check your API keys in settings.";
        } else if (kitApiStatus.status === 'error') {
          errorMessage = `Failed to connect to Kit.com API: ${kitApiStatus.error || 'Unknown error'}`;
        } else if (claudeApiStatus.status === 'error') {
          errorMessage = `Failed to connect to Claude API: ${claudeApiStatus.error || 'Unknown error'}`;
        }
        
        setMessages([{
          content: errorMessage,
          role: 'assistant',
          timestamp: new Date().toISOString()
        }]);
      } else if ((kitApiStatus.status === 'connecting' || claudeApiStatus.status === 'connecting') && messages.length === 0) {
        setMessages([{
          content: "Connecting to APIs, please wait...",
          role: 'assistant',
          timestamp: new Date().toISOString()
        }]);
      }
    }
  }, [apiSettings, kitApiStatus.status, kitApiStatus.error, claudeApiStatus.status, claudeApiStatus.error, messages.length]);

  useEffect(() => {
    const connectWebSocket = () => {
      if (ws.current?.readyState === WebSocket.OPEN) return;
      
      const wsUrl = `${import.meta.env.VITE_API_URL?.replace('http', 'ws') || 'ws://localhost:8000'}/ws`;
      ws.current = new WebSocket(wsUrl);
      
      ws.current.onopen = () => {
        console.log('WebSocket connected');
      };
      
      ws.current.onmessage = (event) => {
        const data = JSON.parse(event.data);
        
        if (data.error) {
          console.error('WebSocket error:', data.error);
          return;
        }
        
        if (data.response) {
          setMessages(prev => [
            ...prev,
            {
              content: data.response,
              role: 'assistant',
              timestamp: data.timestamp
            }
          ]);
          
          if (data.conversation_id) {
            setConversationId(data.conversation_id);
          }
          
          setIsLoading(false);
        }
      };
      
      ws.current.onclose = () => {
        console.log('WebSocket disconnected');
        setTimeout(connectWebSocket, 3000);
      };
      
      ws.current.onerror = (error) => {
        console.error('WebSocket error:', error);
        ws.current?.close();
      };
    };
    
    if (apiSettings.kitApiKey && apiSettings.claudeApiKey) {
      connectWebSocket();
    }
    
    return () => {
      ws.current?.close();
    };
  }, [apiSettings]);

  const handleSendMessage = (message: string) => {
    if (!message.trim()) return;
    
    const newMessage: Message = {
      content: message,
      role: 'user',
      timestamp: new Date().toISOString()
    };
    
    setMessages(prev => [...prev, newMessage]);
    setIsLoading(true);
    
    if (ws.current?.readyState === WebSocket.OPEN) {
      ws.current.send(JSON.stringify({
        message,
        conversation_id: conversationId,
        kit_api_key: apiSettings.kitApiKey,
        claude_api_key: apiSettings.claudeApiKey
      }));
    } else {
      fetch(`${import.meta.env.VITE_API_URL || 'http://localhost:8000'}/api/chat`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-Kit-API-Key': apiSettings.kitApiKey,
          'X-Claude-API-Key': apiSettings.claudeApiKey
        },
        body: JSON.stringify({
          message,
          conversation_id: conversationId
        })
      })
      .then(response => response.json())
      .then(data => {
        setMessages(prev => [
          ...prev,
          {
            content: data.response,
            role: 'assistant',
            timestamp: new Date().toISOString()
          }
        ]);
        
        if (data.conversation_id) {
          setConversationId(data.conversation_id);
        }
        
        setIsLoading(false);
      })
      .catch(error => {
        console.error('Error sending message:', error);
        setIsLoading(false);
        
        setMessages(prev => [
          ...prev,
          {
            content: `Error: ${error.message}`,
            role: 'assistant',
            timestamp: new Date().toISOString()
          }
        ]);
      });
    }
  };

  return (
    <div className="flex flex-col h-full">
      <header className="flex justify-between items-center p-4 border-b dark:border-gray-700">
        <div>
          <h1 className="text-xl font-bold">Kit.com MCP Chat</h1>
          <p className="text-sm text-gray-500 dark:text-gray-400">Interact with Kit.com using natural language</p>
        </div>
        <div className="flex items-center space-x-4">
          <div className="flex items-center space-x-2">
            <div className={`w-2 h-2 rounded-full ${
              claudeApiStatus.status === 'connected' ? 'bg-green-500' : 
              claudeApiStatus.status === 'connecting' ? 'bg-yellow-500' : 'bg-red-500'
            }`}></div>
            <span className="text-sm">Claude API: {
              claudeApiStatus.status === 'connected' ? 'Connected' : 
              claudeApiStatus.status === 'connecting' ? 'Connecting...' : 
              claudeApiStatus.status === 'error' ? 'Error' : 'Disconnected'
            }</span>
          </div>
          <div className="flex items-center space-x-2">
            <div className={`w-2 h-2 rounded-full ${
              kitApiStatus.status === 'connected' ? 'bg-green-500' : 
              kitApiStatus.status === 'connecting' ? 'bg-yellow-500' : 'bg-red-500'
            }`}></div>
            <span className="text-sm">Kit.com API: {
              kitApiStatus.status === 'connected' ? 'Connected' : 
              kitApiStatus.status === 'connecting' ? 'Connecting...' : 
              kitApiStatus.status === 'error' ? 'Error' : 'Disconnected'
            }</span>
          </div>
          <button
            onClick={() => setIsSettingsOpen(true)}
            className="p-2 rounded-full hover:bg-gray-200 dark:hover:bg-gray-700"
            aria-label="Settings"
          >
            <Settings size={20} />
          </button>
        </div>
      </header>
      
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {messages.length === 0 ? (
          <div className="flex items-center justify-center h-full">
            <div className="text-center text-gray-500 dark:text-gray-400">
              <p className="mb-2">Send a message to get started</p>
              <p className="text-sm">Try asking about your Kit.com account, subscribers, or tags</p>
            </div>
          </div>
        ) : (
          messages.map((message, index) => (
            <ChatMessage key={index} message={message} />
          ))
        )}
        {isLoading && (
          <div className="flex justify-start mb-4">
            <div className="bg-gray-200 dark:bg-gray-700 rounded-lg p-4 rounded-bl-none max-w-[80%]">
              <div className="flex space-x-2">
                <div className="w-2 h-2 bg-gray-500 rounded-full animate-bounce"></div>
                <div className="w-2 h-2 bg-gray-500 rounded-full animate-bounce" style={{ animationDelay: '0.2s' }}></div>
                <div className="w-2 h-2 bg-gray-500 rounded-full animate-bounce" style={{ animationDelay: '0.4s' }}></div>
              </div>
            </div>
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>
      
      <div className="p-4 border-t dark:border-gray-700">
        <ChatInput
          onSendMessage={handleSendMessage}
          disabled={isLoading || !apiSettings.kitApiKey || !apiSettings.claudeApiKey}
          placeholder={!apiSettings.kitApiKey || !apiSettings.claudeApiKey ? "Please configure API keys in settings" : "Type your message..."}
        />
      </div>
      
      <SettingsDialog
        isOpen={isSettingsOpen}
        onClose={() => setIsSettingsOpen(false)}
        apiSettings={apiSettings}
        onSave={saveApiSettings}
        kitApiStatus={kitApiStatus}
        claudeApiStatus={claudeApiStatus}
      />
      
      <footer className="text-center p-2 text-xs text-gray-500 dark:text-gray-400">
        Powered by Model Context Protocol (MCP) and Kit.com V4 API
      </footer>
    </div>
  );
};

export default ChatContainer;
