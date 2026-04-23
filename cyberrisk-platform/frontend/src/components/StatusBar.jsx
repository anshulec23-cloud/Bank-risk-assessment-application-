// Top status bar — connection indicator + live ticker
export default function StatusBar({ connected, lastEvent }) {
  const sev = lastEvent?.classification?.severity
  const sevColor = { critical:'bg-red-600', high:'bg-orange-500', medium:'bg-yellow-500', low:'bg-blue-500', none:'bg-green-600' }

  return (
    <div className="flex items-center justify-between px-6 py-2 bg-gray-900 border-b border-gray-800 text-xs">
      <div className="flex items-center gap-3">
        <span className={`w-2 h-2 rounded-full ${connected ? 'bg-green-400 animate-pulse' : 'bg-red-500'}`} />
        <span className="text-gray-400">{connected ? 'LIVE — Pipeline Active' : 'Disconnected'}</span>
      </div>
      {lastEvent && lastEvent.is_anomaly && (
        <div className="flex items-center gap-2">
          <span className={`px-2 py-0.5 rounded text-white text-xs font-bold uppercase ${sevColor[sev] || 'bg-gray-600'}`}>
            {sev}
          </span>
          <span className="text-gray-300">
            {lastEvent.device_id} — {lastEvent.classification?.attack_type}
          </span>
          <span className="text-gray-500 ml-2">
            ${lastEvent.financial_risk?.total_exposure_usd?.toLocaleString()}
          </span>
        </div>
      )}
    </div>
  )
}
