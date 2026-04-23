import React from 'react'
import { LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer, ReferenceLine } from 'recharts'

const SENSOR_CONFIG = {
  temperature: { color: '#f97316', label: 'Temp (°C)',    threshold: 85 },
  pressure:    { color: '#3b82f6', label: 'Pressure (bar)', threshold: 6.5 },
  flow_rate:   { color: '#22c55e', label: 'Flow (L/min)', threshold: null },
  voltage:     { color: '#a855f7', label: 'Voltage (V)',  threshold: 200 },
}

const CustomTooltip = ({ active, payload, label }) => {
  if (!active || !payload?.length) return null
  return (
    <div className="bg-gray-900 border border-gray-700 rounded px-3 py-2 text-xs">
      <p className="text-gray-400 mb-1">{label}</p>
      {payload.map(p => (
        <p key={p.dataKey} style={{ color: p.color }}>{p.name}: {p.value?.toFixed(2)}</p>
      ))}
    </div>
  )
}

export default function TelemetryChart({ data, sensor = 'temperature' }) {
  const cfg = SENSOR_CONFIG[sensor]
  const chartData = data.slice(-30).map((d) => ({
    t: new Date(d.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' }),
    value: d[sensor],
    anomaly: d.is_anomaly,
  }))

  return (
    <div className="bg-gray-900 border border-gray-800 rounded-xl p-4">
      <p className="text-sm text-gray-400 mb-3 font-medium">{cfg.label} — Last 30 readings</p>
      <ResponsiveContainer width="100%" height={160}>
        <LineChart data={chartData}>
          <XAxis dataKey="t" tick={{ fontSize: 9, fill: '#6b7280' }} interval="preserveStartEnd" />
          <YAxis tick={{ fontSize: 10, fill: '#6b7280' }} width={40} />
          <Tooltip content={<CustomTooltip />} />
          {cfg.threshold && (
            <ReferenceLine y={cfg.threshold} stroke="#ef4444" strokeDasharray="4 2" label={{ value: 'Threshold', fontSize: 9, fill: '#ef4444' }} />
          )}
          <Line
            type="monotone"
            dataKey="value"
            stroke={cfg.color}
            strokeWidth={2}
              dot={(props) => {
                const d = chartData[props.index]
                return d?.anomaly
                  ? <circle key={props.key} cx={props.cx} cy={props.cy} r={4} fill="#ef4444" className="animate-pulse" />
                  : <React.Fragment key={props.key} />
              }}
            name={cfg.label}
          />
        </LineChart>
      </ResponsiveContainer>
    </div>
  )
}
