import { useRef, useState } from 'react'
import { Shield, ShieldOff, Zap, Droplets, Factory } from 'lucide-react'
import { injectAttack, isolateDevice, restoreDevice } from '../api/client'

const DEVICE_ICONS = {
  power_plant:     Zap,
  water_treatment: Droplets,
  factory:         Factory,
}

const SEV_COLOR = {
  critical: 'border-red-500 shadow-red-900/50',
  high:     'border-orange-500 shadow-orange-900/50',
  medium:   'border-yellow-500',
  low:      'border-blue-500',
  none:     'border-gray-700',
}

const ATTACK_TYPES = ['DoS', 'Spoofing', 'Replay', 'PhysicalTamper']

export default function DeviceGrid({ devices, liveEvents }) {
  const [loading, setLoading] = useState({})
  const [attackLoading, setAttackLoading] = useState({})
  const [selectedAttack, setSelectedAttack] = useState({})
  const [toast, setToast] = useState('')
  const toastTimeoutRef = useRef(null)

  const handleIsolate = async (deviceId, isolated) => {
    setLoading(p => ({ ...p, [deviceId]: true }))
    try {
      isolated ? await restoreDevice(deviceId) : await isolateDevice(deviceId)
    } finally {
      setLoading(p => ({ ...p, [deviceId]: false }))
    }
  }

  const handleInjectAttack = async (deviceId) => {
    const attackType = selectedAttack[deviceId] || ATTACK_TYPES[0]

    setAttackLoading(p => ({ ...p, [deviceId]: true }))
    try {
      await injectAttack(deviceId, attackType)
      setToast(`Injected ${attackType} on ${deviceId}`)
      if (toastTimeoutRef.current) {
        clearTimeout(toastTimeoutRef.current)
      }
      toastTimeoutRef.current = setTimeout(() => {
        setToast('')
        toastTimeoutRef.current = null
      }, 3000)
    } finally {
      setAttackLoading(p => ({ ...p, [deviceId]: false }))
    }
  }

  return (
    <>
      {toast && (
        <div className="fixed top-4 right-4 z-50 rounded-lg border border-emerald-700 bg-emerald-950/95 px-4 py-2 text-xs font-medium text-emerald-200 shadow-lg">
          {toast}
        </div>
      )}

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {devices.map(device => {
          const live = liveEvents[device.device_id]
          const sev  = live?.classification?.severity || 'none'
          const Icon = DEVICE_ICONS[device.device_type] || Factory

          return (
            <div
              key={device.device_id}
              className={`bg-gray-900 border rounded-xl p-5 shadow-lg transition-all duration-300 ${SEV_COLOR[sev] || SEV_COLOR.none}`}
            >
              {/* Header */}
              <div className="flex items-center justify-between mb-3">
                <div className="flex items-center gap-2">
                  <Icon size={18} className="text-blue-400" />
                  <div>
                    <p className="font-semibold text-sm">{device.device_id}</p>
                    <p className="text-gray-500 text-xs capitalize">{device.device_type.replace('_', ' ')}</p>
                  </div>
                </div>
                <span className={`w-2 h-2 rounded-full ${device.is_isolated ? 'bg-red-500' : 'bg-green-400 animate-pulse'}`} />
              </div>

              {/* Sensors */}
              {live && (
                <div className="grid grid-cols-2 gap-2 mb-3 text-xs">
                  {[
                    ['Temp',    live.telemetry?.temperature, '°C'],
                    ['Pressure',live.telemetry?.pressure,    'bar'],
                    ['Flow',    live.telemetry?.flow_rate,   'L/m'],
                    ['Voltage', live.telemetry?.voltage,     'V'],
                  ].map(([k, v, u]) => (
                    <div key={k} className="bg-gray-800 rounded px-2 py-1">
                      <span className="text-gray-500">{k} </span>
                      <span className="font-mono font-bold text-white">{v?.toFixed(1)}{u}</span>
                    </div>
                  ))}
                </div>
              )}

              {/* Anomaly Score */}
              {live && (
                <div className="mb-3">
                  <div className="flex justify-between text-xs mb-1">
                    <span className="text-gray-400">Anomaly Score</span>
                    <span className={`font-bold ${live.anomaly_score > 0.65 ? 'text-red-400' : 'text-green-400'}`}>
                      {(live.anomaly_score * 100).toFixed(1)}%
                    </span>
                  </div>
                  <div className="h-1.5 bg-gray-800 rounded-full overflow-hidden">
                    <div
                      className={`h-full rounded-full transition-all duration-500 ${live.anomaly_score > 0.65 ? 'bg-red-500' : 'bg-green-500'}`}
                      style={{ width: `${live.anomaly_score * 100}%` }}
                    />
                  </div>
                </div>
              )}

              {/* Attack badge */}
              {live?.is_anomaly && (
                <div className="text-xs bg-red-950/50 border border-red-800 rounded px-2 py-1 mb-3">
                  <span className="text-red-400 font-bold uppercase">{live.classification?.attack_type}</span>
                  <span className="text-gray-400 ml-1">— {live.classification?.severity?.toUpperCase()}</span>
                </div>
              )}

              <div className="mb-3 flex gap-2">
                <select
                  value={selectedAttack[device.device_id] || ATTACK_TYPES[0]}
                  onChange={(e) => setSelectedAttack(p => ({ ...p, [device.device_id]: e.target.value }))}
                  className="min-w-0 flex-1 rounded border border-gray-700 bg-gray-800 px-2 py-1.5 text-xs text-gray-200 focus:border-orange-500 focus:outline-none"
                >
                  {ATTACK_TYPES.map(type => (
                    <option key={type} value={type}>{type}</option>
                  ))}
                </select>
                <button
                  onClick={() => handleInjectAttack(device.device_id)}
                  disabled={attackLoading[device.device_id]}
                  className="rounded border border-orange-700 bg-orange-900/40 px-3 py-1.5 text-xs font-semibold text-orange-200 transition-colors hover:bg-orange-900/60 disabled:cursor-not-allowed disabled:opacity-60"
                >
                  Inject Attack
                </button>
              </div>

              {/* Isolate button */}
              <button
                onClick={() => handleIsolate(device.device_id, device.is_isolated)}
                disabled={loading[device.device_id]}
                className={`w-full flex items-center justify-center gap-2 py-1.5 rounded text-xs font-semibold transition-colors
                  ${device.is_isolated
                    ? 'bg-green-900/50 hover:bg-green-800/50 text-green-300 border border-green-700'
                    : 'bg-red-900/40 hover:bg-red-900/60 text-red-300 border border-red-800'}`}
              >
                {device.is_isolated
                  ? <><Shield size={12} /> Restore Network</>
                  : <><ShieldOff size={12} /> Isolate Device</>
                }
              </button>
            </div>
          )
        })}
      </div>
    </>
  )
}
