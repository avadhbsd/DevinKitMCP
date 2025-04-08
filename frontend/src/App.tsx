import React from 'react';
import ChatContainer from './components/Chat/ChatContainer';
import './App.css';

function App() {
  return (
    <div className="min-h-screen bg-gray-100 dark:bg-gray-900 text-gray-900 dark:text-gray-100">
      <div className="container mx-auto h-screen p-4">
        <ChatContainer />
      </div>
    </div>
  );
}

export default App;
