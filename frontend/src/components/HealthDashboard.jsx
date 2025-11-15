import React, { useEffect, useMemo, useState } from 'react'
import api from '../api/client'
import { Pie, Scatter, Bar } from 'react-chartjs-2'
import {
  Chart as ChartJS,
  ArcElement,
  Tooltip,
  Legend,
  PointElement,
  LinearScale,
  BarElement,
  CategoryScale,
} from 'chart.js'
import { Gauge, Cog, Thermometer } from 'lucide-react'
import { motion } from 'framer-motion'
import { toast } from 'sonner'

ChartJS.register(
  ArcElement,
  Tooltip,
  Legend,
  PointElement,
  LinearScale,
  BarElement,
  CategoryScale
)

/**
 * Soft-Minimal KPI card (Apple-like)
 */
function KpiCard({ title, value, unit, Icon, subtext, colorClass = 'text-gray-900' }) {
  return (
    <motion.div
      whileHover={{ y: -3 }}
      className="flex-1 bg-white rounded-2xl shadow-sm p-4 border border-gray-100"
    >
      <div className="flex items-center gap-3">
        <div className="p-2 rounded-lg bg-gray-50 border border-gray-100">
          <Icon size={18} className="text-gray-600" />
        </div>
        <div className="text-sm text-gray-500">{title}</div>
      </div>

      <div className={`mt-3 text-2xl font-semibold ${colorClass}`}>
        {value ?? '—'}
        {unit ? <span className="text-base font-medium text-gray-500 ml-1">{unit}</span> : null}
      </div>

      {subtext && <div className="text-xs text-gray-400 mt-1">{subtext}</div>}
    </motion.div>
  )
}

function HealthDashboard({ datasetId }) {
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [data, setData] = useState(null)

  useEffect(() => {
    let alive = true
    async function load() {
      setLoading(true)
      setError('')
      try {
        const resp = await api.get(`/datasets/${datasetId}/health/`)
        if (alive) setData(resp.data)
      } catch (e) {
        if (alive) {
          setError('Failed to load dashboard data')
          toast.error('Failed to load dashboard data')
        }
      } finally {
        if (alive) setLoading(false)
      }
    }
    if (datasetId) load()
    return () => {
      alive = false
    }
  }, [datasetId])

  // Pie data for type distribution
  const pieData = useMemo(() => {
    const dist = data?.summary?.type_distribution || {}
    const labels = Object.keys(dist)
    const values = Object.values(dist)
    const palette = ['#3b82f6', '#10b981', '#f59e0b', '#8b5cf6', '#ef4444', '#06b6d4']
    return {
      labels,
      datasets: [
        {
          data: values,
          backgroundColor: labels.map((_, i) => palette[i % palette.length]),
        },
      ],
    }
  }, [data])

  if (loading)
    return (
      <div className="p-6 bg-white rounded-2xl shadow border border-gray-100">
        Loading dashboard…
      </div>
    )
  if (error)
    return (
      <div className="p-6 bg-white rounded-2xl shadow border border-red-100 text-red-600">
        {error}
      </div>
    )
  if (!data) return null

  const k = data.kpis || {}
  const clusters = data.clustering || { k: 0, labels: [], rec_ids: [] }
  const quality = data.data_quality || {}
  const averages = data.summary?.averages || {}
  const corr = data.correlations || { matrix: [], order: [] }

  const avgLabels = Object.keys(averages)
  const avgValues = avgLabels.map((kk) => averages[kk])
  const palette = ['#3b82f6', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6', '#22c55e', '#06b6d4']
  const avgColors = avgLabels.map((_, i) => palette[i % palette.length])
  const avgBarData = { labels: avgLabels, datasets: [{ label: 'Average', data: avgValues, backgroundColor: avgColors }] }

  return (
    <div className="space-y-6">
      {/* KPI Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <KpiCard
          title="Average Flowrate"
          value={k.average_flowrate?.toFixed?.(2)}
          unit="L/s"
          Icon={Gauge}
          subtext="Normal range: 40–50 L/s"
          colorClass="text-blue-600"
        />
        <KpiCard
          title="Average Pressure"
          value={k.average_pressure?.toFixed?.(2)}
          unit="PSI"
          Icon={Cog}
          subtext="Normal range: 4–8 PSI"
          colorClass="text-green-600"
        />
        <KpiCard
          title="Average Temperature"
          value={k.average_temperature?.toFixed?.(2)}
          unit="°C"
          Icon={Thermometer}
          subtext="Normal range: 55–65 °C"
          colorClass="text-orange-600"
        />
      </div>

      {/* Equipment Type Distribution */}
      <div className="bg-white rounded-2xl shadow-sm p-4 border border-gray-100">
        <div className="flex items-center justify-between mb-3">
          <div className="text-md font-medium text-gray-800">Equipment Type Distribution</div>
          <div className="text-xs text-gray-400">Proportional breakdown by type</div>
        </div>

        <div className="flex items-start gap-6">
          <div className="w-full max-w-xs">
            <Pie data={pieData} />
          </div>

          <div className="flex-1">
            <ul className="space-y-2 text-sm">
              {(data?.summary?.type_distribution
                ? Object.entries(data.summary.type_distribution)
                : []
              ).map(([t, v], i) => (
                <li key={t} className="flex items-center gap-3 text-gray-700">
                  <span style={{ width: 12, height: 12, background: pieData.datasets[0].backgroundColor[i], borderRadius: 4 }} />
                  <span className="font-medium">{t}</span>
                  <span className="text-xs text-gray-400 ml-2">{v} items</span>
                </li>
              ))}
            </ul>
          </div>
        </div>
      </div>

      {/* Clusters (if present) */}
      {clusters.k > 0 && (
        <div className="bg-white rounded-2xl shadow-sm p-4 border border-gray-100">
          <div className="flex items-center justify-between mb-3">
            <div className="text-md font-medium text-gray-800">Clusters (K-Means)</div>
            <div className="text-xs text-gray-400">Flowrate vs Pressure</div>
          </div>

          <Scatter
            data={{
              datasets: (() => {
                const rowsById = new Map((data.rows || []).map((r) => [r.Record, r]))
                const sets = Array.from({ length: clusters.k }, (_, i) => ({
                  label: `Cluster ${i + 1}`,
                  data: [],
                  backgroundColor: ['#2563eb', '#16a34a', '#fb923c', '#a855f7'][i % 4],
                }))
                clusters.rec_ids.forEach((recId, idx) => {
                  const label = clusters.labels[idx]
                  const r = rowsById.get(recId)
                  if (r && typeof r.Flowrate === 'number' && typeof r.Pressure === 'number') {
                    sets[label].data.push({ x: r.Flowrate, y: r.Pressure })
                  }
                })
                return sets
              })(),
            }}
            options={{
              scales: { x: { title: { display: true, text: 'Flowrate' } }, y: { title: { display: true, text: 'Pressure' } } },
              plugins: { legend: { position: 'bottom' } },
            }}
            height={240}
          />
        </div>
      )}

      {/* Averages */}
      {avgLabels.length > 0 && (
        <div className="bg-white rounded-2xl shadow-sm p-4 border border-gray-100">
          <div className="flex items-center justify-between mb-3">
            <div className="text-md font-medium text-gray-800">Averages (Numeric Columns)</div>
            <div className="text-xs text-gray-400">Mean values per column</div>
          </div>

          <div className="bg-white border border-gray-100 rounded p-3">
            <Bar data={avgBarData} />
          </div>
        </div>
      )}

      {/* Correlation Heatmap */}
      {Array.isArray(corr.matrix) && corr.matrix.length > 0 && (
        <div className="bg-white rounded-2xl shadow-sm p-4 border border-gray-100 overflow-auto">
          <div className="flex items-center justify-between mb-3">
            <div className="text-md font-medium text-gray-800">Correlation Heatmap</div>
            <div className="text-xs text-gray-400">Pearson correlation coefficients</div>
          </div>

          <div className="overflow-auto">
            <table className="w-full text-sm border-collapse">
              <thead>
                <tr>
                  <th className="p-2 text-left font-medium text-gray-700">Var</th>
                  {corr.order.map((h) => (
                    <th key={h} className="p-2 text-left text-gray-600">{h}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {corr.matrix.map((row, i) => (
                  <tr key={i} className={i % 2 === 0 ? 'bg-gray-50' : ''}>
                    <td className="p-2 pr-4 font-medium text-gray-700">{corr.order[i]}</td>
                    {row.map((v, j) => {
                      const val = typeof v === 'number' ? v : 0
                      const intensity = Math.min(1, Math.abs(val))
                      const red = val > 0 ? Math.round(255 * intensity) : 0
                      const blue = val < 0 ? Math.round(255 * intensity) : 0
                      const bg = `rgba(${red}, ${0}, ${blue}, 0.08)`
                      return (
                        <td key={j} className="p-2 text-sm text-gray-700" style={{ backgroundColor: bg }}>
                          {val.toFixed(2)}
                        </td>
                      )
                    })}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Key Insights */}
      <div className="bg-white rounded-2xl shadow-sm p-4 border border-gray-100">
        <div className="flex items-center justify-between mb-3">
          <div className="text-md font-medium text-gray-800">Key Insights</div>
          <div className="text-xs text-gray-400">Auto-generated by the analyzer</div>
        </div>

        <ul className="list-disc ml-5 text-sm space-y-1 text-gray-700">
          {(() => {
            const insights = []
            const rows = data.rows || []
            const flow = rows.map((r) => r.Flowrate).filter((v) => typeof v === 'number')
            const press = rows.map((r) => r.Pressure).filter((v) => typeof v === 'number')
            const temp = rows.map((r) => r.Temperature).filter((v) => typeof v === 'number')
            const mean = (arr) => (arr.length ? arr.reduce((a, b) => a + b, 0) / arr.length : null)
            const mf = mean(flow), mp = mean(press), mt = mean(temp)
            if (mf != null && mp != null) insights.push(`Flowrate and Pressure averages: ${mf.toFixed(2)} L/s, ${mp.toFixed(2)} PSI.`)
            if (mt != null) insights.push(`Average temperature: ${mt.toFixed(2)} °C.`)
            const highT = temp.filter((v) => v > 65).length
            if (highT > 0) insights.push(`${highT} reading(s) above 65°C detected.`)
            const strongest = data.correlations?.strongest_pairs || []
            strongest.slice(0, 1).forEach((p) => insights.push(`Strongest correlation: ${p.cols[0]} vs ${p.cols[1]} (r=${p.corr.toFixed(2)})`))
            const vs = data.variance_skewness || {}
            const highestVar = Object.entries(vs).sort((a, b) => (b[1]?.variance || 0) - (a[1]?.variance || 0))[0]
            if (highestVar) insights.push(`Highest variance: ${highestVar[0]} (${(highestVar[1].variance || 0).toFixed(2)})`)
            if (rows.length > 0) insights.push(`Processed ${rows.length} records.`)
            return insights.map((t, i) => <li key={i}>{t}</li>)
          })()}
        </ul>
      </div>

      {/* Data Quality */}
      <div className="bg-white rounded-2xl shadow-sm p-4 border border-gray-100">
        <div className="flex items-center justify-between mb-3">
          <div className="text-md font-medium text-gray-800">Data Quality</div>
          <div className="text-xs text-gray-400">Missing, duplicates, schema drift</div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-sm text-gray-700">
          <div>
            <div className="text-gray-500">Missing values</div>
            <ul className="mt-2 space-y-1">
              {Object.entries(quality.missing_values || {}).slice(0, 6).map(([k, v]) => (
                <li key={k} className="flex items-center justify-between">
                  <span className="truncate">{k}</span>
                  <span className="text-gray-500 ml-2">{v}</span>
                </li>
              ))}
              {Object.keys(quality.missing_values || {}).length === 0 && <li className="text-gray-400">None</li>}
            </ul>
          </div>

          <div>
            <div className="text-gray-500">Duplicates</div>
            <div className="mt-2 text-gray-700">Count: {quality.duplicate_rows?.count || 0}</div>
          </div>

          <div>
            <div className="text-gray-500">Schema Drift</div>
            <div className="mt-2 text-gray-700">
              <div className="text-xs">Added: {(quality.schema_drift?.added_columns || []).join(', ') || '—'}</div>
              <div className="text-xs mt-1">Removed: {(quality.schema_drift?.removed_columns || []).join(', ') || '—'}</div>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

export default HealthDashboard

