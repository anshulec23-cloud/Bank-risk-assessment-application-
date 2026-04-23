import { ShieldAlert, Activity, DollarSign, Wifi } from 'lucide-react'
import { fmtUSD } from '../utils'

function KPI({ icon: Icon, label, value, sub, color = 'text-white' }) {
  return (
    <div className="bg-gray-900 border border-gray-800 rounded-xl p-4 flex items-center gap-4">
      <div className="p-2 rounded-lg bg-gray-800">
        <Icon className={`w-5 h-5 ${color}`} />
      </div>
      <div>
        <p className="text-xs text-gray-500 uppercase tracking-wider">{label}</p>
        <p className={`text-2xl font-bold ${color}`}>{value}</p>
        {sub && <p className="text-xs text-gray-500 mt-0.5">{sub}</p>}
      </div>
    </div>
  )
}

export default function SummaryBar({ summary, stats, connected }) {
  const anomalyRatePct = stats
    ? (stats.anomaly_rate ?? ((stats.anomaly_rate_pct ?? 0) / 100)) * 100
    : null

  return (
    <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
      <KPI
        icon={ShieldAlert}
        label="Total Incidents"
        value={summary?.total_incidents ?? '—'}
        sub={`${summary?.critical ?? 0} critical · ${summary?.open ?? 0} open`}
        color="text-red-400"
      />
      <KPI
        icon={DollarSign}
        label="Total Exposure"
        value={summary ? fmtUSD(summary.total_exposure_usd) : '—'}
        sub="across all incidents"
        color="text-orange-400"
      />
      <KPI
        icon={Activity}
        label="Anomaly Rate"
        value={stats ? `${anomalyRatePct.toFixed(1)}%` : '—'}
        sub={`${stats?.anomaly_events ?? 0} / ${stats?.total_events ?? 0} events`}
        color="text-yellow-400"
      />
      <KPI
        icon={Wifi}
        label="Live Feed"
        value={connected ? 'CONNECTED' : 'RECONNECTING'}
        sub="WebSocket pipeline"
        color={connected ? 'text-teal-400' : 'text-gray-500'}
      />
    </div>
  )
}
