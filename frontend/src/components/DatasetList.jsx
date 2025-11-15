import React, { useEffect, useState } from 'react'
import api from '../api/client'
import { useNavigate } from 'react-router-dom'
import { FileText, BarChart3 } from 'lucide-react'

function DatasetList({ changed }) {
  const [items, setItems] = useState([])
  const [error, setError] = useState('')
  const navigate = useNavigate()

  const load = async () => {
    try {
      const { data } = await api.get('/datasets/')
      setItems(data)
    } catch {
      setError('Failed to load datasets')
    }
  }

  useEffect(() => { load() }, [changed])

  const downloadReport = async (id) => {
    try {
      const resp = await api.get(`/datasets/${id}/report/`, { responseType: 'blob' })
      const url = window.URL.createObjectURL(new Blob([resp.data]))
      const a = document.createElement('a')
      a.href = url
      a.download = `dataset_${id}_report.pdf`
      a.click()
      window.URL.revokeObjectURL(url)
    } catch {
      alert('Download failed')
    }
  }

  return (
    <div className="p-6 rounded-xl bg-white/30 backdrop-blur-lg shadow-lg border border-white/40">
      <h2 className="text-lg font-semibold text-gray-900 mb-4">Recent Datasets</h2>

      {error && <p className="text-red-600 text-sm mb-2">{error}</p>}

      <ul className="space-y-3 max-h-[500px] overflow-auto pr-1">
        {items.map(it => (
          <li
            key={it.id}
            className="flex flex-col gap-2 p-4 rounded-xl 
                       bg-white shadow-sm border border-gray-200
                       hover:shadow-md hover:bg-white/90 transition"
          >
            {/* Filename */}
            <div className="text-base font-medium text-gray-900 truncate" title={it.filename}>
              {it.filename || `Dataset ${it.id}`}
            </div>

            {/* ID + Date neatly aligned */}
            <div className="text-xs text-gray-700 flex items-center gap-2">
              <span className="font-semibold">ID:</span> {it.id}
              <span className="mx-1">•</span>
              {it.created_at ? new Date(it.created_at).toLocaleString() : ""}
            </div>

            {/* Buttons */}
            <div className="flex items-center gap-3 mt-1">
              <button
                onClick={() => navigate(`/dashboard/${it.id}`)}
                className="flex items-center gap-1 bg-emerald-600 hover:bg-emerald-700
                           text-white text-sm px-4 py-1.5 rounded-lg shadow 
                           transition"
              >
                <BarChart3 size={14} />
                Dashboard
              </button>

              <button
                onClick={() => downloadReport(it.id)}
                className="flex items-center gap-1 bg-teal-600 hover:bg-teal-700
                           text-white text-sm px-4 py-1.5 rounded-lg shadow
                           transition"
              >
                <FileText size={14} />
                Report
              </button>
            </div>
          </li>
        ))}

        {items.length === 0 && (
          <li className="text-sm text-gray-600">No datasets found</li>
        )}
      </ul>
    </div>
  )
}

export default DatasetList

