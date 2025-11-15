import React, { useState } from 'react'
import api from '../api/client'
import { toast } from 'sonner'
import { UploadCloud } from 'lucide-react'

function UploadForm({ onUploaded }) {
  const [file, setFile] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  const handleSubmit = async (e) => {
    e.preventDefault()
    if (!file) {
      setError('Please select a CSV or XLSX file')
      return
    }

    setLoading(true)
    setError('')

    try {
      const form = new FormData()
      form.append('file', file)

      const { data } = await api.post('/upload/', form, {
        headers: { 'Content-Type': 'multipart/form-data' }
      })

      onUploaded && onUploaded(data)
      toast.success('Upload successful!')
    } catch (err) {
      const msg = err?.response?.data?.detail || 'Upload failed'
      setError(msg)
      toast.error(msg)
    } finally {
      setLoading(false)
    }
  }

  return (
    <form
      onSubmit={handleSubmit}
      className="p-6 rounded-2xl bg-white/50 backdrop-blur-xl shadow-lg border border-white/40
                 transition hover:shadow-xl"
    >
      {/* Header */}
      <div className="flex items-center gap-3 mb-3">
        <div className="h-10 w-10 rounded-xl bg-blue-600 text-white grid place-items-center shadow-md">
          <UploadCloud size={20} />
        </div>
        <div>
          <h3 className="text-lg font-semibold text-gray-900">Upload Your Dataset</h3>
          <p className="text-xs text-gray-600">
            Supported: <b>.csv</b>, <b>.xlsx</b> • Max ~5MB recommended
          </p>
        </div>
      </div>

      {/* file input */}
      <label className="block">
        <input
          type="file"
          accept=".csv,.xlsx"
          onChange={(e) => setFile(e.target.files?.[0] || null)}
          className="block w-full text-sm text-gray-800 cursor-pointer
                     bg-white border border-gray-300 rounded-lg p-2
                     focus:outline-none focus:ring-2 focus:ring-blue-500"
        />
      </label>

      {/* Error */}
      {error && (
        <div className="text-sm text-red-600 mt-1 font-medium">{error}</div>
      )}

      {/* Upload Button */}
      <div className="mt-4">
        <button
          disabled={loading}
          className="w-full flex items-center justify-center gap-2 px-4 py-2.5
                     bg-blue-600 hover:bg-blue-700 text-white font-medium 
                     rounded-lg shadow-md transition-all
                     disabled:opacity-50 disabled:cursor-not-allowed"
        >
          <UploadCloud size={18} className={`${loading ? 'animate-pulse' : ''}`} />
          {loading ? 'Uploading…' : 'Upload Dataset'}
        </button>
      </div>
    </form>
  )
}

export default UploadForm

