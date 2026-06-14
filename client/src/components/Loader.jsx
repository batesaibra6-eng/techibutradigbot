/**
 * Full-screen or inline loading spinner shown while pages/data load.
 */
export default function Loader({ full = false }) {
  const spinner = (
    <div className="flex flex-col items-center justify-center gap-4">
      <div className="relative h-14 w-14">
        <div className="absolute inset-0 rounded-full border-4 border-navy-100" />
        <div className="absolute inset-0 animate-spin rounded-full border-4 border-transparent border-t-gold-500" />
      </div>
      <p className="text-sm font-medium text-navy-400">Loading…</p>
    </div>
  );

  if (full) {
    return (
      <div className="flex min-h-[60vh] items-center justify-center">
        {spinner}
      </div>
    );
  }
  return spinner;
}
