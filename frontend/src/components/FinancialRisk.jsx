import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Cell } from 'recharts'
import { TrendingUp, AlertCircle } from 'lucide-react'

const CREDIT_CONFIG = {
  NORMAL:   { color: '#22c55e', bg: 'bg-green-900/30 border-green-700' },
  ELEVATED: { color: '#eab308', bg: 'bg-yellow-900/30 border-yellow-700' },
  HIGH:     { color: '#f97316', bg: 'bg-orange-900/30 border-orange-700' },
  CRITICAL: { color: '#ef4444', bg: 'bg-red-900/30 border-red-700' },
}

export default function FinancialRisk({ incidents, summary }) {
  // Build bar chart data — exposure by attack type
  const byType = {}
  incidents.forEach(inc => {
    byType[inc.attack_type] = (byType[inc.attack_type] || 0) + inc.total_exposure_usd
  })
  const chartData = Object.entries(byType).map(([name, value]) => ({ name, value }))

  const totalExposure = summary?.total_exposure_usd || 0
  const criticalFlag  = incidents.find(i => i.credit_risk_flag === 'CRITICAL')
  const overallFlag   = criticalFlag ? 'CRITICAL'
    : incidents.find(i => i.credit_risk_flag === 'HIGH')     ? 'HIGH'
    : incidents.find(i => i.credit_risk_flag === 'ELEVATED') ? 'ELEVATED' : 'NORMAL'
  const cfg = CREDIT_CONFIG[overallFlag]

  return (
    <div className="bg-gray-900 border border-gray-800 rounded-xl p-5">
      <div className="flex items-center gap-2 mb-4">
        <TrendingUp size={16} className="text-blue-400" />
        <h3 className="font-semibold text-sm">Financial Risk Overview</h3>
      </div>

      {/* Credit risk flag */}
      <div className={`flex items-center justify-between border rounded-lg px-4 py-3 mb-4 ${cfg.bg}`}>
        <div>
          <p className="text-xs text-gray-400">Overall Credit Risk Flag</p>
          <p className="text-2xl font-black" style={{ color: cfg.color }}>{overallFlag}</p>
        </div>
        <div className="text-right">
          <p className="text-xs text-gray-400">Total Exposure</p>
          <p className="text-xl font-bold text-white">${totalExposure.toLocaleString()}</p>
        </div>
      </div>

      {/* Exposure breakdown */}
      <div className="grid grid-cols-3 gap-2 mb-4 text-xs">
        {[
          ['Downtime',    incidents.reduce((s, i) => s + i.downtime_cost_usd, 0)],
          ['SLA Penalty', incidents.reduce((s, i) => s + i.sla_penalty_usd, 0)],
          ['Reg Fines',   incidents.reduce((s, i) => s + i.regulatory_fine_usd, 0)],
        ].map(([label, val]) => (
          <div key={label} className="bg-gray-800 rounded p-2">
            <p className="text-gray-500">{label}</p>
            <p className="font-bold text-white">${val?.toLocaleString()}</p>
          </div>
        ))}
      </div>

      {/* Bar chart by attack type */}
      {chartData.length > 0 && (
        <ResponsiveContainer width="100%" height={120}>
          <BarChart data={chartData} margin={{ top: 4, right: 4, left: -20, bottom: 4 }}>
            <XAxis dataKey="name" tick={{ fontSize: 9, fill: '#6b7280' }} />
            <YAxis tick={{ fontSize: 9, fill: '#6b7280' }}
              tickFormatter={v => `$${(v/1000).toFixed(0)}k`} />
            <Tooltip formatter={v => [`$${v.toLocaleString()}`, 'Exposure']}
              contentStyle={{ background: '#111827', border: '1px solid #374151', fontSize: 11 }} />
            <Bar dataKey="value" radius={[3,3,0,0]}>
              {chartData.map((_, i) => (
                <Cell key={i} fill={['#ef4444','#f97316','#eab308','#3b82f6','#a855f7'][i % 5]} />
              ))}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      )}
    </div>
  )
}
