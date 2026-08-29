export default function RuntimeModelCard({ icon: Icon, label, value }) {
  const displayValue = value || 'Unavailable';

  return (
    <div className="rounded-md border border-sidebar-border bg-sidebar-accent p-3">
      <div className="flex items-center gap-2 text-sidebar-foreground/70">
        <Icon className="h-3.5 w-3.5 shrink-0" />
        <span className="text-[10px] font-semibold uppercase tracking-wider">{label}</span>
      </div>
      <p
        className="mt-1.5 truncate text-xs font-medium text-sidebar-accent-foreground"
        title={displayValue}
      >
        {displayValue}
      </p>
    </div>
  );
}
