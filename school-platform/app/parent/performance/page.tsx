export default function Performance() {
  return (
    <div className="max-w-3xl">
      <h2 className="text-4xl tracking-tight font-semibold mb-8">Academic Performance</h2>
      <div className="bg-white border rounded-3xl p-8">
        <table className="w-full text-sm">
          <thead>
            <tr className="text-left border-b text-gray-500">
              <th className="py-3">Subject</th>
              <th>Mid-term</th>
              <th>End of Term</th>
              <th>Grade</th>
            </tr>
          </thead>
          <tbody>
            {[
              ["Advanced Mathematics", "78%", "—", "B+"],
              ["Advanced Biology", "91%", "—", "A"],
              ["Chemistry", "84%", "—", "A-"],
              ["Physics", "72%", "—", "B"],
            ].map((row, i) => (
              <tr key={i} className="border-b last:border-none">
                <td className="py-4">{row[0]}</td>
                <td>{row[1]}</td>
                <td className="text-gray-400">{row[2]}</td>
                <td className="font-medium">{row[3]}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
