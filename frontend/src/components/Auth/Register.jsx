import { useState } from 'react'
import { useAuth } from '../../context/AuthContext'
import { Eye, EyeOff, Check, X } from 'lucide-react'
import axios from 'axios'

const checkStrength = (password) => {
  return {
    length: password.length >= 8,
    uppercase: /[A-Z]/.test(password),
    lowercase: /[a-z]/.test(password),
    number: /[0-9]/.test(password),
    special: /[^A-Za-z0-9]/.test(password),
  }
}

const StrengthItem = ({ met, label }) => (
  <div className="flex items-center gap-1.5">
    {met
      ? <Check size={11} className="text-green-500 shrink-0" />
      : <X size={11} className="text-gray-300 dark:text-gray-600 shrink-0" />
    }
    <span className={`text-xs ${met
      ? 'text-green-600 dark:text-green-400'
      : 'text-gray-400 dark:text-gray-500'}`}>
      {label}
    </span>
  </div>
)

export default function Auth() {
  const [mode, setMode] = useState('login')
  const [name, setName] = useState('')
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [confirmPassword, setConfirmPassword] = useState('')
  const [showPassword, setShowPassword] = useState(false)
  const [showConfirm, setShowConfirm] = useState(false)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const { login } = useAuth()

  const strength = checkStrength(password)
  const isStrong = Object.values(strength).every(Boolean)
  const passwordsMatch = password === confirmPassword && confirmPassword !== ''

  const handleSubmit = async (e) => {
    e.preventDefault()
    setError('')

    if (mode === 'register') {
      if (!isStrong) {
        setError('Please meet all password requirements.')
        return
      }
      if (!passwordsMatch) {
        setError('Passwords do not match.')
        return
      }
    }

    setLoading(true)
    try {
      if (mode === 'register') {
        const { data } = await axios.post('/api/auth/register', {
          owner_name: name,
          email,
          password
        })
        // After register — no existing session yet
        login(data.api_key, null, data.owner, data.email)

      } else {
        // Login — get api_key first
        const { data } = await axios.post('/api/auth/login', {
          email,
          password
        })

        // Temporarily set api_key in localStorage so /auth/me can authenticate
        localStorage.setItem('api_key', data.api_key)

        // Fetch last active session
        const meRes = await axios.get('/api/auth/me', {
          headers: { 'X-API-Key': data.api_key }
        })

        // Login with restored session_id
        login(data.api_key, meRes.data.session_id, data.owner, data.email)
      }
    } catch (err) {
      setError(err.response?.data?.detail || 'Something went wrong.')
    } finally {
      setLoading(false)
    }
  }

  const inputClass = `w-full px-4 py-3 rounded-xl
    border border-gray-200 dark:border-gray-700
    bg-gray-50 dark:bg-gray-800
    text-gray-900 dark:text-white
    placeholder-gray-400 dark:placeholder-gray-500
    focus:outline-none focus:ring-2
    focus:ring-gray-900 dark:focus:ring-white
    text-sm transition-all`

  return (
    <div className="min-h-screen flex items-center justify-center
                    bg-gray-50 dark:bg-gray-950 py-8">
      <div className="w-full max-w-md px-8 py-10
                      bg-white dark:bg-gray-900
                      rounded-2xl shadow-lg
                      border border-gray-100 dark:border-gray-800">

        {/* Logo */}
        <div className="mb-8 text-center">
          <div className="inline-flex items-center justify-center
                          w-14 h-14 rounded-2xl
                          bg-gray-950 dark:bg-white mb-4">
            <span className="text-2xl">📄</span>
          </div>
          <h1 className="text-2xl font-bold text-gray-900 dark:text-white tracking-tight">
            PDF Assistant
          </h1>
          <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">
            Your AI-powered document companion
          </p>
        </div>

        {/* Mode tabs */}
        <div className="flex rounded-xl bg-gray-100 dark:bg-gray-800 p-1 mb-6">
          <button
            onClick={() => { setMode('login'); setError('') }}
            className={`flex-1 py-2 text-sm font-medium rounded-lg transition-all
              ${mode === 'login'
                ? 'bg-white dark:bg-gray-900 text-gray-900 dark:text-white shadow-sm'
                : 'text-gray-500 dark:text-gray-400'
              }`}
          >
            Login
          </button>
          <button
            onClick={() => { setMode('register'); setError('') }}
            className={`flex-1 py-2 text-sm font-medium rounded-lg transition-all
              ${mode === 'register'
                ? 'bg-white dark:bg-gray-900 text-gray-900 dark:text-white shadow-sm'
                : 'text-gray-500 dark:text-gray-400'
              }`}
          >
            Register
          </button>
        </div>

        {/* Form */}
        <form onSubmit={handleSubmit} className="space-y-4">

          {mode === 'register' && (
            <div>
              <label className="block text-sm font-medium
                                text-gray-700 dark:text-gray-300 mb-1">
                Full Name
              </label>
              <input
                type="text"
                value={name}
                onChange={(e) => setName(e.target.value)}
                placeholder="e.g. Ayonaire"
                required
                className={inputClass}
              />
            </div>
          )}

          <div>
            <label className="block text-sm font-medium
                              text-gray-700 dark:text-gray-300 mb-1">
              Email
            </label>
            <input
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="you@example.com"
              required
              className={inputClass}
            />
          </div>

          <div>
            <label className="block text-sm font-medium
                              text-gray-700 dark:text-gray-300 mb-1">
              Password
            </label>
            <div className="relative">
              <input
                type={showPassword ? 'text' : 'password'}
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="••••••••"
                required
                className={`${inputClass} pr-11`}
              />
              <button
                type="button"
                onClick={() => setShowPassword(!showPassword)}
                className="absolute right-3 top-1/2 -translate-y-1/2
                           text-gray-400 hover:text-gray-600
                           dark:text-gray-500 dark:hover:text-gray-300"
              >
                {showPassword ? <EyeOff size={16} /> : <Eye size={16} />}
              </button>
            </div>

            {mode === 'register' && password.length > 0 && (
              <div className="mt-3 p-3 rounded-xl bg-gray-50 dark:bg-gray-800
                              border border-gray-100 dark:border-gray-700">
                <p className="text-xs font-medium text-gray-500 dark:text-gray-400 mb-2">
                  Password requirements:
                </p>
                <div className="grid grid-cols-2 gap-1">
                  <StrengthItem met={strength.length} label="At least 8 characters" />
                  <StrengthItem met={strength.uppercase} label="Uppercase letter" />
                  <StrengthItem met={strength.lowercase} label="Lowercase letter" />
                  <StrengthItem met={strength.number} label="Number" />
                  <StrengthItem met={strength.special} label="Special character" />
                </div>
                <div className="mt-2 flex gap-1">
                  {[1, 2, 3, 4, 5].map((i) => {
                    const filled = Object.values(strength).filter(Boolean).length >= i
                    const color = filled
                      ? Object.values(strength).filter(Boolean).length <= 2
                        ? 'bg-red-400'
                        : Object.values(strength).filter(Boolean).length <= 4
                          ? 'bg-yellow-400'
                          : 'bg-green-500'
                      : 'bg-gray-200 dark:bg-gray-700'
                    return (
                      <div key={i}
                           className={`h-1 flex-1 rounded-full transition-all ${color}`} />
                    )
                  })}
                </div>
              </div>
            )}
          </div>

          {mode === 'register' && (
            <div>
              <label className="block text-sm font-medium
                                text-gray-700 dark:text-gray-300 mb-1">
                Confirm Password
              </label>
              <div className="relative">
                <input
                  type={showConfirm ? 'text' : 'password'}
                  value={confirmPassword}
                  onChange={(e) => setConfirmPassword(e.target.value)}
                  placeholder="••••••••"
                  required
                  className={`${inputClass} pr-11 ${
                    confirmPassword.length > 0
                      ? passwordsMatch
                        ? 'border-green-400 dark:border-green-600'
                        : 'border-red-400 dark:border-red-600'
                      : ''
                  }`}
                />
                <button
                  type="button"
                  onClick={() => setShowConfirm(!showConfirm)}
                  className="absolute right-3 top-1/2 -translate-y-1/2
                             text-gray-400 hover:text-gray-600
                             dark:text-gray-500 dark:hover:text-gray-300"
                >
                  {showConfirm ? <EyeOff size={16} /> : <Eye size={16} />}
                </button>
              </div>
              {confirmPassword.length > 0 && (
                <p className={`text-xs mt-1 ${
                  passwordsMatch
                    ? 'text-green-600 dark:text-green-400'
                    : 'text-red-500 dark:text-red-400'
                }`}>
                  {passwordsMatch ? '✓ Passwords match' : '✗ Passwords do not match'}
                </p>
              )}
            </div>
          )}

          {error && (
            <div className="px-4 py-3 rounded-xl
                            bg-red-50 dark:bg-red-950
                            border border-red-200 dark:border-red-800">
              <p className="text-sm text-red-600 dark:text-red-400">{error}</p>
            </div>
          )}

          <button
            type="submit"
            disabled={loading || (mode === 'register' && (!isStrong || !passwordsMatch))}
            className="w-full py-3 px-4
                       bg-gray-950 dark:bg-white
                       text-white dark:text-gray-950
                       rounded-xl font-semibold text-sm tracking-wide
                       hover:bg-gray-800 dark:hover:bg-gray-100
                       disabled:opacity-50 disabled:cursor-not-allowed
                       transition-all duration-200"
          >
            {loading
              ? (mode === 'login' ? 'Logging in...' : 'Creating account...')
              : (mode === 'login' ? 'Login →' : 'Create Account →')
            }
          </button>
        </form>

        <p className="text-xs text-center text-gray-400 dark:text-gray-600 mt-6">
          100% free · Runs locally · No data leaves your machine
        </p>
      </div>
    </div>
  )
}