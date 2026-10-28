export default function InputField({
  label,
  name,
  value,
  onChange,
  placeholder,
  icon: Icon,
  type = 'number',
  min,
  step,
  required = true,
}) {
  return (
    <label className="block">
      <span className="mb-2 flex items-center gap-2 text-sm font-medium text-slate-200">
        {Icon ? <Icon size={16} className="text-cyan-300" /> : null}
        {label}
      </span>
      <input
        name={name}
        value={value}
        onChange={onChange}
        required={required}
        type={type}
        min={min}
        step={step}
        placeholder={placeholder}
        className="w-full rounded-xl border border-slate-500/35 bg-slate-900/55 px-4 py-3 text-slate-100 outline-none transition focus:border-cyan-300/80 focus:ring-2 focus:ring-cyan-400/20"
      />
    </label>
  )
}
