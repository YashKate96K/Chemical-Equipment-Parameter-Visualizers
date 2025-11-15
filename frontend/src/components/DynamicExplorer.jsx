// File: DynamicExplorer.jsx
import React, { useEffect, useMemo, useState } from 'react'
import {
  ResponsiveContainer,
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend,
  PieChart, Pie, Cell,
  ScatterChart, Scatter,
} from 'recharts'

// ----------------------------------------------------------------------
// ALL HELPER FUNCTIONS
// ----------------------------------------------------------------------

// --- Data Analysis Utils ---
function getNumericColumns(rows) {
  if (!rows || rows.length === 0) return []
  const firstRow = rows[0]
  if (!firstRow) return []
  const idLike = new Set(['id', 'ID', 'Id', 'index', 'Index', 'Row', 'row'])
  return Object.keys(firstRow)
    .filter(key => typeof firstRow[key] === 'number')
    .filter(key => !idLike.has(key))
}

function uniqueValues(rows, col) {
  if (!rows) return []
  const set = new Set()
  for (const row of rows) set.add(row[col])
  return Array.from(set)
}

function getCategoricalColumns(rows, maxCardinality = 50, numericCols = []) {
  if (!rows || rows.length === 0) return []
  const firstRow = rows[0]
  if (!firstRow) return []
  const numericSet = new Set(numericCols)
  const allCols = Object.keys(firstRow)
  const potentialCols = allCols.filter(c => !numericSet.has(c) && (typeof firstRow[c] === 'string' || typeof firstRow[c] === 'boolean'))
  return potentialCols.filter(col => {
    const u = uniqueValues(rows, col)
    return u.length > 0 && u.length <= maxCardinality
  })
}

function applyFilters(rows, filters) {
  if (!rows || !filters || Object.keys(filters).length === 0) return rows
  return rows.filter(row => {
    return Object.keys(filters).every(col => {
      const f = filters[col]
      if (!f) return true
      const val = row[col]
      if (f.type === 'category') {
        return f.selected.length === 0 || f.selected.includes(val)
      }
      if (f.type === 'range') {
        const numVal = Number(val)
        if (typeof numVal !== 'number' || isNaN(numVal)) return true
        return numVal >= f.min && numVal <= f.max
      }
      return true
    })
  })
}

function computeQuartiles(vals) {
  const v = vals.filter(n => typeof n === 'number' && isFinite(n)).slice().sort((a, b) => a - b)
  const n = v.length
  if (!n) return { min: 0, q1: 0, q2: 0, q3: 0, max: 0 }
  const q = p => {
    const pos = (n - 1) * p
    const base = Math.floor(pos)
    const rest = pos - base
    if (v[base + 1] === undefined) return v[base]
    return v[base] + (v[base + 1] - v[base]) * (isNaN(rest) ? 0 : rest)
  }
  return { min: v[0], q1: q(0.25), q2: q(0.5), q3: q(0.75), max: v[n - 1] }
}

function computeSummaryStats(rows, numericCols) {
  if (!rows || rows.length === 0) return {}
  const stats = {}
  for (const col of numericCols) {
    const total = rows.length
    const vals = rows.map(r => r[col]).filter(v => typeof v === 'number' && isFinite(v))
    const n = vals.length
    const missing = Math.max(0, total - n)
    if (n === 0) {
      stats[col] = { min: 0, max: 0, mean: 0, median: 0, std: 0, n: 0, missing, total }
      continue
    }
    const q = computeQuartiles(vals)
    const sum = vals.reduce((a, b) => a + b, 0)
    const mean = sum / n
    const std = n < 2 ? 0 : Math.sqrt(
      vals.map(x => Math.pow(x - mean, 2)).reduce((a, b) => a + b, 0) / (n - 1)
    )
    stats[col] = { min: q.min, max: q.max, mean, median: q.q2, std, n, missing, total }
  }
  return stats
}

function pearsonCorrelation(x, y) {
  const n = Math.min(x.length, y.length)
  if (n === 0) return 0
  let sumX = 0, sumY = 0, sumXY = 0, sumX2 = 0, sumY2 = 0
  let validN = 0
  for (let i = 0; i < n; i++) {
    const xVal = x[i], yVal = y[i]
    if (typeof xVal === 'number' && isFinite(xVal) && typeof yVal === 'number' && isFinite(yVal)) {
      sumX += xVal; sumY += yVal; sumXY += xVal * yVal; sumX2 += xVal * xVal; sumY2 += yVal * yVal; validN++
    }
  }
  if (validN === 0) return 0
  const num = (validN * sumXY) - (sumX * sumY)
  const den = Math.sqrt(((validN * sumX2) - (sumX * sumX)) * ((validN * sumY2) - (sumY * sumY)))
  if (den === 0) return 0
  return num / den
}

function computeCorrelationMatrix(rows, numericCols) {
  if (!rows || rows.length === 0 || !numericCols || numericCols.length < 2) return { order: [], matrix: [] }
  const matrix = Array.from({ length: numericCols.length }, () => Array(numericCols.length).fill(0))
  const colData = numericCols.map(col => rows.map(r => r[col]))
  for (let i = 0; i < numericCols.length; i++) {
    for (let j = i; j < numericCols.length; j++) {
      if (i === j) matrix[i][j] = 1.0
      else {
        const corr = pearsonCorrelation(colData[i], colData[j])
        matrix[i][j] = corr; matrix[j][i] = corr
      }
    }
  }
  return { order: numericCols, matrix }
}

function detectOutliers(rows, numericCols) {
  if (!rows || rows.length === 0) return []
  const outliers = []
  for (const col of numericCols) {
    const vals = rows.map(r => r[col]).filter(v => typeof v === 'number' && isFinite(v))
    if (vals.length < 4) continue
    const q = computeQuartiles(vals)
    const iqr = q.q3 - q.q1
    if (iqr === 0) continue
    const lowerBound = q.q1 - 1.5 * iqr
    const upperBound = q.q3 + 1.5 * iqr
    for (const row of rows) {
      const val = row[col]
      if (typeof val === 'number' && (val < lowerBound || val > upperBound)) {
        outliers.push({ ...row, column: col, value: val })
      }
    }
  }
  return outliers
}

// kmeans
function kmeans(points, k, maxIter = 100) {
  if (!points || points.length === 0 || k < 1) return { labels: [], centers: [] }
  const randIdx = Array.from({ length: points.length }, (_, i) => i)
  for (let i = randIdx.length - 1; i > 0; i--) { const j = Math.floor(Math.random() * (i + 1)); [randIdx[i], randIdx[j]] = [randIdx[j], randIdx[i]] }
  let centers = randIdx.slice(0, Math.min(k, points.length)).map(i => ({ ...points[i] }))
  let labels = new Array(points.length).fill(0)
  const dist = (a, b) => { const dx = a.x - b.x; const dy = a.y - b.y; return dx * dx + dy * dy }
  for (let iter = 0; iter < maxIter; iter++) {
    let changed = false
    for (let i = 0; i < points.length; i++) {
      let best = 0, bestD = Infinity
      for (let c = 0; c < centers.length; c++) {
        const d = dist(points[i], centers[c])
        if (d < bestD) { bestD = d; best = c }
      }
      if (labels[i] !== best) { labels[i] = best; changed = true }
    }
    const sums = Array.from({ length: centers.length }, () => ({ x: 0, y: 0, n: 0 }))
    for (let i = 0; i < points.length; i++) {
      const c = labels[i]
      sums[c].x += points[i].x; sums[c].y += points[i].y; sums[c].n += 1
    }
    const newCenters = centers.map((c, i) => sums[i].n ? ({ x: sums[i].x / sums[i].n, y: sums[i].y / sums[i].n }) : c)
    const centerShift = centers.reduce((s, c, i) => s + Math.hypot(c.x - newCenters[i].x, c.y - newCenters[i].y), 0)
    centers = newCenters
    if (!changed || centerShift < 1e-9) break
  }
  return { labels, centers }
}

// --- Helper Components ---
const COLORS = ['#3b82f6', '#10b981', '#f59e0b', '#ef4444', '#a855f7', '#22c55e', '#06b6d4']

const ICONS = {
  clipboard: "M9 2a2 2 0 00-2 2v8a2 2 0 002 2h2a2 2 0 002-2V4a2 2 0 00-2-2H9zM4.5 5.5a.5.5 0 000 1h10a.5.5 0 000-1H4.5zM4.5 8.5a.5.5 0 000 1h10a.5.5 0 000-1H4.5zM4.5 11.5a.5.5 0 000 1h7a.5.5 0 000-1h-7z",
  stats: "M3 13.125C3 12.504 3.504 12 4.125 12h1.75C6.496 12 7 12.504 7 13.125V17C7 17.597 6.496 18.125 5.875 18.125h-1.75C3.504 18.125 3 17.597 3 17v-3.875zM13 3C13 2.403 13.504 1.875 14.125 1.875h1.75C16.496 1.875 17 2.403 17 3v14c0 .597-.504 1.125-1.125 1.125h-1.75C13.504 18.125 13 17.597 13 17V3zM8 8.125C8 7.504 8.504 7 9.125 7h1.75C11.496 7 12 7.504 12 8.125V17c0 .597-.504 1.125-1.125 1.125h-1.75C8.504 18.125 8 17.597 8 17V8.125z",
  insights: "M10 2a.75.75 0 01.75.75v1.5a.75.75 0 01-1.5 0v-1.5A.75.75 0 0110 2zM10 15a.75.75 0 01.75.75v1.5a.75.75 0 01-1.5 0v-1.5A.75.75 0 0110 15zM10 7a3 3 0 100 6 3 3 0 000-6zM15.657 5.404a.75.75 0 10-1.06-1.06l-1.061 1.06a.75.75 0 001.06 1.06l1.06-1.06zM4.343 14.596a.75.75 0 10-1.06-1.06l-1.06 1.06a.75.75 0 101.06 1.06l1.06-1.06zM14.596 15.657a.75.75 0 101.06-1.06l-1.06-1.061a.75.75 0 10-1.06 1.06l1.06 1.061zM5.404 4.343a.75.75 0 10-1.06 1.06l1.06 1.061a.75.75 0 001.06-1.06L5.404 4.343zM2.25 10a.75.75 0 01.75-.75h1.5a.75.75 0 010 1.5h-1.5a.75.75 0 01-.75-.75zM17.75 10a.75.75 0 01.75-.75h1.5a.75.75 0 010 1.5h-1.5a.75.75 0 01-.75-.75z",
  pie: "M10 18a8 8 0 100-16 8 8 0 000 16zM10 2.25a.75.75 0 01.75.75v6.5a.75.75 0 01-1.5 0v-6.5a.75.75 0 01.75-.75zM10 10a.75.75 0 01.75.75v6.5a.75.75 0 01-1.5 0v-6.5a.75.75 0 01.75-.75zM15.898 11.034a.75.75 0 01.102 1.054l-5.25 6.5a.75.75 0 01-1.156-.938l5.25-6.5a.75.75 0 011.054-.116z",
  kmeans: "M11.07 2.22c.16-.14.36-.22.58-.22h2.7a.75.75 0 01.75.75v2.7c0 .22-.08.42-.22.58l-6.25 6.25a.75.75 0 01-1.06 0l-2.7-2.7a.75.75 0 010-1.06l6.25-6.25zM12.5 5a1.5 1.5 0 100-3 1.5 1.5 0 000 3zM3.52 7.22c-.16-.14-.36-.22-.58-.22H.24a.75.75 0 00-.75.75v2.7c0 .22.08.42.22.58l6.25 6.25a.75.75 0 001.06 0l2.7-2.7a.75.75 0 000-1.06L3.52 7.22z",
  table: "M3.375 3C2.339 3 1.5 3.84 1.5 4.875v10.25C1.5 16.16 2.339 17 3.375 17h13.25c1.036 0 1.875-.84 1.875-1.875V4.875C18.5 3.84 17.661 3 16.625 3H3.375zM3 4.875a.375.375 0 01.375-.375h13.25a.375.375 0 01.375.375v3.375H3V4.875zM3 9.75h14v5.375a.375.375 0 01-.375.375H3.375a.375.375 0 01-.375-.375V9.75z",
}

function Icon({ path, className = "w-5 h-5" }) {
  return (
    <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor" className={className}>
      <path fillRule="evenodd" d={path} clipRule="evenodd" />
    </svg>
  )
}

function Section({ title, subtitle, icon, children, className = "" }) {
  return (
    <div className={`bg-white rounded-lg shadow-md p-6 ${className}`}>
      <div className="flex items-center justify-between mb-4 border-b border-gray-200 pb-3">
        <div className="flex items-center gap-2">
          {icon && <span className="text-gray-500">{icon}</span>}
          <h3 className="text-xl font-semibold text-gray-800">{title}</h3>
        </div>
        {subtitle && <div className="text-sm text-gray-500">{subtitle}</div>}
      </div>
      {children}
    </div>
  )
}

const CustomTooltip = ({ active, payload, label }) => {
  if (active && payload && payload.length) {
    return (
      <div className="bg-white/90 backdrop-blur-sm rounded-md shadow-lg border border-gray-200 p-3">
        <p className="font-semibold text-gray-800">{label}</p>
        {payload.map((p, i) => (
          <p key={i} className="text-sm" style={{ color: p.color }}>
            {`${p.name}: `}
            <span className="font-medium">{typeof p.value === 'number' ? p.value.toFixed(2) : p.value}</span>
          </p>
        ))}
      </div>
    )
  }
  return null
}

function InsightsList({ rows, numericCols, categoricalCols, stats, corr, outliers }) {
  const items = []

  // Helpers
  const safeVals = (col) => rows.map(r => r[col]).filter(v => typeof v === 'number' && isFinite(v))
  const skewness = (vals) => {
    const n = vals.length; if (n < 3) return 0
    const mean = vals.reduce((a, b) => a + b, 0) / n
    const s2 = vals.reduce((a, x) => a + Math.pow(x - mean, 2), 0) / (n - 1)
    const s = Math.sqrt(s2 || 0)
    if (!isFinite(s) || s === 0) return 0
    const m3 = vals.reduce((a, x) => a + Math.pow(x - mean, 3), 0) / n
    return (Math.sqrt(n * (n - 1)) / (n - 2)) * (m3 / Math.pow(s, 3))
  }

  // 1) Variability and central tendency
  const withStd = numericCols.map(c => ({ c, s: stats[c] })).filter(x => x.s)
  if (withStd.length) {
    const maxVar = [...withStd].sort((a, b) => (b.s.std || 0) - (a.s.std || 0))[0]
    const maxMean = [...withStd].sort((a, b) => (b.s.mean || 0) - (a.s.mean || 0))[0]
    if (maxVar && (maxVar.s.std || 0) > 0) items.push(`Highest variability: ${maxVar.c} (std = ${maxVar.s.std.toFixed(2)})`)
    if (maxMean && (maxMean.s.mean || 0) !== 0) items.push(`Largest mean value: ${maxMean.c} (mean = ${maxMean.s.mean.toFixed(2)})`)

    // Coefficient of variation
    const cvList = withStd
      .filter(x => Math.abs(x.s.mean) > 1e-9)
      .map(x => ({ c: x.c, cv: Math.abs(x.s.std / x.s.mean) }))
    if (cvList.length) {
      const highestCV = [...cvList].sort((a, b) => b.cv - a.cv)[0]
      const lowestCV = [...cvList].sort((a, b) => a.cv - b.cv)[0]
      if (highestCV) items.push(`Most volatile by CV: ${highestCV.c} (CV = ${highestCV.cv.toFixed(2)})`)
      if (lowestCV) items.push(`Most stable by CV: ${lowestCV.c} (CV = ${lowestCV.cv.toFixed(2)})`)
    }
  }

  // 2) Skewness (shape)
  const skewList = numericCols.map(c => ({ c, skew: skewness(safeVals(c)) }))
  if (skewList.length) {
    const topSkew = [...skewList].sort((a, b) => Math.abs(b.skew) - Math.abs(a.skew))[0]
    if (topSkew && Math.abs(topSkew.skew) > 0.5) items.push(`Most skewed: ${topSkew.c} (skew = ${topSkew.skew.toFixed(2)})`)
  }

  // 3) Strongest correlations (top + and top -)
  if (corr.order.length > 1) {
    let bestPos = { i: 0, j: 1, r: corr.matrix[0][1] }
    let bestNeg = { i: 0, j: 1, r: corr.matrix[0][1] }
    for (let i = 0; i < corr.order.length; i++) {
      for (let j = i + 1; j < corr.order.length; j++) {
        const r = corr.matrix[i][j]
        if (typeof r === 'number') {
          if (r > (bestPos.r ?? -Infinity)) bestPos = { i, j, r }
          if (r < (bestNeg.r ?? Infinity)) bestNeg = { i, j, r }
        }
      }
    }
    if (isFinite(bestPos.r) && bestPos.r > 0) items.push(`Top positive correlation: ${corr.order[bestPos.i]} vs ${corr.order[bestPos.j]} (r=${bestPos.r.toFixed(2)})`)
    if (isFinite(bestNeg.r) && bestNeg.r < 0) items.push(`Top negative correlation: ${corr.order[bestNeg.i]} vs ${corr.order[bestNeg.j]} (r=${bestNeg.r.toFixed(2)})`)
  }

  // 4) Dominant category (highest share across categoricals)
  let dominant = null
  categoricalCols.forEach(col => {
    const counts = new Map()
    rows.forEach(r => { const k = String(r[col]); counts.set(k, (counts.get(k) || 0) + 1) })
    const total = rows.length || 1
    const top = Array.from(counts.entries()).map(([k, v]) => ({ k, p: v / total })).sort((a, b) => b.p - a.p)[0]
    if (top && (!dominant || top.p > dominant.p)) dominant = { col, ...top }
  })
  if (dominant && dominant.p >= 0.5) items.push(`Dominant category: ${dominant.col} = ${dominant.k} (${(dominant.p * 100).toFixed(0)}%)`)

  // 5) Outlier-heavy columns
  if (outliers.length) {
    const byCol = new Map()
    outliers.forEach(o => byCol.set(o.column, (byCol.get(o.column) || 0) + 1))
    const top = Array.from(byCol.entries()).sort((a, b) => b[1] - a[1])[0]
    if (top) {
      const pct = (top[1] / Math.max(1, rows.length)) * 100
      items.push(`Outlier-heavy: ${top[0]} (${top[1]} points, ${pct.toFixed(1)}% of rows)`)  
    }
  }

  // 6) Near-constant metrics (very low variability or few unique values)
  const nearConst = numericCols.filter(c => {
    const v = safeVals(c)
    const u = new Set(v).size
    const s = stats[c]
    const cv = s && Math.abs(s.mean) > 1e-9 ? Math.abs(s.std / s.mean) : 0
    return u <= 2 || cv < 0.01
  })
  if (nearConst.length) items.push(`Near-constant metrics: ${nearConst.slice(0, 3).join(', ')}${nearConst.length > 3 ? ` +${nearConst.length - 3} more` : ''}`)

  // 7) Group mean gaps (first categorical)
  if (categoricalCols.length && numericCols.length) {
    const cat = categoricalCols[0]
    const groups = {}
    rows.forEach(r => {
      const k = String(r[cat])
      groups[k] = groups[k] || {}
      numericCols.forEach(n => {
        const v = r[n]
        if (typeof v === 'number') {
          const g = groups[k][n] || { sum: 0, count: 0 }
          g.sum += v; g.count += 1; groups[k][n] = g
        }
      })
    })
    const keys = Object.keys(groups)
    if (keys.length > 1) {
      let top = { n: null, range: -Infinity }
      numericCols.forEach(n => {
        const means = keys.map(k => (groups[k][n]?.sum || 0) / (groups[k][n]?.count || 1))
        const range = Math.max(...means) - Math.min(...means)
        if (range > top.range) top = { n, range }
      })
      if (top.n && top.range > 0) items.push(`Largest group gap on ${top.n} (range of means = ${top.range.toFixed(2)})`)
    }
  }

  if (items.length === 0) return <div className="text-sm text-gray-600">No significant insights detected.</div>
  return (
    <ul className="list-disc ml-5 text-sm text-gray-800 space-y-1.5">
      {items.map((t, i) => <li key={i}>{t}</li>)}
    </ul>
  )
}

function PieLegend({ data }) {
  if (!data || data.length === 0) return null
  return (
    <div className="mt-4 max-h-28 overflow-y-auto">
      <div className="grid grid-cols-2 gap-x-4 gap-y-1 text-xs">
        {data.map((d, i) => (
          <div key={i} className="flex items-center gap-2 min-w-0">
            <span className="flex-shrink-0 inline-block w-3 h-3 rounded" style={{ backgroundColor: COLORS[i % COLORS.length] }} />
            <span className="truncate" title={`${d.name}: ${d.value}`}>{d.name}</span>
            <span className="ml-auto text-gray-500 font-medium">{d.value}</span>
          </div>
        ))}
      </div>
    </div>
  )
}

function KMeansScatter({ rows, numericCols }) {
  const [xKey, setXKey] = useState(numericCols[0] || null)
  const [yKey, setYKey] = useState(numericCols[1] || numericCols[0] || null)
  const [k, setK] = useState(3)

  useEffect(() => {
    if (!numericCols.includes(xKey)) setXKey(numericCols[0] || null)
    if (!numericCols.includes(yKey)) setYKey(numericCols[1] || numericCols[0] || null)
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [numericCols])

  const points = useMemo(() =>
    rows
      .map(r => ({ x: Number(r[xKey]), y: Number(r[yKey]) }))
      .filter(p => Number.isFinite(p.x) && Number.isFinite(p.y)),
    [rows, xKey, yKey]
  )

  const { labels, centers } = useMemo(() => kmeans(points, Math.max(2, Math.min(6, k))), [points, k])
  const clustered = useMemo(() => points.map((p, i) => ({ ...p, cluster: labels[i] ?? 0 })), [points, labels])

  if (points.length === 0) return <div className="text-sm text-gray-600">Not enough numeric data for clustering.</div>

  const formInput = "border-gray-300 rounded-md shadow-sm p-1.5 text-sm focus:border-blue-500 focus:ring-blue-500"

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap gap-4 items-center text-sm">
        <label className="flex items-center gap-2 font-medium">X-Axis
          <select className={formInput} value={xKey} onChange={e => setXKey(e.target.value)}>
            {numericCols.map(c => <option key={c} value={c}>{c}</option>)}
          </select>
        </label>
        <label className="flex items-center gap-2 font-medium">Y-Axis
          <select className={formInput} value={yKey} onChange={e => setYKey(e.target.value)}>
            {numericCols.map(c => <option key={c} value={c}>{c}</option>)}
          </select>
        </label>
        <label className="flex items-center gap-2 font-medium">Clusters (k)
          <input className={`${formInput} w-16`} type="number" min={2} max={6} value={k} onChange={e => setK(Number(e.target.value))} />
        </label>
      </div>

      <div className="w-full h-80">
        <ResponsiveContainer>
          <ScatterChart>
            <CartesianGrid />
            <XAxis dataKey="x" name={xKey} type="number" />
            <YAxis dataKey="y" name={yKey} type="number" />
            <Tooltip content={<CustomTooltip />} />
            <Legend />
            {Array.from(new Set(clustered.map(p => p.cluster))).map((cid) => (
              <Scatter key={cid} name={`Cluster ${cid + 1}`} data={clustered.filter(p => p.cluster === cid)} fill={COLORS[cid % COLORS.length]} isAnimationActive={true} />
            ))}
            <Scatter
              name="Centers"
              data={centers.map(c => ({ x: c.x, y: c.y }))}
              fill="#a855f7"
              stroke="#fff"
              strokeWidth={2}
              shape="star"
              size={150}
              opacity={0.8}
            />
          </ScatterChart>
        </ResponsiveContainer>
      </div>
    </div>
  )
}

function BoxPlotSVG({ stats, width = 600, height = 60 }) {
  const pad = 40
  const span = Math.max(1e-6, stats.max - stats.min)
  const sx = (v) => pad + (width - pad * 2) * ((v - stats.min) / span)
  const cy = height / 2
  const boxTop = cy - 12
  const boxBottom = cy + 12
  const q1x = sx(stats.q1)
  const q2x = sx(stats.q2)
  const q3x = sx(stats.q3)
  const minx = sx(stats.min)
  const maxx = sx(stats.max)

  return (
    <svg viewBox={`0 0 ${width} ${height}`} className="w-full h-full">
      <line x1={minx} x2={maxx} y1={cy} y2={cy} stroke="#0ea5e9" strokeWidth="2" />
      <line x1={minx} x2={minx} y1={cy - 6} y2={cy + 6} stroke="#0ea5e9" />
      <line x1={maxx} x2={maxx} y1={cy - 6} y2={cy + 6} stroke="#0ea5e9" />
      <rect x={q1x} y={boxTop} width={Math.max(1, q3x - q1x)} height={boxBottom - boxTop} fill="rgba(14,165,233,0.25)" stroke="#0ea5e9" />
      <line x1={q2x} x2={q2x} y1={boxTop} y2={boxBottom} stroke="#0ea5e9" strokeWidth="2" />
    </svg>
  )
}

// ----------------------------------------------------------------------
// MAIN COMPONENT
// ----------------------------------------------------------------------

export default function DynamicExplorer({ rows: initialRows }) {
  const [rows] = useState(initialRows || [])
  const [filters, setFilters] = useState({})
  const [query, setQuery] = useState('')
  const [page, setPage] = useState(1)
  const [perPage, setPerPage] = useState(10)
  const [hiddenCols, setHiddenCols] = useState(new Set())

  const numericCols = useMemo(() => getNumericColumns(rows), [rows])
  const categoricalCols = useMemo(() => getCategoricalColumns(rows, 50, numericCols), [rows, numericCols])
  const allCols = useMemo(() => (rows.length > 0 ? Object.keys(rows[0]) : []), [rows])

  useEffect(() => {
    const f = {}
    categoricalCols.forEach(c => f[c] = { type: 'category', selected: [] })
    numericCols.forEach(c => {
      const vals = rows.map(r => r[c]).filter(v => typeof v === 'number' && isFinite(v))
      const min = Math.min(...vals)
      const max = Math.max(...vals)
      f[c] = {
        type: 'range',
        min: isFinite(min) ? min : 0,
        max: isFinite(max) ? max : 0,
        origMin: isFinite(min) ? min : 0,
        origMax: isFinite(max) ? max : 0
      }
    })
    setFilters(f)
  }, [rows, numericCols, categoricalCols])

  const filteredRows = useMemo(() => applyFilters(rows, filters), [rows, filters])
  const stats = useMemo(() => computeSummaryStats(filteredRows, numericCols), [filteredRows, numericCols])
  const corr = useMemo(() => computeCorrelationMatrix(filteredRows, numericCols), [filteredRows, numericCols])
  const outliers = useMemo(() => detectOutliers(filteredRows, numericCols), [filteredRows, numericCols])
  const outliersByCol = useMemo(() => {
    const m = new Map()
    outliers.forEach(o => { const a = m.get(o.column) || []; a.push(o); m.set(o.column, a) })
    return m
  }, [outliers])

  const barByCategory = (numCol, catCol) => {
    const groups = new Map()
    filteredRows.forEach(r => {
      const key = String(r[catCol])
      const v = r[numCol]
      if (typeof v === 'number') {
        const g = groups.get(key) || { key, sum: 0, count: 0 }
        g.sum += v
        g.count += 1
        groups.set(key, g)
      }
    })
    return Array.from(groups.values()).map(g => ({ category: g.key, avg: g.count ? g.sum / g.count : 0 }))
  }

  const textFilteredRows = useMemo(() => {
    if (!query) return filteredRows
    const q = query.toLowerCase()
    return filteredRows.filter(r =>
      Object.values(r).some(v => String(v).toLowerCase().includes(q))
    )
  }, [filteredRows, query])

  const totalPages = useMemo(() => Math.ceil(textFilteredRows.length / perPage), [textFilteredRows, perPage])
  const paginatedRows = useMemo(() => {
    const start = (page - 1) * perPage
    return textFilteredRows.slice(start, start + perPage)
  }, [textFilteredRows, page, perPage])

  const formInputStyle = "w-full p-2 border border-gray-300 rounded-md shadow-sm focus:border-blue-500 focus:ring-blue-500"
  const buttonStyle = "px-4 py-2 bg-white border border-gray-300 rounded-md shadow-sm text-sm font-medium text-gray-700 hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
  const checkboxStyle = "rounded border-gray-300 text-blue-600 shadow-sm focus:ring-blue-500"

  if (rows.length === 0) {
    return (
      <div className="p-4 md:p-8 bg-slate-100 min-h-screen">
        <div className="bg-white rounded-lg shadow-md p-6">
          <h1 className="text-3xl font-bold text-gray-900">Dynamic Data Explorer</h1>
          <p className="text-base text-gray-600 mt-1">No data loaded.</p>
        </div>
      </div>
    )
  }

  return (
    <div className="p-4 md:p-8 bg-slate-100 min-h-screen">
      <div className="space-y-6">
        <div className="bg-white rounded-lg shadow-md p-6">
          <h1 className="text-3xl font-bold text-gray-900">Dynamic Data Explorer</h1>
          <p className="text-base text-gray-600 mt-1">Real-time automated dataset analysis</p>
        </div>

        {/* Top Row */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <Section title="Summary Stats" subtitle="Key numeric metrics" icon={<Icon path={ICONS.stats} />} className="lg:col-span-2">
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {numericCols.length > 0 ? numericCols.map(col => {
                const s = stats[col]
                if (!s) return <div key={col} className="text-sm text-gray-500">No stats for {col}</div>
                return (
                  <div key={col} className="bg-slate-50 rounded-lg p-4 border border-slate-200">
                    <div className="text-sm font-semibold text-gray-800 mb-2">{col}</div>
                    <div className="grid grid-cols-2 text-sm gap-y-1">
                      <div><div className="text-gray-500">Mean</div><b className="text-gray-800">{s.mean.toFixed(2)}</b></div>
                      <div><div className="text-gray-500">Median</div><b className="text-gray-800">{s.median.toFixed(2)}</b></div>
                      <div><div className="text-gray-500">Min</div><b className="text-gray-800">{s.min.toFixed(2)}</b></div>
                      <div><div className="text-gray-500">Max</div><b className="text-gray-800">{s.max.toFixed(2)}</b></div>
                      <div><div className="text-gray-500">Std</div><b className="text-gray-800">{s.std.toFixed(2)}</b></div>
                      <div><div className="text-gray-500">N</div><b className="text-gray-800">{s.n}</b></div>
                      <div><div className="text-gray-500">Missing</div><b className="text-gray-800">{s.missing}</b></div>
                    </div>
                  </div>
                )
              }) : <div className="text-sm text-gray-500">No numeric columns found.</div>}
            </div>
          </Section>

          <Section title="Insights" subtitle="Auto-generated observations" icon={<Icon path={ICONS.insights} />} className="lg:col-span-1">
            <InsightsList rows={filteredRows} numericCols={numericCols} categoricalCols={categoricalCols} stats={stats} corr={corr} outliers={outliers} />
          </Section>
        </div>

        {/* Dynamic Chart Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-6">

          {/* Bar charts */}
          {categoricalCols.length > 0 && numericCols.map(num => (
            <Section key={num} title={`Average ${num}`} subtitle={`by ${categoricalCols[0]}`} icon={<Icon path={ICONS.stats} />}>
              <div className="w-full h-72">
                <ResponsiveContainer>
                  <BarChart data={barByCategory(num, categoricalCols[0])}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="category" fontSize={12} />
                    <YAxis fontSize={12} />
                    <Tooltip content={<CustomTooltip />} />
                    <Legend />
                    <Bar dataKey="avg" fill={COLORS[0]} isAnimationActive={true} />
                  </BarChart>
                </ResponsiveContainer>
              </div>
            </Section>
          ))}

          {/* Pie charts */}
          {categoricalCols.map(cat => {
            const counts = new Map()
            filteredRows.forEach(r => {
              const k = String(r[cat])
              counts.set(k, (counts.get(k) || 0) + 1)
            })
            let data = Array.from(counts.entries()).map(([name, value]) => ({ name, value }))
            data.sort((a, b) => b.value - a.value)
            const top = data.slice(0, 8)
            const other = data.slice(8).reduce((a, b) => a + b.value, 0)
            if (other > 0) top.push({ name: 'Other', value: other })
            data = top
            return (
              <Section key={cat} title={`${cat} Distribution`} icon={<Icon path={ICONS.pie} />}>
                <div className="w-full h-72">
                  <ResponsiveContainer>
                    <PieChart>
                      <Pie data={data} dataKey="value" nameKey="name" innerRadius={50} outerRadius={100} label={false} labelLine={false} isAnimationActive={true}>
                        {data.map((e, i) => (<Cell key={i} fill={COLORS[i % COLORS.length]} />))}
                      </Pie>
                      <Tooltip content={<CustomTooltip />} />
                    </PieChart>
                  </ResponsiveContainer>
                </div>
                <PieLegend data={data} />
              </Section>
            )
          })}

          {/* KMeans */}
          {numericCols.length >= 2 && (
            <Section title="K-Means Clustering" subtitle="Find groups in your data" icon={<Icon path={ICONS.kmeans} />} className="md:col-span-2">
              <KMeansScatter rows={filteredRows} numericCols={numericCols} />
            </Section>
          )}

          {/* Correlation */}
          {corr.order.length > 1 && (
            <Section title="Relationships" subtitle="Correlation and outliers" icon={<Icon path={ICONS.insights} />} className="md:col-span-2 xl:col-span-3">
              <div className="space-y-6">
                <div>
                  <div className="text-base font-semibold mb-2">Correlation Heatmap</div>
                  <div className="overflow-auto border rounded-lg w-full">
                    <table className="w-full text-sm border-collapse table-auto">
                      <thead className="bg-gray-50">
                        <tr>
                          <th className="p-2 border text-xs">Var</th>
                          {corr.order.map(h => (<th key={h} className="p-2 border text-xs whitespace-nowrap">{h}</th>))}
                        </tr>
                      </thead>
                      <tbody>
                        {corr.matrix.map((row, i) => (
                          <tr key={i} className="odd:bg-white even:bg-slate-50">
                            <td className="p-2 border font-semibold text-xs whitespace-nowrap">{corr.order[i]}</td>
                            {row.map((v, j) => {
                              const val = typeof v === 'number' ? v : 0
                              const intensity = Math.min(1, Math.abs(val))
                              const color = val > 0 ? `rgba(59, 130, 246, ${intensity * 0.8})` : `rgba(239, 68, 68, ${intensity * 0.8})`
                              const textColor = intensity > 0.7 ? 'white' : 'black'
                              return (
                                <td key={j} className="p-2 border text-center" style={{ backgroundColor: i === j ? '#f3f4f6' : color, color: i === j ? 'black' : textColor, minWidth: 60 }}>
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
              </div>
            </Section>
          )}
        </div>

        {/* Boxplots */}
        {numericCols.length > 0 && (
          <Section title="Data Distribution" subtitle="Boxplots for numeric columns" icon={<Icon path={ICONS.stats} />}>
            <div className="space-y-4">
              {numericCols.map(col => {
                const vals = filteredRows.map(r => r[col]).filter(v => typeof v === 'number')
                if (vals.length === 0) return null
                const q = computeQuartiles(vals)
                return (
                  <div key={col} className="bg-white rounded-lg p-4 border border-gray-200">
                    <div className="text-sm font-medium mb-2">{col} Boxplot</div>
                    <BoxPlotSVG stats={q} />
                    <div className="flex justify-between text-xs text-gray-600 px-10 -mt-2">
                      <span>Min: {q.min.toFixed(2)}</span>
                      <span>Q1: {q.q1.toFixed(2)}</span>
                      <span>Q2: {q.q2.toFixed(2)}</span>
                      <span>Q3: {q.q3.toFixed(2)}</span>
                      <span>Max: {q.max.toFixed(2)}</span>
                    </div>
                  </div>
                )
              })}
            </div>
          </Section>
        )}

        {/* Outliers by Metric */}
        <Section title="Outliers by Metric" subtitle="IQR rule per numeric column" icon={<Icon path={ICONS.insights} />}>
          <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
            {numericCols.map(col=>{
              const arr = outliersByCol.get(col) || []
              const vals = filteredRows.map(r=> r[col]).filter(v=> typeof v==='number' && isFinite(v))
              const q = computeQuartiles(vals)
              const lb = q.q1 - 1.5*(q.q3-q.q1)
              const ub = q.q3 + 1.5*(q.q3-q.q1)
              const top = arr.slice().sort((a,b)=>{
                const da = Math.max(0, Math.min(Math.abs(a.value-lb), Math.abs(a.value-ub)))
                const db = Math.max(0, Math.min(Math.abs(b.value-lb), Math.abs(b.value-ub)))
                return db-da
              }).slice(0,8)
              return (
                <div key={col} className="bg-white rounded-lg border p-4">
                  <div className="flex items-center justify-between mb-2">
                    <div className="text-sm font-semibold">{col}</div>
                    <span className="text-xs px-2 py-0.5 rounded-full bg-red-50 text-red-600 border border-red-200">{arr.length} outliers</span>
                  </div>
                  <div className="text-xs text-gray-600 mb-2">Bounds: [{lb.toFixed(2)}, {ub.toFixed(2)}]</div>
                  {arr.length===0 ? (
                    <div className="text-xs text-gray-500">None detected</div>
                  ) : (
                    <ul className="text-sm space-y-1 max-h-32 overflow-y-auto">
                      {top.map((o,i)=> (
                        <li key={i} className="flex items-center justify-between">
                          <span className="truncate">Value</span>
                          <b className="ml-2">{Number(o.value).toFixed(2)}</b>
                        </li>
                      ))}
                    </ul>
                  )}
                </div>
              )
            })}
          </div>
        </Section>

        {/* Data Table */}
        <Section title="Dataset Table" subtitle={`Showing ${paginatedRows.length} of ${textFilteredRows.length} rows`} icon={<Icon path={ICONS.table} />}>
          <div className="space-y-4">
            <input className={formInputStyle} placeholder="Search all columns..." value={query} onChange={e => { setQuery(e.target.value); setPage(1) }} />
            <div>
              <div className="text-sm font-medium mb-2">Toggle Columns:</div>
              <div className="flex flex-wrap gap-2">
                {allCols.map(col => (
                  <label key={col} className="flex items-center gap-2 text-sm bg-gray-100 hover:bg-gray-200 px-3 py-1.5 rounded-md cursor-pointer">
                    <input type="checkbox" className={checkboxStyle} checked={!hiddenCols.has(col)} onChange={() => {
                      setHiddenCols(prev => {
                        const n = new Set(prev)
                        if (n.has(col)) n.delete(col)
                        else n.add(col)
                        return n
                      })
                    }} />
                    {col}
                  </label>
                ))}
              </div>
            </div>

            <div className="overflow-x-auto border border-gray-200 rounded-lg">
              <table className="text-sm min-w-full">
                <thead className="bg-gray-100">
                  <tr>
                    {allCols.filter(c => !hiddenCols.has(c)).map(col => (
                      <th key={col} className="p-3 border-b-2 border-gray-200 text-left text-xs font-semibold text-gray-600 uppercase tracking-wider">{col}</th>
                    ))}
                  </tr>
                </thead>
                <tbody className="bg-white">
                  {paginatedRows.length > 0 ? paginatedRows.map((r, i) => (
                    <tr key={i} className="odd:bg-white even:bg-slate-50 hover:bg-slate-100">
                      {allCols.filter(c => !hiddenCols.has(c)).map(col => (
                        <td key={col} className="p-3 border-b border-gray-200 whitespace-nowrap">{String(r[col])}</td>
                      ))}
                    </tr>
                  )) : (
                    <tr>
                      <td colSpan={allCols.filter(c => !hiddenCols.has(c)).length} className="text-center p-6 text-gray-500">
                        No rows found {query ? 'matching your search' : ''}.
                      </td>
                    </tr>
                  )}
                </tbody>
              </table>
            </div>

            <div className="flex flex-wrap items-center justify-between gap-4 mt-3 text-sm">
              <div className="flex items-center gap-2">
                <button className={buttonStyle} onClick={() => setPage(p => Math.max(1, p - 1))} disabled={page === 1}>Previous</button>
                <span className="text-gray-700">Page {page} of {totalPages > 0 ? totalPages : 1}</span>
                <button className={buttonStyle} onClick={() => setPage(p => p + 1)} disabled={page === totalPages || totalPages === 0}>Next</button>
              </div>
              <div className="flex items-center gap-2">
                <span className="text-gray-700">Rows per page:</span>
                <select className="p-1.5 border-gray-300 rounded-md shadow-sm text-sm focus:border-blue-500 focus:ring-blue-500" value={perPage} onChange={e => { setPerPage(Number(e.target.value)); setPage(1) }}>
                  {[10, 20, 50, 100].map(x => (<option key={x} value={x}>{x}</option>))}
                </select>
              </div>
            </div>
          </div>
        </Section>
      </div>
    </div>
  )
}


