import React, { useEffect, useState } from 'react'
import api from '../api/client'
import { useNavigate } from 'react-router-dom'

function DatasetList({ changed, onOpenDashboard }){
  const [items, setItems] = useState([])
  const [error, setError] = useState('')
  const navigate = useNavigate()

  const load = async ()=>{
    setError('')
    try{
      const { data } = await api.get('/datasets/')
      setItems(data)
    }catch(err){ setError('Failed to load datasets') }
  }

  useEffect(()=>{ load() }, [changed])

  const downloadReport = async (id)=>{
    try{
      const resp = await api.get(`/datasets/${id}/report/`, { responseType: 'blob' })
      const url = window.URL.createObjectURL(new Blob([resp.data]))
      const a = document.createElement('a')
      a.href = url
      a.download = `dataset_${id}_report.pdf`
      a.click()
      window.URL.revokeObjectURL(url)
    }catch(e){ alert('Download failed') }
  }

  return (
    <div className="bg-white p-4 rounded shadow overflow-hidden">
      <h2 className="font-medium mb-2">Last 5 Datasets</h2>
      {error && <p className="text-red-600 text-sm mb-2">{error}</p>}
      <ul className="space-y-2 max-h-96 overflow-auto pr-1">
        {items.map(it=> (
          <li key={it.id} className="flex items-center justify-between border p-2 rounded bg-white">
            <div className="min-w-0">
              <div className="font-medium truncate" title={it.filename || `Dataset ${it.id}`}>{it.filename || `Dataset ${it.id}`}</div>
              <div className="text-xs text-gray-500">ID: {it.id} · {it.created_at ? new Date(it.created_at).toLocaleString() : ''}</div>
            </div>
            <div className="flex items-center gap-2">
              <button onClick={()=> navigate(`/dashboard/${it.id}`)} className="bg-blue-600 text-white px-3 py-1 rounded">Dashboard</button>
              <button onClick={()=>downloadReport(it.id)} className="bg-green-600 text-white px-3 py-1 rounded">Report</button>
            </div>
          </li>
        ))}
        {items.length === 0 && <li className="text-sm text-gray-500">No datasets yet</li>}
      </ul>
    </div>
  )
}
export default DatasetList
