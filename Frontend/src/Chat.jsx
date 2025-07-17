import React, { useState } from 'react';
import { FiSend } from 'react-icons/fi';
import { useParams, useLocation } from 'react-router-dom';
import './App.css';

const ChatInterface = () => {
  const { docId } = useParams();
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);

  const location = useLocation();
  const filename = location.state?.filename || 'demo.pdf';

  const handleSend = async () => {
    if (!input.trim()) return;

    const newMessage = { sender: 'user', text: input };
    setMessages([...messages, newMessage]);
    setInput('');
    setLoading(true);

    const typingMessage = { sender: 'ai', text: 'AI is typing...' };
    setMessages((prev) => [...prev, typingMessage]);

    try {
      const response = await fetch('http://127.0.0.1:8000/ask', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ question: input }),
      });

      if (!response.ok) throw new Error('Failed to get response from server');
      const data = await response.json();
      console.log('Backend response:', data);
      const aiMessage = {
        sender: 'AI',
        text: data.answer || 'No response received',
      };
      setMessages((prev) => [...prev.slice(0, -1), aiMessage]);
    } catch (error) {
      console.error('Error during /ask:', error);
      setMessages((prev) => [
        ...prev.slice(0, -1),
        { sender: 'AI', text: 'Error: ' + error.message },
      ]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="chat-page">
      {/* Header */}
      <div className="chat-header">
        <h1 className="chat-title">Chat</h1>
        <div className="chat-filename">{filename}</div>
      </div>

      {/* Chat area */}
      <div className="chat-body">
        {messages.map((msg, index) => (
          <div
            key={index}
            className={`chat-message ${msg.sender === 'user' ? 'user' : 'ai'}`}
          >
            <p>{msg.text}</p>
          </div>
        ))}
      </div>

      {/* Input bar */}
      <div className="chat-input">
        <input
          type="text"
          placeholder="Send a message..."
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => e.key === 'Enter' && handleSend()}
        />
        <button onClick={handleSend}>
          <FiSend size={20} />
        </button>
      </div>
    </div>
  );
};

export default ChatInterface;
