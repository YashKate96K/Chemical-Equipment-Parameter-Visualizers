import React from 'react'
import { createRoot } from 'react-dom/client'
import App from './App'
import './index.css'
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import DashboardPage from './pages/Dashboard'
import { Toaster } from 'sonner'
import SignIn from './pages/SignIn'
import SignUp from './pages/SignUp'

function RequireAuth({ children }){
  const token = (()=>{ try { return localStorage.getItem('auth_token') } catch { return null } })()
  const sessionAuthed = (()=>{ try { return sessionStorage.getItem('session_authed') } catch { return null } })()
  if(!token || !sessionAuthed){
    return <Navigate to="/signin" replace />
  }
  return children
}

function RedirectIfAuthed({ children }){
  const token = (()=>{ try { return localStorage.getItem('auth_token') } catch { return null } })()
  const sessionAuthed = (()=>{ try { return sessionStorage.getItem('session_authed') } catch { return null } })()
  if(token && sessionAuthed){
    return <Navigate to="/" replace />
  }
  return children
}

createRoot(document.getElementById('root')).render(
  <React.StrictMode>
    <BrowserRouter>
      <Toaster richColors position="top-right" />
      <Routes>
        <Route path="/" element={<RequireAuth><App /></RequireAuth>} />
        <Route path="/dashboard/:id" element={<RequireAuth><DashboardPage /></RequireAuth>} />
        <Route path="/signin" element={<RedirectIfAuthed><SignIn /></RedirectIfAuthed>} />
        <Route path="/signup" element={<RedirectIfAuthed><SignUp /></RedirectIfAuthed>} />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </BrowserRouter>
  </React.StrictMode>
)
