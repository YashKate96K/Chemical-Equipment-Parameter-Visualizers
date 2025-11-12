import React from 'react'

function TablePreview({ csvText }){
  if(!csvText) return (
    <div className="bg-white/60 backdrop-blur p-4 rounded-xl shadow border">
      <h2 className="font-medium mb-2">Preview (first 10 rows)</h2>
      <p className="text-sm text-gray-500">No preview yet</p>
    </div>
  )
  const lines = csvText.trim().split(/\r?\n/)
  const headers = lines[0].split(',')
  const rows = lines.slice(1).map(l => l.split(','))
  return (
    <div className="bg-white/60 backdrop-blur p-4 rounded-xl shadow border overflow-auto">
      <div className="flex items-center justify-between mb-2">
        <h2 className="font-medium">Preview (first 10 rows)</h2>
        <span className="text-xs text-gray-500">Read-only</span>
      </div>
      <table className="min-w-full text-sm">
        <thead className="bg-gray-100 sticky top-0 z-10">
          <tr>
            {headers.map((h,i)=>(<th key={i} className="px-2 py-2 text-left font-medium">{h}</th>))}
          </tr>
        </thead>
        <tbody className="divide-y">
          {rows.map((r,ri)=>(
            <tr key={ri} className={ri % 2 === 0 ? 'bg-white/40' : ''}>
              {r.map((c,ci)=>(<td key={ci} className="px-2 py-1 whitespace-nowrap">{c}</td>))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}
export default TablePreview

