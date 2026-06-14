export default function Timetable() {
  return (
    <div>
      <h2 className="text-4xl font-semibold tracking-tight mb-8">Weekly Timetable</h2>
      <div className="bg-white border rounded-3xl p-8 overflow-x-auto">
        <table className="min-w-full text-sm">
          <thead>
            <tr className="text-gray-500 border-b">
              <th className="py-3 text-left pr-8">Time</th>
              <th>Mon</th><th>Tue</th><th>Wed</th><th>Thu</th><th>Fri</th>
            </tr>
          </thead>
          <tbody>
            {[
              ["8:00 – 9:00", "Mathematics", "Biology", "Chemistry", "Physics", "GP"],
              ["9:00 – 10:00", "Biology", "Mathematics", "Physics", "Chemistry", "Mathematics"],
              ["10:30 – 11:30", "Chemistry", "Physics", "Biology", "Mathematics", "Chemistry"],
            ].map((row, i) => (
              <tr key={i} className="border-b">
                <td className="py-4 pr-8 text-gray-500">{row[0]}</td>
                {row.slice(1).map((cell, j) => <td key={j} className="font-medium">{cell}</td>)}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
