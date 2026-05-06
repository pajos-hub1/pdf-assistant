import { useAuth } from '../../context/AuthContext'
import { useTheme } from '../../context/ThemeContext'
import { Sun, Moon, LogOut } from 'lucide-react'

export default function Header() {
  const { owner, email, logout } = useAuth()
  const { isDark, toggleTheme } = useTheme()

  return (
    <header className="h-14 border-b border-gray-200 dark:border-gray-800
                        bg-white dark:bg-gray-950 flex items-center
                        justify-between px-6 shrink-0">
      {/* Logo */}
      <div className="flex items-center gap-2">
        <div className="w-7 h-7 rounded-lg bg-gray-950 dark:bg-white
                        flex items-center justify-center text-sm">
          <span>📄</span>
        </div>
        <span className="font-bold text-gray-900 dark:text-white
                         tracking-tight text-sm">
          PDF Assistant
        </span>
      </div>

      {/* Right side */}
      <div className="flex items-center gap-3">

        {/* User info */}
        {owner && (
          <div className="flex flex-col items-end">
            <span className="text-xs font-medium text-gray-700 dark:text-gray-300">
              {owner}
            </span>
            {email && (
              <span className="text-xs text-gray-400 dark:text-gray-500">
                {email}
              </span>
            )}
          </div>
        )}

        {/* Avatar */}
        {owner && (
          <div className="w-8 h-8 rounded-full bg-gray-950 dark:bg-white
                          flex items-center justify-center shrink-0">
            <span className="text-xs font-bold text-white dark:text-gray-950">
              {owner.charAt(0).toUpperCase()}
            </span>
          </div>
        )}

        {/* Theme toggle */}
        <button
          onClick={toggleTheme}
          className="w-8 h-8 rounded-lg flex items-center justify-center
                     text-gray-500 dark:text-gray-400
                     hover:bg-gray-100 dark:hover:bg-gray-800
                     transition-all duration-200"
          title={isDark ? 'Switch to light mode' : 'Switch to dark mode'}
        >
          {isDark ? <Sun size={16} /> : <Moon size={16} />}
        </button>

        {/* Logout */}
        <button
          onClick={logout}
          className="w-8 h-8 rounded-lg flex items-center justify-center
                     text-gray-500 dark:text-gray-400
                     hover:bg-red-50 dark:hover:bg-red-950
                     hover:text-red-500 dark:hover:text-red-400
                     transition-all duration-200"
          title="Logout"
        >
          <LogOut size={16} />
        </button>
      </div>
    </header>
  )
}