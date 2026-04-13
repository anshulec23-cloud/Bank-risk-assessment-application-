// Reusable KPI card
export default function MetricCard({ label, value, sub, color = 'text-white', icon: Icon }) {
  return (
    <div className="bg-gray-900 border border-gray-800 rounded-xl p-5 flex flex-col gap-1">
      <div className="flex items-center justify-between">
        <span className="text-gray-400 text-xs uppercase tracking-widest">{label}</span>
        {Icon && <Icon size={16} className="text-gray-600" />}
      </div>
      <span className={`text-3xl font-bold ${color}`}>{value}</span>
      {sub && <span className="text-gray-500 text-xs">{sub}</span>}
    </div>
  )
}
