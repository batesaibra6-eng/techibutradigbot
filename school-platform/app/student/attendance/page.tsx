export default function Attendance() {
  return (
    <div>
      <h2 className="text-4xl font-semibold tracking-tight mb-9">Attendance Record</h2>
      
      <div className="bg-white rounded-3xl border p-9">
        <div className="flex items-center justify-between mb-8">
          <div>
            <div className="font-medium">Term 1 • 2026</div>
            <div className="text-sm text-gray-500">94% overall attendance</div>
          </div>
          <div className="text-right text-sm">
            <div className="font-mono text-4xl font-semibold text-emerald-600">94</div>
            <div className="text-xs text-gray-500 -mt-1">DAYS PRESENT</div>
          </div>
        </div>

        <div className="space-y-px text-sm">
          {[
            { date: "Mon 10 Feb", status: "Present" },
            { date: "Tue 11 Feb", status: "Present" },
            { date: "Wed 12 Feb", status: "Present" },
            { date: "Thu 13 Feb", status: "Absent (Sick)" },
            { date: "Fri 14 Feb", status: "Present" },
          ].map((day, idx) => (
            <div key={idx} className="flex justify-between py-3 px-4 border-b last:border-none">
              <div>{day.date}</div>
              <div className={day.status.includes("Absent") ? "text-red-600" : "text-emerald-600"}>{day.status}</div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
