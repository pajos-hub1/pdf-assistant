import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import './index.css'
import App from './App.jsx'
import { AuthProvider } from './context/AuthContext.jsx'
import { ThemeProvider } from './context/ThemeContext.jsx'
import { ChatProvider } from './context/ChatContext.jsx'
import { ToastProvider } from './context/ToastContext.jsx'

createRoot(document.getElementById('root')).render(
  <StrictMode>
    <ThemeProvider>
      <AuthProvider>
        <ChatProvider>
          <ToastProvider>
            <App />
          </ToastProvider>
        </ChatProvider>
      </AuthProvider>
    </ThemeProvider>
  </StrictMode>
)