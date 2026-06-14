export default function Results() {
  return (
    <div className="max-w-3xl">
      <div className="flex items-end justify-between mb-8">
        <h2 className="text-4xl font-semibold tracking-tight">Examination Results</h2>
        <button className="text-sm px-5 py-2 rounded-full border">Download Report Card</button>
      </div>

      <div className="bg-white border rounded-3xl p-8">
        <div className="font-medium mb-5">Mid-Term Examinations • February 2026</div>
        
        <table className="w-full text-sm">
          <thead>
            <tr className="text-left border-b text-gray-500">
              <th className="py-3">Subject</th>
              <th>Score</th>
              <th>Grade</th>
              <th>Position</th>
            </tr>
          </thead>
          <tbody>
            {[
              ["Advanced Mathematics", "78", "B+", "9/84"],
              ["Advanced Biology", "91", "A", "3/84"],
              ["Chemistry", "84", "A-", "5/84"],
              ["Physics", "72", "B", "18/84"],
              ["General Paper", "65", "C+", "31/84"],
            ].map((row, i) => (
              <tr key={i} className="border-b last:border-none">
                <td className="py-4 font-medium">{row[0]}</td>
                <td className="font-mono">{row[1]}%</td>
                <td className="font-semibold text-emerald-700">{row[2]}</td>
                <td>{row[3]}</td>
              </tr>
            ))}
          </tbody>
        </table>

        <div className="mt-8 pt-6 border-t text-sm flex items-center justify-between">
          <div>Overall Average: <span className="font-semibold">78%</span></div>
          <div>Class Position: <span className="font-semibold">12 / 84</span></div>
        </div>
      </div>
    </div>
  );
}
