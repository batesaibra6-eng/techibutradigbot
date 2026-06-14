export default function Assignments() {
  return (
    <div>
      <h2 className="text-4xl tracking-tight font-semibold mb-9">Assignments</h2>
      
      <div className="space-y-4">
        {[
          { title: "Photosynthesis Lab Report", subject: "Advanced Biology", due: "Feb 15", status: "Pending" },
          { title: "Calculus Worksheet", subject: "Mathematics", due: "Feb 18", status: "Submitted" },
          { title: "Organic Compounds Essay", subject: "Chemistry", due: "Feb 20", status: "Pending" },
        ].map((a, idx) => (
          <div key={idx} className="flex items-center justify-between bg-white border px-8 py-6 rounded-3xl">
            <div>
              <div className="font-medium">{a.title}</div>
              <div className="text-sm text-gray-500">{a.subject}</div>
            </div>
            <div className="flex items-center gap-4 text-sm">
              <div className="text-right">
                <div>Due: {a.due}</div>
                <div className={a.status === "Submitted" ? "text-emerald-600" : "text-orange-600"}>{a.status}</div>
              </div>
              <button className="px-5 py-2 rounded-full border text-xs">View / Submit</button>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
