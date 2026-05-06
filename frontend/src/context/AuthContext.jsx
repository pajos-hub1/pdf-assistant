import { createContext, useContext, useState } from 'react'

const AuthContext = createContext(null)

export const AuthProvider = ({ children }) => {
  const [apiKey, setApiKey] = useState(localStorage.getItem('api_key') || null)
  const [sessionId, setSessionId] = useState(localStorage.getItem('session_id') || null)
  const [owner, setOwner] = useState(localStorage.getItem('owner') || null)
  const [email, setEmail] = useState(localStorage.getItem('email') || null)
  const [isAuthenticated, setIsAuthenticated] = useState(!!localStorage.getItem('api_key'))

  const login = (key, session, ownerName, userEmail) => {
    localStorage.setItem('api_key', key)
    localStorage.setItem('owner', ownerName)
    if (session) localStorage.setItem('session_id', session)
    if (userEmail) localStorage.setItem('email', userEmail)
    setApiKey(key)
    setSessionId(session)
    setOwner(ownerName)
    setEmail(userEmail)
    setIsAuthenticated(true)
  }

  const updateSession = (session) => {
    localStorage.setItem('session_id', session)
    setSessionId(session)
  }

  const logout = () => {
    localStorage.removeItem('api_key')
    localStorage.removeItem('session_id')
    localStorage.removeItem('owner')
    localStorage.removeItem('email')
    setApiKey(null)
    setSessionId(null)
    setOwner(null)
    setEmail(null)
    setIsAuthenticated(false)
  }

  return (
    <AuthContext.Provider value={{
      apiKey, sessionId, owner, email,
      isAuthenticated, login, logout, updateSession
    }}>
      {children}
    </AuthContext.Provider>
  )
}

export const useAuth = () => useContext(AuthContext)