import { useState } from 'react'
import { AlertTriangle, CheckCircle, FileText, DollarSign } from 'lucide-react'
import { resolveIncident, getNistReport, getCreditBrief } from '../api/client'

const SEV_STYLE = {
  critical: 'bg-red-500/10 text-red-400 border-red-800',
  high:     'bg-orange-500/10 text-orange-400 border-orange-800',
  medium:   'bg-yellow-500/10 text-yellow-400 border-yellow-800',
  low:      'bg-blue-500/10 text-blue-400 border-blue-800',
}

const CREDIT_COLOR = {
  CRITICAL: 'text-red-400', HIGH: 'text-orange-400',
  ELEVATED: 'text-yellow-400', NORMAL: 'text-green-400',
}

export default function IncidentFeed({ incidents, onRefresh }) {
  const [expandedId, setExpandedId] = useState(null)
  const [reportText, setReportText] = useState({})

  const handleResolve = async (id) => {
    await resolveIncident(id)
    onRefresh()
  }

  const loadReport = async (incidentId, type) => {
    const key = `${incidentId}_${type}`
    if (reportText[key]) { setExpandedId(key); return }
    try {
      const res = type === 'nist'
        ? await getNistReport(incidentId)
        : await getCreditBrief(incidentId)
      setReportText(p => ({ ...p, [key]: res.data }))
      setExpandedId(key)
    } catch { setReportText(p => ({ ...p, [key]: 'Report not available.' })) }
  }

  if (!incidents.length) return (
    <div className="text-center text-gray-600 py-12">No incidents detected yet.</div>
  )

  return (
    <div className="space-y-3 max-h-[600px] overflow-y-auto scrollbar-hide">
      {incidents.map(inc => (
        <div key={inc.incident_id} className={`border rounded-xl p-4 ${SEV_STYLE[inc.severity] || 'border-gray-700'}`}>

          {/* Row 1: ID + severity + status */}
          <div className="flex items-center justify-between mb-2">
            <div className="flex items-center gap-2">
              <AlertTriangle size={14} />
              <span className="font-mono text-sm font-bold">{inc.incident_id}</span>
              <span className="text-xs uppercase px-2 py-0.5 rounded border text-current">
                {inc.severity}
              </span>
            </div>
            <span className={`text-xs px-2 py-0.5 rounded ${inc.status === 'RESOLVED' ? 'bg-green-900/40 text-green-400' : 'bg-gray-800 text-gray-400'}`}>
              {inc.status}
            </span>
          </div>

          {/* Row 2: Details */}
          <div className="grid grid-cols-3 gap-2 text-xs mb-3">
            <div><span className="text-gray-500">Device</span><br/><span>{inc.device_id}</span></div>
            <div><span className="text-gray-500">Attack</span><br/><span>{inc.attack_type}</span></div>
            <div>
              <span className="text-gray-500">Credit Risk</span><br/>
              <span className={`font-bold ${CREDIT_COLOR[inc.credit_risk_flag]}`}>{inc.credit_risk_flag}</span>
            </div>
          </div>

          {/* Row 3: Financial */}
          <div className="flex items-center gap-1 text-xs mb-3 text-gray-400">
            <DollarSign size={12}/>
            <span>Total Exposure:</span>
            <span className="font-bold text-white ml-1">${inc.total_exposure_usd?.toLocaleString()}</span>
          </div>

          {/* Actions */}
          <div className="flex gap-2 flex-wrap">
            <button onClick={() => loadReport(inc.incident_id, 'nist')}
              className="flex items-center gap-1 text-xs px-3 py-1 bg-gray-800 hover:bg-gray-700 rounded border border-gray-700">
              <FileText size={11}/> NIST Report
            </button>
            <button onClick={() => loadReport(inc.incident_id, 'credit')}
              className="flex items-center gap-1 text-xs px-3 py-1 bg-gray-800 hover:bg-gray-700 rounded border border-gray-700">
              <DollarSign size={11}/> Credit Brief
            </button>
            {inc.status !== 'RESOLVED' && (
              <button onClick={() => handleResolve(inc.incident_id)}
                className="flex items-center gap-1 text-xs px-3 py-1 bg-green-900/40 hover:bg-green-900/60 rounded border border-green-800 text-green-300 ml-auto">
                <CheckCircle size={11}/> Resolve
              </button>
            )}
          </div>

          {/* Report text expansion */}
          {(expandedId === `${inc.incident_id}_nist` || expandedId === `${inc.incident_id}_credit`) && (
            <div className="mt-3 p-3 bg-gray-950 rounded border border-gray-800 text-xs font-mono text-gray-300 whitespace-pre-wrap max-h-64 overflow-y-auto">
              {reportText[expandedId]}
            </div>
          )}
        </div>
      ))}
    </div>
  )
}
