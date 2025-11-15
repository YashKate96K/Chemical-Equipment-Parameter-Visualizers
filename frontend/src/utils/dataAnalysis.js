// Dynamic data analysis helpers (schema-adaptive)

export function getNumericColumns(rows) {
  if (!Array.isArray(rows) || rows.length === 0) return []
  const keys = Object.keys(rows[0] || {})
  return keys.filter(k => rows.some(r => typeof r[k] === 'number'))
}

export function getCategoricalColumns(rows, maxUniques = 50, numericCols = []) {
  if (!Array.isArray(rows) || rows.length === 0) return []
  const keys = Object.keys(rows[0] || {})
  const numSet = new Set(numericCols)
  return keys.filter(k => {
    const vals = rows.map(r => r[k]).filter(v => v !== null && v !== undefined)
    if (vals.length === 0) return false

    const allNum = vals.every(v => typeof v === 'number')
    const allStrOrBool = vals.every(v => typeof v === 'string' || typeof v === 'boolean')
    const uniquesArr = Array.from(new Set(vals.map(v => String(v))))
    const uniqueCount = uniquesArr.length

    // Strings/booleans with reasonable cardinality => categorical
    if (allStrOrBool && uniqueCount > 1 && uniqueCount <= maxUniques) return true

    // Numeric columns: consider categorical only if low-cardinality integers (like encoded categories)
    if (allNum) {
      const allIntegers = vals.every(v => Number.isInteger(v))
      if (allIntegers && uniqueCount > 1 && uniqueCount <= Math.min(10, maxUniques)) return true
      return false
    }

    // Mixed primitive types: if low cardinality, treat as categorical
    return uniqueCount > 1 && uniqueCount <= Math.min(20, maxUniques)
  })
}

export function computeSummaryStats(rows, numericCols) {
  const stats = {}
  for (const col of numericCols) {
    const vals = rows.map(r => r[col]).filter(v => typeof v === 'number')
    const n = vals.length
    if (!n) { stats[col] = null; continue }
    vals.sort((a,b)=>a-b)
    const mean = vals.reduce((a,b)=>a+b,0)/n
    const median = n%2? vals[(n-1)/2] : (vals[n/2-1]+vals[n/2])/2
    const min = vals[0]
    const max = vals[n-1]
    const variance = vals.reduce((a,b)=>a+Math.pow(b-mean,2),0)/n
    const std = Math.sqrt(variance)
    stats[col] = { mean, median, min, max, std, count:n }
  }
  return stats
}

export function computeCorrelationMatrix(rows, numericCols) {
  const matrix = []
  const n = numericCols.length
  for (let i=0;i<n;i++){
    matrix[i] = []
    for (let j=0;j<n;j++){
      matrix[i][j] = pearson(rows, numericCols[i], numericCols[j])
    }
  }
  return { order: numericCols, matrix }
}

function pearson(rows, a, b){
  const ax = [], bx = []
  for(const r of rows){
    if(typeof r[a]==='number' && typeof r[b]==='number'){
      ax.push(r[a]); bx.push(r[b])
    }
  }
  const n = ax.length
  if(n<2) return 0
  const ma = ax.reduce((s,v)=>s+v,0)/n
  const mb = bx.reduce((s,v)=>s+v,0)/n
  let num=0, da=0, db=0
  for(let i=0;i<n;i++){
    const xa = ax[i]-ma
    const xb = bx[i]-mb
    num += xa*xb
    da += xa*xa
    db += xb*xb
  }
  const den = Math.sqrt(da*db)
  return den===0? 0 : num/den
}

export function detectOutliers(rows, numericCols, zThresh=3){
  const stats = computeSummaryStats(rows, numericCols)
  const outliers = []
  for(const col of numericCols){
    const s = stats[col]
    if(!s || s.std === 0) continue
    rows.forEach((r, idx)=>{
      const v = r[col]
      if(typeof v==='number'){
        const z = (v - s.mean) / s.std
        if(Math.abs(z) >= zThresh){ outliers.push({ index: idx, column: col, value: v, z }) }
      }
    })
  }
  return outliers.sort((a,b)=> Math.abs(b.z) - Math.abs(a.z))
}

export function uniqueValues(rows, col){
  return Array.from(new Set(rows.map(r => r[col]).filter(v => v!==undefined && v!==null))).slice(0,500)
}

export function applyFilters(rows, filters){
  return rows.filter(r => {
    for(const [key, f] of Object.entries(filters)){
      const v = r[key]
      if(!f) continue
      if(f.type==='category'){
        if(f.selected && f.selected.length>0 && !f.selected.includes(String(v))) return false
      }else if(f.type==='range'){
        const num = typeof v==='number'? v : Number(v)
        if(isFinite(f.min) && num < f.min) return false
        if(isFinite(f.max) && num > f.max) return false
      }
    }
    return true
  })
}
