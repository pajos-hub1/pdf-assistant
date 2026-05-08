import { createContext, useContext, useState, useEffect, useRef } from 'react'
import axios from 'axios'

const AuthContext = createContext(null)

export const AuthProvider = ({ children }) => {
  const [accessToken, setAccessToken] = useState(
    localStorage.getItem('access_token') || null
  )
  const [refreshToken, setRefreshToken] = useState(
    localStorage.getItem('refresh_token') || null
  )
  const [sessionId, setSessionId] = useState(
    localStorage.getItem('session_id') || null
  )
  const [owner, setOwner] = useState(localStorage.getItem('owner') || null)
  const [email, setEmail] = useState(localStorage.getItem('email') || null)
  const [isAuthenticated, setIsAuthenticated] = useState(
    !!localStorage.getItem('access_token')
  )

  const refreshTimerRef = useRef(null)

  // Only schedule refresh if BOTH tokens exist
  useEffect(() => {
    if (accessToken && refreshToken) {
      scheduleRefresh()
    }
    return () => {
      if (refreshTimerRef.current) {
        clearTimeout(refreshTimerRef.current)
      }
    }
  }, [accessToken, refreshToken])

  const scheduleRefresh = () => {
    if (!refreshToken) return  // guard — don't schedule if no refresh token

    const refreshIn = 14 * 60 * 1000  // 14 minutes

    if (refreshTimerRef.current) {
      clearTimeout(refreshTimerRef.current)
    }

    refreshTimerRef.current = setTimeout(async () => {
      await refreshAccessToken()
    }, refreshIn)
  }

  const refreshAccessToken = async () => {
    const storedRefresh = localStorage.getItem('refresh_token')
    if (!storedRefresh) {
      // No refresh token — don't logout, just do nothing
      return
    }

    try {
      const { data } = await axios.post('/api/auth/refresh', {
        refresh_token: storedRefresh
      })

      localStorage.setItem('access_token', data.access_token)
      localStorage.setItem('refresh_token', data.refresh_token)
      setAccessToken(data.access_token)
      setRefreshToken(data.refresh_token)
      scheduleRefresh()
      console.log('✅ Token refreshed automatically')
    } catch (err) {
      console.error('Token refresh failed — logging out')
      logout()
    }
  }

  const login = (tokens, session, ownerName, userEmail) => {
    localStorage.setItem('access_token', tokens.access_token)
    localStorage.setItem('refresh_token', tokens.refresh_token)
    localStorage.setItem('owner', ownerName)
    localStorage.setItem('email', userEmail)
    if (session) localStorage.setItem('session_id', session)

    setAccessToken(tokens.access_token)
    setRefreshToken(tokens.refresh_token)
    setOwner(ownerName)
    setEmail(userEmail)
    setSessionId(session)
    setIsAuthenticated(true)
  }

  const updateSession = (session) => {
    localStorage.setItem('session_id', session)
    setSessionId(session)
  }

  const logout = () => {
    localStorage.removeItem('access_token')
    localStorage.removeItem('refresh_token')
    localStorage.removeItem('session_id')
    localStorage.removeItem('owner')
    localStorage.removeItem('email')

    if (refreshTimerRef.current) {
      clearTimeout(refreshTimerRef.current)
    }

    setAccessToken(null)
    setRefreshToken(null)
    setOwner(null)
    setEmail(null)
    setSessionId(null)
    setIsAuthenticated(false)
  }

  return (
    <AuthContext.Provider value={{
      accessToken,
      sessionId,
      owner,
      email,
      isAuthenticated,
      login,
      logout,
      updateSession,
      refreshAccessToken
    }}>
      {children}
    </AuthContext.Provider>
  )
}

export const useAuth = () => useContext(AuthContext)