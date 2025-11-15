import React, { useEffect, useState } from 'react'
import { useNavigate, Link } from 'react-router-dom'
import api, { setAuthToken } from '../api/client'
import { toast } from 'sonner'
import { LogIn, Beaker } from 'lucide-react'

export default function SignIn() {
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [loading, setLoading] = useState(false)
  const navigate = useNavigate()

  useEffect(() => {
    const token = (()=>{ try { return localStorage.getItem('auth_token') } catch { return null } })()
    const sessionAuthed = (()=>{ try { return sessionStorage.getItem('session_authed') } catch { return null } })()
    if (token && sessionAuthed) navigate('/')
  }, [navigate])

  const submit = async (e) => {
    e.preventDefault()
    if (!username || !password) {
      toast.error('Enter username and password')
      return
    }
    setLoading(true)
    try {
      const { data } = await api.post('/auth/token/', { username, password })
      if (data?.token) {
        setAuthToken(data.token)
        try { sessionStorage.setItem('session_authed', '1') } catch {}
        toast.success('Signed in')
        navigate('/')
      } else {
        toast.error('Invalid response from server')
      }
    } catch (err) {
      const msg = err?.response?.data?.detail || 'Sign in failed'
      toast.error(msg)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen relative overflow-hidden">
      {/* Background */}
      <div
        className="absolute inset-0 bg-cover bg-center"
        style={{
          backgroundImage:
            "url('https://img.freepik.com/free-vector/abstract-technology-particle-background_23-2148408853.jpg?semt=ais_incoming&w=740&q=80')",
        }}
      ></div>

      {/* Overlay for contrast */}
      <div className="absolute inset-0 bg-black/30 backdrop-blur-sm"></div>

      {/* Header */}
      <div className="relative z-10 max-w-6xl mx-auto px-4 py-12">
        <div className="flex items-center gap-3">
          <Beaker className="w-10 h-10 text-cyan-300 drop-shadow-lg" />
          <h1 className="text-3xl font-bold bg-gradient-to-r from-blue-300 to-cyan-200 bg-clip-text text-transparent drop-shadow">
            Chemical Equipment Parameter Visualizer
          </h1>
        </div>
        <p className="text-sm text-white italic font-[cursive] drop-shadow-sm mt-1">
          Sign in to upload, analyze, and visualize your datasets
        </p>
      </div>

      {/* Sign In Card */}
      <div className="relative z-10 grid place-items-center px-4">
        <form
          onSubmit={submit}
          className="w-full max-w-sm bg-white/10 backdrop-blur-md border border-white/20 p-6 rounded-2xl shadow-[0_0_20px_rgba(59,130,246,0.3)] space-y-4 transition-all hover:shadow-[0_0_25px_rgba(59,130,246,0.5)]"
        >
          <div className="flex items-center gap-2">
            <div className="h-9 w-9 rounded-lg bg-blue-600/90 text-white grid place-items-center shadow">
              <LogIn size={18} />
            </div>
            <div>
              <h2 className="text-lg font-semibold leading-tight text-white">
                Sign in
              </h2>
              <p className="text-xs text-gray-300">
                Use your account to continue
              </p>
            </div>
          </div>

          {/* Username & Password */}
          <div className="space-y-3">
            <div>
              <label className="text-sm text-gray-300">Username</label>
              <input
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                className="mt-1 w-full border border-gray-400/40 rounded px-3 py-2 text-sm text-gray-800 focus:outline-none focus:ring focus:ring-blue-200"
              />
            </div>
            <div>
              <label className="text-sm text-gray-300">Password</label>
              <input
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className="mt-1 w-full border border-gray-400/40 rounded px-3 py-2 text-sm text-gray-800 focus:outline-none focus:ring focus:ring-blue-200"
              />
            </div>
          </div>

          {/* Button */}
          <button
            disabled={loading}
            className="w-full bg-blue-600 hover:bg-blue-700 transition-colors text-white py-2 rounded-lg disabled:opacity-50"
          >
            {loading ? 'Signing in…' : 'Sign in'}
          </button>

          {/* Footer */}
          <div className="text-xs text-gray-300 text-center">
            No account?{' '}
            <Link to="/signup" className="text-blue-400 hover:underline">
              Sign up
            </Link>
          </div>
        </form>
      </div>

      {/* Footer note */}
      <footer className="absolute bottom-2 w-full text-center text-[10px] text-gray-400">
        © 2025 Chemical Equipment Visualizer — Developed by Yash Kate
      </footer>
    </div>
  )
}

