export default function Announcements() {
  return (
    <div>
      <h2 className="text-4xl tracking-tight font-semibold mb-8">School Announcements</h2>
      <div className="space-y-5">
        {[
          { title: "Mid-term break schedule", date: "Feb 12, 2026", body: "School will be closed from 20th – 24th February for mid-term break." },
          { title: "Science Fair 2026", date: "Feb 8, 2026", body: "All S5 and S6 students are required to submit project proposals by Friday." },
        ].map((ann, i) => (
          <div key={i} className="bg-white border p-8 rounded-3xl">
            <div className="font-semibold text-lg">{ann.title}</div>
            <div className="text-xs text-gray-500 mt-1">{ann.date}</div>
            <p className="mt-4 text-gray-600">{ann.body}</p>
          </div>
        ))}
      </div>
    </div>
  );
}
