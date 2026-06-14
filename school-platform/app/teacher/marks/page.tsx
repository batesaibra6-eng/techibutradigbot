export default function MarksEntry() {
  return (
    <div>
      <h2 className="text-4xl tracking-tight font-semibold mb-8">Marks Entry — S5 PCB</h2>
      
      <div className="bg-white border rounded-3xl p-8">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b text-left text-gray-500">
              <th className="py-3">Student</th>
              <th>Maths</th>
              <th>Biology</th>
              <th>Chemistry</th>
              <th>Physics</th>
            </tr>
          </thead>
          <tbody>
            {["Nakato Sarah", "Kizito Brian", "Nambi Grace", "Muwanguzi Ivan"].map((name, i) => (
              <tr key={i} className="border-b">
                <td className="py-4 font-medium">{name}</td>
                <td><input type="text" className="w-16 border px-2 py-1 rounded" placeholder="78" /></td>
                <td><input type="text" className="w-16 border px-2 py-1 rounded" placeholder="91" /></td>
                <td><input type="text" className="w-16 border px-2 py-1 rounded" placeholder="84" /></td>
                <td><input type="text" className="w-16 border px-2 py-1 rounded" placeholder="72" /></td>
              </tr>
            ))}
          </tbody>
        </table>
        <button className="mt-8 px-8 py-3 bg-[#0a5c36] text-white rounded-2xl text-sm font-medium">Save All Marks</button>
      </div>
    </div>
  );
}
