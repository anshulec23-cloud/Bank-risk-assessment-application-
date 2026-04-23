import { useState, useEffect, useCallback, useRef } from 'react'
import { Shield } from 'lucide-react'
import { useWebSocket } from './hooks/useWebSocket'
import StatusBar from './components/StatusBar'
import SummaryBar from './components/SummaryBar'
import DeviceGrid from './components/DeviceGrid'
import IncidentFeed from './components/IncidentFeed'
import TelemetryChart from './components/TelemetryChart'
import FinancialRisk from './components/FinancialRisk'
import {
  getDevices, getIncidents, getIncidentSummary, getTelemetryStats, injectAttack, resolveIncident
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
  const [demoRunning, setDemoRunning] = useState(false)
  const [resolvingAll, setResolvingAll] = useState(false)
  const [apiError, setApiError] = useState('')
  const demoTimeoutsRef = useRef([])

  // Initial data fetch
  const fetchAll = useCallback(async () => {
    try {
      const [d, i, s, ts] = await Promise.all([
        getDevices(), getIncidents(), getIncidentSummary(), getTelemetryStats()
      ])
      setDevices(d.data)
      setIncidents(i.data)
      setSummary(s.data)
      setTelStats(ts.data)
      setApiError('')
    } catch {
      setApiError('REST data is retrying. Live telemetry is still active.')
    }
  }, [])

  useEffect(() => { fetchAll() }, [fetchAll])

  useEffect(() => {
    if (!connected) return
    const retryTimer = setInterval(() => {
      if (!devices.length || !summary || !telStats) {
        fetchAll()
      }
    }, 4000)

    return () => clearInterval(retryTimer)
  }, [connected, devices.length, summary, telStats, fetchAll])

  // Handle live WebSocket messages
  useEffect(() => {
    if (!lastMessage) return
    const msg = lastMessage

    // Update live events map per device
    setLiveEvents(prev => ({ ...prev, [msg.device_id]: msg }))

    setDevices(prev => {
      const existing = prev.find(device => device.device_id === msg.device_id)
      if (existing) {
        return prev.map(device => device.device_id === msg.device_id
          ? {
              ...device,
              device_type: msg.device_type || device.device_type,
              location: msg.location || device.location,
              is_isolated: msg.is_isolated ?? device.is_isolated,
            }
          : device)
      }

      return [...prev, {
        device_id: msg.device_id,
        device_type: msg.device_type || 'factory',
        location: msg.location || 'Unknown',
        is_isolated: msg.is_isolated ?? false,
      }]
    })

    // Append to telemetry history for charts
    setTelHistory(prev => [...prev.slice(-99), {
      temperature: msg.temperature,
      pressure: msg.pressure,
      flow_rate: msg.flow_rate,
      voltage: msg.voltage,
      device_id:    msg.device_id,
      anomaly_score: msg.anomaly_score,
      is_anomaly:    msg.is_anomaly,
      timestamp:     msg.timestamp,
    }])

    setTelStats(prev => {
      const totalEvents = (prev?.total_events ?? 0) + 1
      const anomalyEvents = (prev?.anomaly_events ?? 0) + (msg.is_anomaly ? 1 : 0)
      return {
        total_events: totalEvents,
        anomaly_events: anomalyEvents,
        normal_events: totalEvents - anomalyEvents,
        anomaly_rate_pct: Number(((anomalyEvents / totalEvents) * 100).toFixed(2)),
        avg_anomaly_score: prev?.avg_anomaly_score ?? msg.anomaly_score ?? 0,
      }
    })

    // If new incident detected, prepend to feed and refresh summary
    if (msg.incident) {
      setIncidents(prev => {
        if (prev.some(incident => incident.incident_id === msg.incident.incident_id)) {
          return prev
        }

        return [{
          ...msg.incident,
          device_id: msg.device_id,
          status: msg.incident.status || 'OPEN',
          is_isolated: msg.is_isolated,
          created_at: msg.timestamp,
          nist_report: msg.incident.nist_report,
          credit_brief: msg.incident.credit_brief,
        }, ...prev]
      })
      fetchAll()
    }
  }, [lastMessage, fetchAll])

  useEffect(() => {
    return () => {
      demoTimeoutsRef.current.forEach(clearTimeout)
    }
  }, [])

  const runDemo = useCallback(async () => {
    if (demoRunning) return

    setDemoRunning(true)
    demoTimeoutsRef.current.forEach(clearTimeout)
    demoTimeoutsRef.current = []

    try {
      await injectAttack('device-01', 'PhysicalTamper')

      demoTimeoutsRef.current = [
        setTimeout(async () => {
          await injectAttack('device-02', 'DoS')
          fetchAll()
        }, 3000),
        setTimeout(async () => {
          await injectAttack('device-03', 'Spoofing')
          fetchAll()
        }, 6000),
        setTimeout(() => {
          fetchAll()
          setDemoRunning(false)
          demoTimeoutsRef.current = []
        }, 9000),
      ]
      fetchAll()
    } catch {
      setDemoRunning(false)
    }
  }, [demoRunning, fetchAll])

  const handleResolveAll = useCallback(async () => {
    const openIncidents = incidents.filter(inc => inc.status !== 'RESOLVED')
    if (!openIncidents.length || resolvingAll) return

    setResolvingAll(true)
    try {
      for (const incident of openIncidents) {
        await resolveIncident(incident.incident_id)
      }
      await fetchAll()
    } finally {
      setResolvingAll(false)
    }
  }, [fetchAll, incidents, resolvingAll])

  const TABS = ['overview', 'devices', 'incidents', 'financial']
  const derivedSummary = {
    total_incidents: incidents.length,
    critical: incidents.filter(incident => incident.severity === 'critical').length,
    high: incidents.filter(incident => incident.severity === 'high').length,
    open: incidents.filter(incident => incident.status !== 'RESOLVED').length,
    total_exposure_usd: incidents.reduce((sum, incident) => sum + (incident.total_exposure_usd || 0), 0),
  }
  const effectiveSummary = summary || derivedSummary
  const creditRiskCounts = incidents.reduce((acc, incident) => {
    const flag = incident.credit_risk_flag || 'NORMAL'
    acc[flag] = (acc[flag] || 0) + 1
    return acc
  }, { NORMAL: 0, ELEVATED: 0, HIGH: 0, CRITICAL: 0 })
  const portfolioExposure = incidents.reduce((sum, incident) => sum + (incident.total_exposure_usd || 0), 0)
  const facilityCount = new Set(incidents.map(incident => incident.device_id)).size
  const elevatedFacilityCount = new Set(
    incidents
      .filter(incident => ['ELEVATED', 'HIGH', 'CRITICAL'].includes(incident.credit_risk_flag))
      .map(incident => incident.device_id)
  ).size
  const recoveryTimelineDays = Math.ceil((portfolioExposure / 500000) * 3)

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
        <div className="flex items-center gap-3">
          {demoRunning && (
            <div className="rounded-full border border-blue-700 bg-blue-950/80 px-3 py-1 text-xs font-medium text-blue-200 animate-pulse">
              Demo running...
            </div>
          )}
          <nav className="flex gap-1">
            {TABS.map(tab => (
              <button key={tab} onClick={() => setActiveTab(tab)}
                className={`px-3 py-1.5 rounded text-xs font-medium capitalize transition-colors
                  ${activeTab === tab ? 'bg-blue-600 text-white' : 'text-gray-400 hover:bg-gray-800'}`}>
                {tab}
              </button>
            ))}
          </nav>
          <button
            onClick={runDemo}
            disabled={demoRunning}
            className="rounded-lg border border-blue-700 bg-blue-900/50 px-3 py-1.5 text-xs font-semibold text-blue-200 transition-colors hover:bg-blue-900/70 disabled:cursor-not-allowed disabled:opacity-60"
          >
            Run demo
          </button>
        </div>
      </header>

      <StatusBar connected={connected} lastEvent={lastMessage} />

      <main className="p-6 space-y-6">
        {apiError && (
          <div className="rounded-lg border border-yellow-800 bg-yellow-950/40 px-4 py-2 text-sm text-yellow-200">
            {apiError}
          </div>
        )}

        {/* Overview Tab */}
        {activeTab === 'overview' && (
          <>
            {/* KPI row */}
            <SummaryBar summary={effectiveSummary} stats={telStats} connected={connected} />

            <div className="rounded-xl border border-gray-800 bg-gray-900 p-5">
              <div className="flex flex-wrap gap-2 mb-4">
                {[
                  ['NORMAL', 'bg-green-900/40 text-green-300 border-green-700'],
                  ['ELEVATED', 'bg-yellow-900/40 text-yellow-300 border-yellow-700'],
                  ['HIGH', 'bg-orange-900/40 text-orange-300 border-orange-700'],
                  ['CRITICAL', 'bg-red-900/40 text-red-300 border-red-700'],
                ].map(([label, classes]) => (
                  <span key={label} className={`rounded-full border px-3 py-1 text-xs font-semibold ${classes}`}>
                    {label}: {creditRiskCounts[label] || 0}
                  </span>
                ))}
              </div>
              <p className="text-3xl font-black text-white">
                ${((portfolioExposure || 0) / 1000000).toFixed(1)}M across {facilityCount} facilities
              </p>
              <p className="mt-2 text-sm text-gray-400">
                {elevatedFacilityCount} facility loans are at elevated credit risk - covenant review recommended.
              </p>
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
              <FinancialRisk incidents={incidents} summary={effectiveSummary} />
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
                <div className="flex gap-2">
                  <button
                    onClick={handleResolveAll}
                    disabled={resolvingAll || !incidents.some(inc => inc.status !== 'RESOLVED')}
                    className="text-xs px-3 py-1 bg-green-900/40 rounded border border-green-800 text-green-300 hover:bg-green-900/60 disabled:cursor-not-allowed disabled:opacity-50"
                  >
                    {resolvingAll ? 'Resolving...' : 'Resolve all'}
                  </button>
                  <button onClick={fetchAll} className="text-xs px-3 py-1 bg-gray-800 rounded border border-gray-700 hover:bg-gray-700">
                    Refresh
                  </button>
                </div>
              </div>
              <IncidentFeed incidents={incidents} onRefresh={fetchAll} />
            </div>
        )}

        {/* Financial Tab */}
        {activeTab === 'financial' && (
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
            <FinancialRisk incidents={incidents} summary={effectiveSummary} />
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
                <p className="mt-4 text-sm text-gray-400">
                  Estimated recovery timeline: {recoveryTimelineDays} days
                </p>
              </div>
            </div>
          </div>
        )}

      </main>
    </div>
  )
}
