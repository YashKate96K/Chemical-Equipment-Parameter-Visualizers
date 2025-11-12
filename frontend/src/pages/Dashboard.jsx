import React from 'react'
import { useParams, Link } from 'react-router-dom'
import HealthDashboard from '../components/HealthDashboard'

function DashboardPage(){
  const { id } = useParams()
  const datasetId = parseInt(id, 10)
  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 to-slate-100 text-gray-900">
      <header className="sticky top-0 z-10 backdrop-blur bg-white/60 border-b">
        <div className="max-w-6xl mx-auto px-4 py-3 flex items-center justify-between">
          <div className="font-semibold">Equipment Health Overview</div>
          <Link to="/" className="text-blue-600 hover:underline">Home</Link>
        </div>
      </header>
      <main className="max-w-6xl mx-auto px-4 py-6 space-y-4">
        <div className="bg-white/60 backdrop-blur rounded-xl border p-4">
          <div className="flex items-baseline justify-between">
            <div>
              <h1 className="text-xl font-semibold">Equipment Health Overview Dashboard</h1>
              <p className="text-sm text-gray-600">A quick look at system performance and health</p>
            </div>
            <div className="text-sm text-gray-500">Dataset ID: {datasetId}</div>
          </div>
        </div>
        {Number.isFinite(datasetId) ? (
          <HealthDashboard datasetId={datasetId} />
        ) : (
          <div className="bg-white/60 backdrop-blur rounded-xl border p-4">Invalid dataset id</div>
        )}
      </main>
    </div>
  )
}

export default DashboardPage
