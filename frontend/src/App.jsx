import { useState, useEffect, useCallback } from 'react'
import { Shield, Activity, AlertTriangle, TrendingUp } from 'lucide-react'
import { useWebSocket } from './hooks/useWebSocket'
import StatusBar from './components/StatusBar'
import MetricCard from './components/MetricCard'
import DeviceGrid from './components/DeviceGrid'
import IncidentFeed from './components/IncidentFeed'
import TelemetryChart from './components/TelemetryChart'
import FinancialRisk from './components/FinancialRisk'
import {
  getDevices, getIncidents, getIncidentSummary, getTelemetryStats, getLatestTelemetry
} from './api/client'

export default function App() {
  const { connected, lastMessage } = useWebSocket()

  const [devices,   setDevices]   = useState([])
  const [incidents, setIncidents] = useState([])
  const [summary,   setSummary]   = useState(null)
  const [telStats,  setTelStats]  = useState(null)
  const [liveEvents, setLiveEvents] = useState({})   // keyed by device_id
  const [telHistory, setTelHistory] = useState([])   // last 30 readings for charts
  const [activeTab, setActiveTab] = useState('overview')

  // Initial data fetch
  const fetchAll = useCallback(async () => {
    const [d, i, s, ts] = await Promise.all([
      getDevices(), getIncidents(), getIncidentSummary(), getTelemetryStats()
    ])
    setDevices(d.data)
    setIncidents(i.data)
    setSummary(s.data)
    setTelStats(ts.data)
  }, [])

  useEffect(() => { fetchAll() }, [fetchAll])

  // Handle live WebSocket messages
  useEffect(() => {
    if (!lastMessage) return
    const msg = lastMessage

    // Update live events map per device
    setLiveEvents(prev => ({ ...prev, [msg.device_id]: msg }))

    // Append to telemetry history for charts
    setTelHistory(prev => [...prev.slice(-99), {
      ...msg.telemetry,
      device_id:    msg.device_id,
      anomaly_score: msg.anomaly_score,
      is_anomaly:    msg.is_anomaly,
      timestamp:     msg.timestamp,
    }])

    // If new incident detected, prepend to feed and refresh summary
    if (msg.incident) {
      fetchAll()
    }
  }, [lastMessage, fetchAll])

  const TABS = ['overview', 'devices', 'incidents', 'financial']

  return (
    <div className="min-h-screen bg-gray-950 text-gray-100">
      {/* Top nav */}
      <header className="bg-gray-900 border-b border-gray-800 px-6 py-4 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <Shield size={22} className="text-blue-400" />
          <div>
            <h1 className="font-bold text-base leading-none">CyberRisk Intelligence Platform</h1>
            <p className="text-gray-500 text-xs mt-0.5">ICS Security + Financial Risk · Powered by GenAI</p>
          </div>
        </div>
        <nav className="flex gap-1">
          {TABS.map(tab => (
            <button key={tab} onClick={() => setActiveTab(tab)}
              className={`px-3 py-1.5 rounded text-xs font-medium capitalize transition-colors
                ${activeTab === tab ? 'bg-blue-600 text-white' : 'text-gray-400 hover:bg-gray-800'}`}>
              {tab}
            </button>
          ))}
        </nav>
      </header>

      <StatusBar connected={connected} lastEvent={lastMessage} />

      <main className="p-6 space-y-6">

        {/* Overview Tab */}
        {activeTab === 'overview' && (
          <>
            {/* KPI row */}
            <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
              <MetricCard label="Total Incidents"  value={summary?.total_incidents ?? 0} color="text-white" icon={AlertTriangle} />
              <MetricCard label="Critical"         value={summary?.critical ?? 0} color="text-red-400" icon={AlertTriangle} />
              <MetricCard label="Total Exposure"   value={`$${((summary?.total_exposure_usd || 0)/1000).toFixed(0)}k`} color="text-orange-400" icon={TrendingUp} />
              <MetricCard label="Anomaly Rate"     value={`${telStats?.anomaly_rate_pct ?? 0}%`} color="text-yellow-400" icon={Activity} />
            </div>

            {/* Charts row */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
              <TelemetryChart data={telHistory} sensor="temperature" />
              <TelemetryChart data={telHistory} sensor="pressure" />
            </div>

            {/* Bottom row */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
              <div>
                <h3 className="text-sm font-semibold text-gray-400 mb-3">Recent Incidents</h3>
                <IncidentFeed incidents={incidents.slice(0, 5)} onRefresh={fetchAll} />
              </div>
              <FinancialRisk incidents={incidents} summary={summary} />
            </div>
          </>
        )}

        {/* Devices Tab */}
        {activeTab === 'devices' && (
          <DeviceGrid devices={devices} liveEvents={liveEvents} />
        )}

        {/* Incidents Tab */}
        {activeTab === 'incidents' && (
          <div className="max-w-3xl mx-auto">
            <div className="flex items-center justify-between mb-4">
              <h2 className="font-semibold">All Incidents</h2>
              <button onClick={fetchAll} className="text-xs px-3 py-1 bg-gray-800 rounded border border-gray-700 hover:bg-gray-700">
                Refresh
              </button>
            </div>
            <IncidentFeed incidents={incidents} onRefresh={fetchAll} />
          </div>
        )}

        {/* Financial Tab */}
        {activeTab === 'financial' && (
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
            <FinancialRisk incidents={incidents} summary={summary} />
            <div className="space-y-4">
              <div className="bg-gray-900 border border-gray-800 rounded-xl p-5">
                <h3 className="font-semibold text-sm mb-4">Exposure Breakdown</h3>
                <div className="space-y-3">
                  {incidents.slice(0, 8).map(inc => (
                    <div key={inc.incident_id} className="flex justify-between items-center text-xs">
                      <div>
                        <span className="font-mono">{inc.incident_id}</span>
                        <span className="text-gray-500 ml-2">{inc.attack_type}</span>
                      </div>
                      <div className="text-right">
                        <span className="font-bold text-white">${inc.total_exposure_usd?.toLocaleString()}</span>
                        <span className={`ml-2 px-1.5 py-0.5 rounded text-xs font-bold
                          ${{ CRITICAL:'bg-red-900/50 text-red-400', HIGH:'bg-orange-900/50 text-orange-400',
                              ELEVATED:'bg-yellow-900/50 text-yellow-400', NORMAL:'bg-green-900/50 text-green-400' }[inc.credit_risk_flag]}`}>
                          {inc.credit_risk_flag}
                        </span>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          </div>
        )}

      </main>
    </div>
  )
}
