import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts'

const colors = ['#2dd4bf', '#38bdf8', '#f59e0b', '#fb7185', '#a78bfa']

function Metric({ label, value }) {
  return (
    <div className="rounded-xl border border-slate-500/30 bg-slate-900/40 p-4">
      <p className="text-xs uppercase tracking-wide text-slate-400">{label}</p>
      <p className="mt-1 text-xl font-bold text-cyan-200">{value}</p>
    </div>
  )
}

export default function DataScienceDashboard({ data, loading, error }) {
  if (loading) return <section className="glass rounded-2xl p-6 text-sm text-slate-300">Loading computed analytics...</section>
  if (error) return <section className="glass rounded-2xl p-6 text-sm text-rose-200">{error}</section>
  if (!data) return null

  const statistics = data.descriptive_statistics || {}
  const mean = (key) => Number(statistics[key]?.mean || 0).toLocaleString(undefined, { maximumFractionDigits: 0 })
  const selected = data.models?.comparison?.find((item) => item.model === data.models.selected_model)
  const trend = (data.trend || []).map((item) => ({ ...item, date: item.date.slice(5) }))
  const modelRows = (data.models?.comparison || []).map((item) => ({
    ...item,
    f1: Number((item.cv_macro_f1_mean * 100).toFixed(1)),
  }))

  return (
    <section className="mt-6 space-y-6">
      <div>
        <p className="text-xs font-semibold uppercase tracking-[0.2em] text-cyan-200">Data Science Analytics</p>
        <h2 className="font-display text-2xl font-bold text-slate-100">Evidence from the public Fitbit sample</h2>
        <p className="mt-2 text-sm text-slate-300">
          Descriptive findings, validated model comparisons, and exploratory clusters. These results are not medical diagnoses.
        </p>
      </div>

      <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-5">
        <Metric label="Valid records" value={data.quality.valid_records.toLocaleString()} />
        <Metric label="Average steps" value={mean('TotalSteps')} />
        <Metric label="Average calories" value={mean('Calories')} />
        <Metric label="Average active min" value={mean('ActivityScore')} />
        <Metric label="Best CV macro F1" value={selected ? `${(selected.cv_macro_f1_mean * 100).toFixed(1)}%` : 'n/a'} />
      </div>

      <div className="grid gap-6 lg:grid-cols-2">
        <section className="glass rounded-2xl p-5">
          <h3 className="mb-3 font-display font-semibold text-slate-100">Daily activity trend</h3>
          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={trend}>
                <CartesianGrid strokeDasharray="3 3" stroke="rgba(148,163,184,0.2)" />
                <XAxis dataKey="date" stroke="#cbd5e1" minTickGap={24} />
                <YAxis stroke="#cbd5e1" />
                <Tooltip contentStyle={{ backgroundColor: '#0f172a', border: '1px solid rgba(148,163,184,0.3)' }} />
                <Line type="monotone" dataKey="TotalSteps" name="Steps" stroke="#2dd4bf" dot={false} />
                <Line type="monotone" dataKey="ActivityScore" name="Active minutes" stroke="#f59e0b" dot={false} />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </section>

        <section className="glass rounded-2xl p-5">
          <h3 className="mb-3 font-display font-semibold text-slate-100">Cross-validated model comparison</h3>
          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={modelRows} layout="vertical" margin={{ left: 20, right: 12 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="rgba(148,163,184,0.2)" />
                <XAxis type="number" domain={[0, 100]} stroke="#cbd5e1" unit="%" />
                <YAxis type="category" dataKey="model" width={105} stroke="#cbd5e1" tick={{ fontSize: 11 }} />
                <Tooltip formatter={(value) => [`${value}%`, 'CV macro F1']} />
                <Bar dataKey="f1" name="CV macro F1">
                  {modelRows.map((entry, index) => <Cell key={entry.model} fill={colors[index % colors.length]} />)}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>
          <p className="mt-2 text-xs text-slate-400">Selected model: {data.models.selected_model}; scores are from stratified 5-fold CV on the training set.</p>
        </section>

        <section className="glass rounded-2xl p-5">
          <h3 className="mb-3 font-display font-semibold text-slate-100">Fitness-label distribution</h3>
          <div className="flex flex-wrap gap-3">
            {Object.entries(data.label_distribution).map(([label, count]) => (
              <Metric key={label} label={label} value={count.toLocaleString()} />
            ))}
          </div>
          <p className="mt-4 text-xs text-amber-200">{data.models.target_caveat}</p>
        </section>

        <section className="glass rounded-2xl p-5">
          <h3 className="mb-3 font-display font-semibold text-slate-100">Statistical test</h3>
          {data.statistical_test.available ? (
            <div className="space-y-2 text-sm text-slate-300">
              <p><span className="text-slate-400">Test:</span> {data.statistical_test.test}</p>
              <p><span className="text-slate-400">U statistic:</span> {data.statistical_test.statistic.toFixed(1)}</p>
              <p><span className="text-slate-400">p-value:</span> {data.statistical_test.p_value.toExponential(3)}</p>
              <p><span className="text-slate-400">Effect size:</span> {data.statistical_test.effect_size.toFixed(2)}</p>
              <p className="text-xs text-slate-400">{data.statistical_test.interpretation}</p>
            </div>
          ) : <p className="text-sm text-slate-300">{data.statistical_test.reason}</p>}
        </section>
      </div>

      <section className="glass rounded-2xl p-5">
        <h3 className="font-display font-semibold text-slate-100">PCA cluster profiles</h3>
        <p className="mt-1 text-xs text-slate-400">{data.clustering.interpretation} Selected k = {data.clustering.selected_k}.</p>
        <div className="mt-3 grid gap-3 md:grid-cols-3">
          {data.clustering.profiles.map((profile) => (
            <div key={profile.cluster} className="rounded-xl border border-slate-500/30 bg-slate-900/40 p-3 text-xs text-slate-300">
              <p className="font-semibold text-cyan-200">Cluster {profile.cluster}</p>
              <p>Steps: {profile.TotalSteps.toFixed(0)}</p>
              <p>Calories: {profile.Calories.toFixed(0)}</p>
              <p>Active min: {profile.ActivityScore.toFixed(0)}</p>
              <p>Sedentary min: {profile.SedentaryMinutes.toFixed(0)}</p>
            </div>
          ))}
        </div>
      </section>
    </section>
  )
}
