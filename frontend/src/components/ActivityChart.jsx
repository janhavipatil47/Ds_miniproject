import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from 'recharts'

const metricMap = {
  steps: { label: 'Steps', color: '#2dd4bf' },
  calories: { label: 'Calories', color: '#38bdf8' },
  activity: { label: 'Active Min', color: '#f59e0b' },
}

export default function ActivityChart({ history, metric, onMetricChange, window, onWindowChange }) {
  const chartData = (history || []).map((item) => ({
    ...item,
    day: item.date?.slice(5) || item.date,
  }))

  const activeMetric = metricMap[metric] ? metric : 'steps'

  return (
    <section className="glass rounded-2xl p-6 shadow-glass">
      <div className="mb-3 flex flex-wrap items-center justify-between gap-3">
        <h3 className="font-display text-lg font-semibold text-slate-100">Activity Trend</h3>
        <div className="flex items-center gap-2">
          <select
            value={window}
            onChange={(event) => onWindowChange(event.target.value)}
            className="rounded-lg border border-slate-500/40 bg-slate-900/70 px-2 py-1 text-xs text-slate-100"
          >
            <option value="7d">Past 7 Days</option>
            <option value="30d">Past Month</option>
          </select>

          <select
            value={activeMetric}
            onChange={(event) => onMetricChange(event.target.value)}
            className="rounded-lg border border-slate-500/40 bg-slate-900/70 px-2 py-1 text-xs text-slate-100"
          >
            <option value="steps">Steps</option>
            <option value="calories">Calories</option>
            <option value="activity">Active Minutes</option>
          </select>
        </div>
      </div>

      {chartData.length === 0 ? (
        <p className="text-sm text-slate-300">No saved activity data for this period yet. Add daily data using the calendar date field.</p>
      ) : null}

      <div className="h-64 w-full">
        <ResponsiveContainer width="100%" height="100%">
          <LineChart data={chartData}>
            <CartesianGrid strokeDasharray="3 3" stroke="rgba(148,163,184,0.2)" />
            <XAxis dataKey="day" stroke="#cbd5e1" />
            <YAxis stroke="#cbd5e1" />
            <Tooltip
              contentStyle={{
                backgroundColor: '#0f172a',
                border: '1px solid rgba(148,163,184,0.3)',
                color: '#e2e8f0',
              }}
            />
            <Line
              type="monotone"
              dataKey={activeMetric}
              stroke={metricMap[activeMetric].color}
              strokeWidth={3}
              dot={{ r: 4 }}
              activeDot={{ r: 6 }}
            />
          </LineChart>
        </ResponsiveContainer>
      </div>
    </section>
  )
}
