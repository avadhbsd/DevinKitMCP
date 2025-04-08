import React, { useState, KeyboardEvent, useEffect, useRef } from 'react';
import { Send } from 'lucide-react';

interface ChatInputProps {
  onSendMessage: (message: string) => void;
  disabled?: boolean;
  placeholder?: string;
}

const ChatInput: React.FC<ChatInputProps> = ({
  onSendMessage,
  disabled = false,
  placeholder = 'Type your message...'
}) => {
  const [message, setMessage] = useState('');
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  useEffect(() => {
    console.log('ChatInput state:', { message, disabled });
  }, [message, disabled]);

  const handleSendMessage = () => {
    if (message.trim() && !disabled) {
      console.log('Sending message:', message);
      onSendMessage(message);
      setMessage('');
    }
  };

  const handleKeyDown = (e: KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  };

  const handleChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    console.log('Input changed:', e.target.value);
    setMessage(e.target.value);
  };

  return (
    <div className="flex items-end border rounded-lg p-2 bg-white dark:bg-gray-800">
      <textarea
        ref={textareaRef}
        className="flex-1 resize-none border-0 bg-transparent p-2 focus:ring-0 focus:outline-none text-gray-800"
        placeholder={placeholder}
        rows={1}
        value={message}
        onChange={handleChange}
        onKeyDown={handleKeyDown}
        disabled={disabled}
      />
      <button
        className={`p-2 rounded-full ${
          message.trim() && !disabled
            ? 'bg-blue-500 text-white hover:bg-blue-600'
            : 'bg-gray-200 text-gray-500 cursor-not-allowed'
        }`}
        onClick={handleSendMessage}
        disabled={!message.trim() || disabled}
      >
        <Send size={20} />
      </button>
    </div>
  );
};

export default ChatInput;
