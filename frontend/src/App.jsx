import React, { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { Beaker } from 'lucide-react'
import UploadForm from './components/UploadForm'
import DatasetList from './components/DatasetList'
import ChartPanel from './components/ChartPanel'
import TablePreview from './components/TablePreview'

function App(){
  const [summary, setSummary] = useState(null)
  const [preview, setPreview] = useState('')
  const [datasetsChanged, setDatasetsChanged] = useState(0)
  const [lastDatasetId, setLastDatasetId] = useState(null)

  // Hydrate from localStorage on mount
  useEffect(()=>{
    try{
      const s = localStorage.getItem('last_summary')
      const p = localStorage.getItem('last_preview')
      const id = localStorage.getItem('last_dataset_id')
      if(s){ setSummary(JSON.parse(s)) }
      if(p){ setPreview(p) }
      if(id){ setLastDatasetId(parseInt(id, 10)) }
    }catch{}
  }, [])

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 to-slate-100 text-gray-900">
      <header className="sticky top-0 z-10 backdrop-blur bg-white/60 border-b">
        <div className="max-w-6xl mx-auto px-4 py-3 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="h-9 w-9 rounded-lg bg-blue-600/90 text-white grid place-items-center shadow">
              <Beaker size={18} />
            </div>
            <div>
              <h1 className="text-xl font-semibold leading-tight">Chemical Equipment Parameter Visualizer</h1>
              <p className="text-xs text-gray-600">Upload data, see Quick Summary here, open the full Dashboard from the list</p>
            </div>
          </div>
          {lastDatasetId && (
            <Link to={`/dashboard/${lastDatasetId}`} className="inline-flex items-center gap-1 bg-blue-600 hover:bg-blue-700 text-white text-sm px-3 py-1.5 rounded-full shadow transition-colors">Resume Dashboard →</Link>
          )}
        </div>
        <div className="h-0.5 bg-gradient-to-r from-blue-600 via-emerald-500 to-orange-400 opacity-60"></div>
      </header>
      <main className="max-w-6xl mx-auto px-4 py-6">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <div className="md:col-span-2 space-y-6">
            <UploadForm onUploaded={(res)=>{ 
              setSummary(res.summary_json); 
              setPreview(res.preview_csv); 
              setDatasetsChanged(x=>x+1); 
              setLastDatasetId(res.id);
              try{
                localStorage.setItem('last_summary', JSON.stringify(res.summary_json))
                localStorage.setItem('last_preview', res.preview_csv || '')
                localStorage.setItem('last_dataset_id', String(res.id))
              }catch{}
            }} />
            <div className="flex items-center justify-between">
              <h2 className="font-medium text-lg">Quick Summary</h2>
              {lastDatasetId && (
                <Link to={`/dashboard/${lastDatasetId}`} className="text-blue-600 hover:underline">Open Dashboard →</Link>
              )}
            </div>
            <ChartPanel summary={summary} />
            <TablePreview csvText={preview} />
          </div>
          <div className="md:col-span-1">
            <DatasetList changed={datasetsChanged} />
          </div>
        </div>
      </main>
    </div>
  )
}
export default App
