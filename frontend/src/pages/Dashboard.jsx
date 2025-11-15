import React, { useEffect, useState } from 'react'
import { useParams, Link } from 'react-router-dom'
import api from '../api/client'
import DynamicExplorer from '../components/DynamicExplorer'

class ErrorBoundary extends React.Component{
  constructor(p){ super(p); this.state={ hasError:false, error:null } }
  static getDerivedStateFromError(error){ return { hasError:true, error } }
  componentDidCatch(error, info){ /* no-op */ }
  render(){
    if(this.state.hasError){
      return <div className="bg-white/80 rounded-xl p-4 border text-red-700">Dashboard failed to render. Please share this message: {String(this.state.error)}</div>
    }
    return this.props.children
  }
}

function DashboardPage(){
  const { id } = useParams()
  const datasetId = parseInt(id, 10)
  const [rows, setRows] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  useEffect(()=>{
    let alive = true
    async function load(){
      if(!Number.isFinite(datasetId)) return
      setLoading(true); setError('')
      try{
        const { data } = await api.get(`/datasets/${datasetId}/health/`)
        if(alive) setRows(data?.rows || [])
      }catch(e){ if(alive) setError('Failed to load dataset') }
      finally{ if(alive) setLoading(false) }
    }
    load();
    return ()=>{ alive = false }
  }, [datasetId])

  return (
    <div className="min-h-screen relative text-gray-900 overflow-hidden">
      <header className="sticky top-0 backdrop-blur-2xl bg-white/10 border-b border-white/20 shadow z-20">
        <div className="max-w-7xl mx-auto px-6 py-4 flex items-center justify-between">
          <div className="text-white font-semibold">Dynamic Data Explorer Dashboard</div>
          <Link to="/" className="text-teal-100 hover:text-white underline">Home</Link>
        </div>
      </header>
      <main className="max-w-7xl mx-auto px-6 py-8">
        {!Number.isFinite(datasetId) && (
          <div className="bg-white/80 rounded-xl p-4 border">Invalid dataset id</div>
        )}
        {Number.isFinite(datasetId) && (
          loading ? (
            <div className="bg-white/80 rounded-xl p-4 border">Loading…</div>
          ) : error ? (
            <div className="bg-white/80 rounded-xl p-4 border text-red-600">{error}</div>
          ) : (
            <>
              <div className="mb-3 text-xs text-gray-600">Rows loaded: {rows?.length ?? 0}</div>
              {Array.isArray(rows) && rows.length>0 ? (
                <ErrorBoundary>
                  <DynamicExplorer rows={rows} />
                </ErrorBoundary>
              ) : (
                <div className="bg-white/80 rounded-xl p-4 border">No rows found for this dataset. Upload a dataset and try again.</div>
              )}
            </>
          )
        )}
      </main>
    </div>
  )
}

export default DashboardPage
