import React, { useEffect, useMemo, useState } from 'react'
import api from '../api/client'
import { Pie, Scatter, Bar } from 'react-chartjs-2'
import { Chart as ChartJS, ArcElement, Tooltip, Legend, PointElement, LinearScale, BarElement, CategoryScale } from 'chart.js'
import { Gauge, Cog, Thermometer, PieChart, ScatterChart, TrendingUp } from 'lucide-react'
import { motion } from 'framer-motion'
import { toast } from 'sonner'

ChartJS.register(ArcElement, Tooltip, Legend, PointElement, LinearScale, BarElement, CategoryScale)

function KpiCard({ title, value, unit, Icon, subtext, color="text-gray-900" }){
  return (
    <motion.div whileHover={{ y: -2 }} className="flex-1 bg-white/60 backdrop-blur rounded-xl shadow-sm p-4 border">
      <div className="flex items-center gap-2 text-sm text-gray-500"><Icon size={16} /> {title}</div>
      <div className={`mt-1 text-2xl font-semibold ${color}`}>{value ?? '—'}{unit ? <span className="text-base font-normal text-gray-500 ml-1">{unit}</span> : null}</div>
      {subtext && <div className="text-xs text-gray-500 mt-1">{subtext}</div>}
    </motion.div>
  )
}

function HealthDashboard({ datasetId }){
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [data, setData] = useState(null)

  useEffect(()=>{
    let alive = true
    async function load(){
      setLoading(true); setError('')
      try{
        const resp = await api.get(`/datasets/${datasetId}/health/`)
        if(alive) setData(resp.data)
      }catch(e){ if(alive){ setError('Failed to load dashboard data'); toast.error('Failed to load dashboard data') } }
      finally{ if(alive) setLoading(false) }
    }
    if(datasetId) load()
    return ()=>{ alive = false }
  }, [datasetId])

  // Build pie data for Type distribution
  const pieData = useMemo(()=>{
    const dist = data?.summary?.type_distribution || {}
    const labels = Object.keys(dist)
    const values = Object.values(dist)
    const palette = ['#2196F3','#4CAF50','#FF9800','#8B5CF6','#EF4444','#06B6D4','#22C55E']
    return {
      labels,
      datasets: [{
        data: values,
        backgroundColor: labels.map((_,i)=> palette[i % palette.length])
      }]
    }
  }, [data])

  if(loading) return <div className="p-6 bg-white rounded shadow">Loading dashboard…</div>
  if(error) return <div className="p-6 bg-white rounded shadow text-red-600">{error}</div>
  if(!data) return null

  const k = data.kpis || {}
  const clusters = data.clustering || { k:0, labels:[], rec_ids:[] }
  const quality = data.data_quality || {}
  const averages = data.summary?.averages || {}
  const corr = data.correlations || { matrix: [], order: [] }

  const avgLabels = Object.keys(averages)
  const avgValues = avgLabels.map(k => averages[k])
  const palette = ['#3b82f6', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6', '#22c55e', '#06b6d4', '#eab308']
  const avgColors = avgLabels.map((_, i) => palette[i % palette.length])
  const avgBarData = { labels: avgLabels, datasets: [{ label: 'Average', data: avgValues, backgroundColor: avgColors }] }

  return (
    <div className="space-y-6">
      {/* KPI Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <KpiCard title="Average Flowrate" value={k.average_flowrate?.toFixed?.(2)} unit="L/s" Icon={Gauge} subtext="Normal range: 40–50 L/s" color="text-blue-600" />
        <KpiCard title="Average Pressure" value={k.average_pressure?.toFixed?.(2)} unit="PSI" Icon={Cog} subtext="Normal range: 4–8 PSI" color="text-green-600" />
        <KpiCard title="Average Temperature" value={k.average_temperature?.toFixed?.(2)} unit="°C" Icon={Thermometer} subtext="Normal range: 55–65 °C" color="text-orange-600" />
      </div>

      {/* Charts: keep only equipment count pie chart */}
      <div className="bg-white/60 backdrop-blur rounded-xl shadow-sm p-4 border">
        <div className="font-medium mb-2">Equipment Type Distribution</div>
        <div className="max-w-md">
          <Pie data={pieData} />
        </div>
      </div>

      {/* Cluster Scatter (Flowrate vs Pressure, colored by cluster) */}
      {clusters.k > 0 && (
        <div className="bg-white/60 backdrop-blur rounded-xl shadow-sm p-4 border">
          <div className="font-medium mb-2">Clusters (K-Means)</div>
          <Scatter
            data={{
              datasets: (()=>{
                // Build points grouped by label
                const rowsById = new Map((data.rows||[]).map(r=> [r.Record, r]))
                const sets = Array.from({length: clusters.k}, (_,i)=> ({ label:`Cluster ${i+1}`, data:[], backgroundColor: ['#2563eb','#16a34a','#fb923c','#a855f7'][i%4] }))
                clusters.rec_ids.forEach((recId, idx)=>{
                  const label = clusters.labels[idx]
                  const r = rowsById.get(recId)
                  if(r && typeof r.Flowrate==='number' && typeof r.Pressure==='number'){
                    sets[label].data.push({ x: r.Flowrate, y: r.Pressure })
                  }
                })
                return sets
              })()
            }}
            options={{ scales:{ x:{ title:{ display:true, text:'Flowrate' } }, y:{ title:{ display:true, text:'Pressure' } } }, plugins:{ legend:{ position:'bottom' } } }}
            height={220}
          />
        </div>
      )}

      {/* Averages for all numeric columns */}
      {avgLabels.length > 0 && (
        <div className="bg-white/60 backdrop-blur rounded-xl shadow-sm p-4 border">
          <div className="font-medium mb-2">Averages (All Numeric Columns)</div>
          <div className="bg-white p-2 border rounded">
            <Bar data={avgBarData} />
          </div>
        </div>
      )}

      {/* Correlation Diagram */}
      {Array.isArray(corr.matrix) && corr.matrix.length > 0 && (
        <div className="bg-white/60 backdrop-blur rounded-xl shadow-sm p-4 border overflow-auto">
          <div className="font-medium mb-2">Correlation Heatmap</div>
          <table className="text-sm border-collapse">
            <thead>
              <tr>
                <th className="p-2 text-left">Var</th>
                {corr.order.map((h) => (
                  <th key={h} className="p-2 text-left">{h}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {corr.matrix.map((row, i) => (
                <tr key={i}>
                  <td className="p-2 pr-4 font-medium">{corr.order[i]}</td>
                  {row.map((v, j) => {
                    const val = typeof v === 'number' ? v : 0
                    // Map r in [-1,1] to a blue-red background; white around 0
                    const intensity = Math.min(1, Math.abs(val))
                    const red = val > 0 ? Math.round(255 * intensity) : 0
                    const blue = val < 0 ? Math.round(255 * intensity) : 0
                    const bg = `rgba(${red}, ${0}, ${blue}, 0.15)`
                    return (
                      <td key={j} className="p-2 border" style={{ backgroundColor: bg }}>
                        {val.toFixed(2)}
                      </td>
                    )
                  })}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      

      {/* Anomalies */}
      {/* Anomalies section removed per request */}

      {/* Summary Table removed per request */}

      {/* Dynamic Insights */}
      <div className="bg-white/60 backdrop-blur rounded-xl shadow-sm p-4 border">
        <div className="font-medium mb-2">Key Insights</div>
        <ul className="list-disc ml-6 text-sm space-y-1">
          {(() => {
            const insights = []
            const rows = data.rows || []
            const flow = rows.map(r=> r.Flowrate).filter(v=> typeof v==='number')
            const press = rows.map(r=> r.Pressure).filter(v=> typeof v==='number')
            const temp = rows.map(r=> r.Temperature).filter(v=> typeof v==='number')
            const mean = arr => arr.length ? (arr.reduce((a,b)=>a+b,0)/arr.length) : null
            const mf = mean(flow), mp = mean(press), mt = mean(temp)
            if(mf!=null && mp!=null) insights.push(`⚙️ Flowrate and Pressure behave normally around averages (${mf.toFixed(2)} L/s, ${mp.toFixed(2)} PSI).`)
            if(mt!=null) insights.push(`🌡️ Average temperature is ${mt.toFixed(2)} °C.`)
            const highT = temp.filter(v=> v>65).length
            if(highT>0) insights.push(`🔥 ${highT} reading(s) above 65°C detected.`)
            // correlations
            const strongest = data.correlations?.strongest_pairs || []
            strongest.slice(0,1).forEach(p=> insights.push(`📈 Strongest correlation: ${p.cols[0]} vs ${p.cols[1]} (r=${p.corr.toFixed(2)})`))
            // variance/skewness highlights
            const vs = data.variance_skewness || {}
            const highestVar = Object.entries(vs).sort((a,b)=> (b[1]?.variance||0)-(a[1]?.variance||0))[0]
            if(highestVar) insights.push(`📊 Highest variance: ${highestVar[0]} (${(highestVar[1].variance||0).toFixed(2)})`)
            if(rows.length>0) insights.push(`✅ Processed ${rows.length} records with no missing required fields.`)
            return insights.map((t,i)=> <li key={i}>{t}</li>)
          })()}
        </ul>
      </div>

      {/* Data Quality Summary */}
      <div className="bg-white/60 backdrop-blur rounded-xl shadow-sm p-4 border">
        <div className="font-medium mb-2">Data Quality</div>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-sm">
          <div>
            <div className="text-gray-500">Missing values</div>
            <ul className="mt-1">
              {Object.entries(quality.missing_values||{}).slice(0,5).map(([k,v])=>(<li key={k}>{k}: {v}</li>))}
            </ul>
          </div>
          <div>
            <div className="text-gray-500">Duplicates</div>
            <div>Count: {quality.duplicate_rows?.count||0}</div>
          </div>
          <div>
            <div className="text-gray-500">Schema Drift</div>
            <div className="text-xs">Added: {(quality.schema_drift?.added_columns||[]).join(', ')||'—'}</div>
            <div className="text-xs">Removed: {(quality.schema_drift?.removed_columns||[]).join(', ')||'—'}</div>
          </div>
        </div>
      </div>
    </div>
  )
}

export default HealthDashboard
