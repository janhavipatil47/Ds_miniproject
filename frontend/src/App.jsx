import { useEffect, useMemo, useState } from 'react'
import axios from 'axios'
import { motion as Motion } from 'framer-motion'
import {
  Activity,
  UserRound,
  Ruler,
  Weight,
  Footprints,
  Flame,
  Sparkles,
  LoaderCircle,
  AlertTriangle,
  Gauge,
  CalendarDays,
  LogOut,
  Save,
  ShieldCheck,
} from 'lucide-react'
import InputField from './components/InputField'
import InsightsPanel from './components/InsightsPanel'
import ActivityChart from './components/ActivityChart'
import DataScienceDashboard from './components/DataScienceDashboard'

const API_URL = import.meta.env.VITE_API_URL || 'http://127.0.0.1:5000'
const STORAGE_KEY = 'smartfit_user'

const initialSignup = {
  username: '',
  password: '',
  age: '',
  height: '',
  weight: '',
}

const initialLogin = {
  username: '',
  password: '',
}

const initialActivity = {
  date: new Date().toISOString().slice(0, 10),
  steps: '',
  calories: '',
  activity: '',
}

const fitnessBadgeClass = {
  Low: 'badge border border-rose-300/30 bg-rose-500/20 text-rose-200',
  Medium: 'badge border border-amber-300/30 bg-amber-500/20 text-amber-200',
  High: 'badge border border-emerald-300/30 bg-emerald-500/20 text-emerald-200',
}

function AuthPanel({
  authMode,
  setAuthMode,
  signupForm,
  loginForm,
  onSignupChange,
  onLoginChange,
  onSignupSubmit,
  onLoginSubmit,
  loading,
}) {
  return (
    <section className="glass rounded-2xl p-6 md:p-8 shadow-glass">
      <div className="mb-4 flex items-center justify-between">
        <div>
          <p className="inline-flex items-center gap-2 text-xs font-semibold uppercase tracking-[0.2em] text-cyan-200">
            <ShieldCheck size={14} />
            Secure Access
          </p>
          <h2 className="font-display text-2xl font-bold text-slate-100">Create account or login</h2>
        </div>

        <div className="glass inline-flex rounded-full p-1 text-xs">
          <button
            onClick={() => setAuthMode('signup')}
            className={`rounded-full px-4 py-2 transition ${authMode === 'signup' ? 'bg-cyan-400/20 text-cyan-200' : 'text-slate-300'}`}
          >
            Sign Up
          </button>
          <button
            onClick={() => setAuthMode('login')}
            className={`rounded-full px-4 py-2 transition ${authMode === 'login' ? 'bg-cyan-400/20 text-cyan-200' : 'text-slate-300'}`}
          >
            Login
          </button>
        </div>
      </div>

      {authMode === 'signup' ? (
        <form onSubmit={onSignupSubmit} className="grid gap-4 md:grid-cols-2">
          <InputField
            icon={UserRound}
            label="Username"
            name="username"
            value={signupForm.username}
            onChange={onSignupChange}
            placeholder="e.g. alex"
            type="text"
            required
          />
          <InputField
            icon={ShieldCheck}
            label="Password"
            name="password"
            value={signupForm.password}
            onChange={onSignupChange}
            placeholder="minimum 4 chars"
            type="password"
            required
          />
          <InputField
            icon={UserRound}
            label="Age"
            name="age"
            value={signupForm.age}
            onChange={onSignupChange}
            placeholder="e.g. 28"
            min="1"
            step="1"
          />
          <InputField
            icon={Ruler}
            label="Height (cm or m)"
            name="height"
            value={signupForm.height}
            onChange={onSignupChange}
            placeholder="e.g. 175 or 1.75"
            min="0"
            step="any"
          />
          <InputField
            icon={Weight}
            label="Weight (kg)"
            name="weight"
            value={signupForm.weight}
            onChange={onSignupChange}
            placeholder="e.g. 72"
            min="0"
            step="any"
          />

          <button
            type="submit"
            disabled={loading}
            className="col-span-full mt-2 flex items-center justify-center gap-2 rounded-xl bg-gradient-to-r from-cyan-400 to-teal-400 px-4 py-3 font-semibold text-slate-900 transition hover:brightness-110 disabled:cursor-not-allowed disabled:opacity-70"
          >
            {loading ? <LoaderCircle className="animate-spin" size={18} /> : <Sparkles size={18} />}
            {loading ? 'Creating account...' : 'Create Account'}
          </button>
        </form>
      ) : (
        <form onSubmit={onLoginSubmit} className="grid gap-4 md:grid-cols-2">
          <InputField
            icon={UserRound}
            label="Username"
            name="username"
            value={loginForm.username}
            onChange={onLoginChange}
            placeholder="e.g. alex"
            type="text"
            required
          />
          <InputField
            icon={ShieldCheck}
            label="Password"
            name="password"
            value={loginForm.password}
            onChange={onLoginChange}
            placeholder="your password"
            type="password"
            required
          />

          <button
            type="submit"
            disabled={loading}
            className="col-span-full mt-2 flex items-center justify-center gap-2 rounded-xl bg-gradient-to-r from-cyan-400 to-teal-400 px-4 py-3 font-semibold text-slate-900 transition hover:brightness-110 disabled:cursor-not-allowed disabled:opacity-70"
          >
            {loading ? <LoaderCircle className="animate-spin" size={18} /> : <ShieldCheck size={18} />}
            {loading ? 'Signing in...' : 'Login'}
          </button>
        </form>
      )}
    </section>
  )
}

function App() {
  const [authMode, setAuthMode] = useState('signup')
  const [user, setUser] = useState(() => {
    try {
      const saved = localStorage.getItem(STORAGE_KEY)
      return saved ? JSON.parse(saved) : null
    } catch {
      return null
    }
  })

  const [signupForm, setSignupForm] = useState(initialSignup)
  const [loginForm, setLoginForm] = useState(initialLogin)
  const [profileForm, setProfileForm] = useState({ age: '', height: '', weight: '' })
  const [activityForm, setActivityForm] = useState(initialActivity)

  const [profileResult, setProfileResult] = useState(null)
  const [activityResult, setActivityResult] = useState(null)
  const [history, setHistory] = useState([])
  const [analytics, setAnalytics] = useState(null)
  const [analyticsLoading, setAnalyticsLoading] = useState(true)
  const [analyticsError, setAnalyticsError] = useState('')

  const [historyWindow, setHistoryWindow] = useState('7d')
  const [historyMetric, setHistoryMetric] = useState('steps')
  const [loading, setLoading] = useState(false)
  const [historyLoading, setHistoryLoading] = useState(false)
  const [error, setError] = useState('')

  useEffect(() => {
    const fetchAnalytics = async () => {
      try {
        const response = await axios.get(`${API_URL}/analytics`, { timeout: 30000 })
        setAnalytics(response.data)
      } catch {
        setAnalyticsError('Analytics are temporarily unavailable. Start the backend and verify the dataset.')
      } finally {
        setAnalyticsLoading(false)
      }
    }
    fetchAnalytics()
  }, [])

  const numericValues = useMemo(
    () => ({
      steps: Number(activityForm.steps || 0),
      calories: Number(activityForm.calories || 0),
      activity: Number(activityForm.activity || 0),
    }),
    [activityForm],
  )

  const fetchProfile = async (userId) => {
    const response = await axios.get(`${API_URL}/profile`, {
      params: { user_id: userId },
      timeout: 10000,
    })
    const profile = response.data?.profile
    if (!profile) return

    setProfileResult(profile)
    setProfileForm({
      age: String(profile.age ?? ''),
      height: String(profile.height ?? ''),
      weight: String(profile.weight ?? ''),
    })
  }

  const fetchHistory = async (userId, window) => {
    if (!userId) {
      setHistory([])
      return
    }

    setHistoryLoading(true)
    try {
      const response = await axios.get(`${API_URL}/activity-history`, {
        params: { user_id: userId, window },
        timeout: 10000,
      })
      setHistory(response.data?.history || [])
    } catch {
      setHistory([])
    } finally {
      setHistoryLoading(false)
    }
  }

  useEffect(() => {
    const bootstrap = async () => {
      if (!user?.id) return
      try {
        await fetchProfile(user.id)
        await fetchHistory(user.id, historyWindow)
      } catch {
        localStorage.removeItem(STORAGE_KEY)
        setUser(null)
      }
    }
    bootstrap()
  }, [user?.id, historyWindow])

  const handleSignupChange = (event) => {
    const { name, value } = event.target
    setSignupForm((prev) => ({ ...prev, [name]: value }))
  }

  const handleLoginChange = (event) => {
    const { name, value } = event.target
    setLoginForm((prev) => ({ ...prev, [name]: value }))
  }

  const handleProfileChange = (event) => {
    const { name, value } = event.target
    setProfileForm((prev) => ({ ...prev, [name]: value }))
  }

  const handleActivityChange = (event) => {
    const { name, value } = event.target
    setActivityForm((prev) => ({ ...prev, [name]: value }))
  }

  const submitSignup = async (event) => {
    event.preventDefault()
    setLoading(true)
    setError('')

    try {
      const payload = {
        username: signupForm.username.trim(),
        password: signupForm.password,
        age: Number(signupForm.age),
        height: Number(signupForm.height),
        weight: Number(signupForm.weight),
      }

      const response = await axios.post(`${API_URL}/auth/register`, payload, { timeout: 10000 })
      const currentUser = response.data?.user
      if (!currentUser) throw new Error('invalid register response')

      setUser(currentUser)
      localStorage.setItem(STORAGE_KEY, JSON.stringify(currentUser))

      const profile = response.data?.profile
      if (profile) {
        setProfileResult(profile)
        setProfileForm({
          age: String(payload.age),
          height: String(payload.height),
          weight: String(payload.weight),
        })
      }
      await fetchHistory(currentUser.id, historyWindow)
    } catch (requestError) {
      const message = requestError?.response?.data?.error || 'Sign up failed. Please try again.'
      setError(message)
    } finally {
      setLoading(false)
    }
  }

  const submitLogin = async (event) => {
    event.preventDefault()
    setLoading(true)
    setError('')

    try {
      const response = await axios.post(`${API_URL}/auth/login`, {
        username: loginForm.username.trim(),
        password: loginForm.password,
      }, { timeout: 10000 })

      const currentUser = response.data?.user
      if (!currentUser) throw new Error('invalid login response')

      setUser(currentUser)
      localStorage.setItem(STORAGE_KEY, JSON.stringify(currentUser))
      await fetchProfile(currentUser.id)
      await fetchHistory(currentUser.id, historyWindow)
    } catch (requestError) {
      const message = requestError?.response?.data?.error || 'Login failed. Please try again.'
      setError(message)
    } finally {
      setLoading(false)
    }
  }

  const submitProfileUpdate = async (event) => {
    event.preventDefault()
    if (!user?.id) return

    setLoading(true)
    setError('')
    try {
      const payload = {
        user_id: user.id,
        age: Number(profileForm.age),
        height: Number(profileForm.height),
        weight: Number(profileForm.weight),
      }
      const response = await axios.put(`${API_URL}/profile`, payload, { timeout: 10000 })
      const profile = response.data?.profile
      if (profile) setProfileResult(profile)
    } catch (requestError) {
      const message = requestError?.response?.data?.error || 'Profile update failed. Please try again.'
      setError(message)
    } finally {
      setLoading(false)
    }
  }

  const submitActivity = async (event) => {
    event.preventDefault()
    if (!user?.id) return

    setLoading(true)
    setError('')
    try {
      const activityMinutes = Number(activityForm.activity)
      const payload = {
        user_id: user.id,
        date: activityForm.date,
        steps: Number(activityForm.steps),
        calories: Number(activityForm.calories),
        activity: activityMinutes,
        sedentary: Math.max(0, 1440 - activityMinutes),
      }

      const response = await axios.post(`${API_URL}/daily-entry`, payload, { timeout: 10000 })
      setActivityResult(response.data)
      await fetchHistory(user.id, historyWindow)
    } catch (requestError) {
      const message = requestError?.response?.data?.error || 'Daily entry save failed. Please try again.'
      setError(message)
    } finally {
      setLoading(false)
    }
  }

  const handleWindowChange = async (nextWindow) => {
    setHistoryWindow(nextWindow)
    if (user?.id) {
      await fetchHistory(user.id, nextWindow)
    }
  }

  const handleLogout = () => {
    localStorage.removeItem(STORAGE_KEY)
    setUser(null)
    setProfileResult(null)
    setActivityResult(null)
    setHistory([])
    setSignupForm(initialSignup)
    setLoginForm(initialLogin)
    setProfileForm({ age: '', height: '', weight: '' })
    setActivityForm(initialActivity)
    setError('')
  }

  const visibleResult = activityResult || profileResult

  return (
    <main className="relative min-h-screen overflow-hidden px-4 py-8 md:px-10 md:py-12">
      <Motion.div
        initial={{ opacity: 0, y: 22 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.55, ease: 'easeOut' }}
        className="mx-auto w-full max-w-6xl"
      >
        <header className="mb-6 flex flex-wrap items-center justify-between gap-3">
          <div>
            <p className="inline-flex items-center gap-2 text-xs font-semibold uppercase tracking-[0.2em] text-cyan-200">
              <Sparkles size={14} />
              SmartFit AI
            </p>
            <h1 className="font-display text-3xl font-extrabold text-slate-100 md:text-4xl">Smart health assistant</h1>
          </div>

          {user ? (
            <div className="flex items-center gap-2">
              <span className="badge border border-cyan-300/30 bg-cyan-500/10 text-cyan-200">
                Logged in as {user.username}
              </span>
              <button
                onClick={handleLogout}
                className="inline-flex items-center gap-2 rounded-xl border border-slate-400/40 bg-slate-900/50 px-3 py-2 text-sm text-slate-200 transition hover:border-cyan-300/50"
              >
                <LogOut size={14} />
                Logout
              </button>
            </div>
          ) : null}
        </header>

        {!user ? (
          <AuthPanel
            authMode={authMode}
            setAuthMode={setAuthMode}
            signupForm={signupForm}
            loginForm={loginForm}
            onSignupChange={handleSignupChange}
            onLoginChange={handleLoginChange}
            onSignupSubmit={submitSignup}
            onLoginSubmit={submitLogin}
            loading={loading}
          />
        ) : (
          <section className="grid gap-6 lg:grid-cols-[minmax(0,1fr)_minmax(0,1.1fr)]">
            <div className="space-y-6">
              <section className="glass rounded-2xl p-6 shadow-glass">
                <h2 className="font-display text-xl font-bold text-slate-100">Personal Data</h2>
                <p className="mt-2 text-sm text-slate-300">Update your age, height, or weight anytime without creating a new account.</p>

                <form onSubmit={submitProfileUpdate} className="mt-5 grid gap-4 md:grid-cols-3">
                  <InputField
                    icon={UserRound}
                    label="Age"
                    name="age"
                    value={profileForm.age}
                    onChange={handleProfileChange}
                    min="1"
                    step="1"
                  />
                  <InputField
                    icon={Ruler}
                    label="Height (cm or m)"
                    name="height"
                    value={profileForm.height}
                    onChange={handleProfileChange}
                    min="0"
                    step="any"
                  />
                  <InputField
                    icon={Weight}
                    label="Weight (kg)"
                    name="weight"
                    value={profileForm.weight}
                    onChange={handleProfileChange}
                    min="0"
                    step="any"
                  />

                  <button
                    type="submit"
                    disabled={loading}
                    className="col-span-full inline-flex items-center justify-center gap-2 rounded-xl border border-cyan-400/40 bg-cyan-500/10 px-4 py-3 font-semibold text-cyan-200 transition hover:bg-cyan-500/20 disabled:cursor-not-allowed disabled:opacity-70"
                  >
                    {loading ? <LoaderCircle className="animate-spin" size={18} /> : <Save size={16} />}
                    Save Profile
                  </button>
                </form>
              </section>

              <section className="glass rounded-2xl p-6 shadow-glass">
                <h2 className="font-display text-xl font-bold text-slate-100">Daily Activity Entry</h2>
                <p className="mt-2 text-sm text-slate-300">Add today or backfill any missed day in the same session using the calendar input.</p>

                <form onSubmit={submitActivity} className="mt-5 space-y-4">
                  <InputField
                    icon={CalendarDays}
                    label="Date"
                    name="date"
                    value={activityForm.date}
                    onChange={handleActivityChange}
                    type="date"
                    required
                  />
                  <InputField
                    icon={Footprints}
                    label="Steps"
                    name="steps"
                    value={activityForm.steps}
                    onChange={handleActivityChange}
                    min="0"
                    step="any"
                  />
                  <InputField
                    icon={Flame}
                    label="Calories"
                    name="calories"
                    value={activityForm.calories}
                    onChange={handleActivityChange}
                    min="0"
                    step="any"
                  />
                  <InputField
                    icon={Activity}
                    label="Active Minutes"
                    name="activity"
                    value={activityForm.activity}
                    onChange={handleActivityChange}
                    min="0"
                    step="any"
                  />

                  <button
                    type="submit"
                    disabled={loading}
                    className="flex w-full items-center justify-center gap-2 rounded-xl bg-gradient-to-r from-cyan-400 to-teal-400 px-4 py-3 font-semibold text-slate-900 transition hover:brightness-110 disabled:cursor-not-allowed disabled:opacity-70"
                  >
                    {loading ? <LoaderCircle className="animate-spin" size={18} /> : <Gauge size={18} />}
                    {loading ? 'Saving...' : 'Save Daily Entry'}
                  </button>
                </form>
              </section>

              <ActivityChart
                history={history}
                metric={historyMetric}
                onMetricChange={setHistoryMetric}
                window={historyWindow}
                onWindowChange={handleWindowChange}
              />
              {historyLoading ? <p className="text-xs text-slate-300">Loading history...</p> : null}
            </div>

            <div className="space-y-6">
              <section className="glass animate-pop rounded-2xl p-6 shadow-glass">
                <h3 className="mb-3 font-display text-lg font-semibold text-slate-100">Health Summary</h3>
                <div className="grid gap-3 text-sm text-slate-200">
                  <div className="flex items-center justify-between rounded-xl border border-slate-500/30 bg-slate-900/40 px-4 py-3">
                    <span>BMI</span>
                    <span className="font-semibold text-cyan-200">{visibleResult?.bmi ?? 'Not available yet'}</span>
                  </div>
                  <div className="flex items-center justify-between rounded-xl border border-slate-500/30 bg-slate-900/40 px-4 py-3">
                    <span>Cluster Type</span>
                    <span className="badge border border-cyan-300/30 bg-cyan-500/10 text-cyan-200">{visibleResult?.cluster_type || 'Pending'}</span>
                  </div>
                  <div className="flex items-center justify-between rounded-xl border border-slate-500/30 bg-slate-900/40 px-4 py-3">
                    <span>Fitness Level</span>
                    {visibleResult?.fitness_level ? (
                      <span className={fitnessBadgeClass[visibleResult.fitness_level] || 'badge border border-slate-300/30 bg-slate-500/20 text-slate-200'}>
                        {visibleResult.fitness_level}
                      </span>
                    ) : (
                      <span className="text-slate-300">Available after daily entry</span>
                    )}
                  </div>
                </div>
              </section>

              <InsightsPanel insights={visibleResult?.insights} />

              <section className="glass rounded-2xl p-6 shadow-glass">
                <h3 className="mb-2 font-display text-lg font-semibold text-slate-100">Latest Input Snapshot</h3>
                <p className="text-sm text-slate-300">
                  Steps: {numericValues.steps} | Calories: {numericValues.calories} | Active Minutes: {numericValues.activity}
                </p>
              </section>
            </div>
          </section>
        )}

        {user ? <DataScienceDashboard data={analytics} loading={analyticsLoading} error={analyticsError} /> : null}

        {error ? (
          <div className="mt-4 flex items-start gap-2 rounded-xl border border-rose-400/30 bg-rose-500/10 p-3 text-sm text-rose-200">
            <AlertTriangle size={16} className="mt-0.5" />
            <span>{error}</span>
          </div>
        ) : null}
      </Motion.div>
    </main>
  )
}

export default App
