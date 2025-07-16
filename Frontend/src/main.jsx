import { StrictMode } from 'react';
import { createRoot } from 'react-dom/client';
// import './index.css'
import App from './App.jsx';
import Dashboard from './Dashboard.jsx';
import ChatInterface from './Chat.jsx';

createRoot(document.getElementById('root')).render(
  <StrictMode>
    <App />
  </StrictMode>
);
