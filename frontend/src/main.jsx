import React from 'react'
import { createRoot } from 'react-dom/client'
import App from './App'
import './index.css'
import { BrowserRouter, Routes, Route } from 'react-router-dom'
import DashboardPage from './pages/Dashboard'
import { Toaster } from 'sonner'

createRoot(document.getElementById('root')).render(
  <React.StrictMode>
    <BrowserRouter>
      <Toaster richColors position="top-right" />
      <Routes>
        <Route path="/" element={<App />} />
        <Route path="/dashboard/:id" element={<DashboardPage />} />
      </Routes>
    </BrowserRouter>
  </React.StrictMode>
)
