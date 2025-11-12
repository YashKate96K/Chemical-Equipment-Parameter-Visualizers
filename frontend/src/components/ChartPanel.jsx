import React from 'react'

function ChartPanel({ summary }){
  if(!summary) return (
    <div className="bg-white/60 backdrop-blur p-4 rounded-xl shadow border">
      <h2 className="font-medium mb-2">Charts</h2>
      <p className="text-sm text-gray-500">Upload a CSV to see charts</p>
    </div>
  )

  const labels = Object.keys(summary.averages || {})
  const values = labels.map(k => summary.averages[k])
  // Average bar chart removed per request

  return (
    <div className="bg-white/60 backdrop-blur p-4 rounded-xl shadow border space-y-4">
      <div className="flex items-center justify-between">
        <h2 className="font-medium">Quick Summary</h2>
        <span className="text-xs text-gray-500">Stats ignore missing values</span>
      </div>

      {/* Stats table: average, median, min, max for all numeric columns */}
      <div className="overflow-auto">
        <table className="min-w-full text-sm">
          <thead className="bg-gray-100 sticky top-0 z-10">
            <tr>
              <th className="px-2 py-1 text-left">Parameter</th>
              <th className="px-2 py-1 text-left">Average</th>
              <th className="px-2 py-1 text-left">Median</th>
              <th className="px-2 py-1 text-left">Min</th>
              <th className="px-2 py-1 text-left">Max</th>
            </tr>
          </thead>
          <tbody className="divide-y">
            {labels.map((name, idx) => (
              <tr key={name} className={idx % 2 === 0 ? 'bg-white/40' : ''}>
                <td className="px-2 py-1">{name}</td>
                <td className="px-2 py-1">{typeof summary.averages?.[name]==='number' ? summary.averages[name].toFixed(2) : '—'}</td>
                <td className="px-2 py-1">{typeof summary.median?.[name]==='number' ? summary.median[name].toFixed(2) : '—'}</td>
                <td className="px-2 py-1">{typeof summary.min?.[name]==='number' ? summary.min[name].toFixed(2) : '—'}</td>
                <td className="px-2 py-1">{typeof summary.max?.[name]==='number' ? summary.max[name].toFixed(2) : '—'}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}
export default ChartPanel

