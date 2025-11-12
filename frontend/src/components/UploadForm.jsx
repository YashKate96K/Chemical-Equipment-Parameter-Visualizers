import React, { useState } from 'react'
import api from '../api/client'
import { toast } from 'sonner'
import { UploadCloud } from 'lucide-react'

function UploadForm({ onUploaded }){
  const [file, setFile] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  const handleSubmit = async (e)=>{
    e.preventDefault()
    if(!file) { setError('Please select a CSV file'); return }
    setLoading(true); setError('')
    try{
      const form = new FormData()
      form.append('file', file)
      const { data } = await api.post('/upload/', form, { headers: { 'Content-Type': 'multipart/form-data' } })
      onUploaded && onUploaded(data)
      toast.success('Upload successful. Quick Summary updated.')
    }catch(err){
      const msg = err?.response?.data?.detail || 'Upload failed'
      setError(msg)
      toast.error(msg)
    }finally{
      setLoading(false)
    }
  }

  return (
    <form onSubmit={handleSubmit} className="bg-white/60 backdrop-blur p-4 rounded-xl shadow border space-y-3">
      <div className="flex items-center gap-2">
        <div className="h-8 w-8 rounded-md bg-blue-600/90 text-white grid place-items-center shadow"><UploadCloud size={16} /></div>
        <div>
          <div className="font-medium leading-tight">Upload CSV or XLSX</div>
          <div className="text-xs text-gray-500">Supported: .csv, .xlsx • Max ~5MB recommended</div>
        </div>
      </div>
      <input type="file" accept=".csv,.xlsx" onChange={e=> setFile(e.target.files?.[0]||null)} className="block text-sm" />
      {error && <div className="text-sm text-red-600">{error}</div>}
      <div className="flex gap-2">
        <button disabled={loading} className="inline-flex items-center gap-2 bg-blue-600 hover:bg-blue-700 transition-colors text-white px-4 py-2 rounded-md disabled:opacity-50">
          {loading ? 'Uploading…' : 'Upload'}
        </button>
      </div>
    </form>
  )
}
export default UploadForm
