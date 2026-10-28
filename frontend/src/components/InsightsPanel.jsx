import { Lightbulb } from 'lucide-react'

export default function InsightsPanel({ insights }) {
  const safeInsights = Array.isArray(insights) ? insights.slice(0, 3) : []

  return (
    <section className="glass rounded-2xl p-6 shadow-glass">
      <h3 className="mb-3 flex items-center gap-2 font-display text-lg font-semibold text-slate-100">
        <Lightbulb size={18} className="text-cyan-300" />
        Personalized Insights
      </h3>

      {safeInsights.length === 0 ? (
        <p className="text-sm text-slate-300">Complete your profile or add activity data to see personalized insights.</p>
      ) : (
        <ul className="list-disc space-y-2 pl-5 text-sm text-slate-200">
          {safeInsights.map((item, index) => (
            <li key={`${item}-${index}`}>{item}</li>
          ))}
        </ul>
      )}
    </section>
  )
}
