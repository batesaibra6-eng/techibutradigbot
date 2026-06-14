import Link from 'next/link';

export default function TeacherDashboard() {
  return (
    <div>
      <h1 className="text-5xl tracking-[-1.5px] font-semibold">Good morning, Mr. Okello.</h1>
      <p className="text-gray-600 mt-2">Senior 5 Science • Class Teacher</p>

      <div className="grid md:grid-cols-4 gap-5 mt-10">
        {[
          { label: "Total Students", value: "84" },
          { label: "Classes Today", value: "5" },
          { label: "Pending Marks", value: "42" },
          { label: "Assignments", value: "12" },
        ].map((item, i) => (
          <div key={i} className="bg-white border p-7 rounded-3xl">
            <div className="text-5xl tracking-tight font-semibold">{item.value}</div>
            <div className="text-sm mt-1 text-gray-600">{item.label}</div>
          </div>
        ))}
      </div>

      <div className="mt-10">
        <Link href="/teacher/marks" className="inline-block px-8 py-4 rounded-2xl bg-[#0a5c36] text-white font-medium">Enter Mid-term Marks →</Link>
      </div>
    </div>
  );
}
