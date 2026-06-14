import Link from 'next/link';

export default function StudentDashboard() {
  return (
    <div>
      <div className="mb-10">
        <div className="text-xs tracking-[2px] text-[#0a5c36]">SENIOR 5 • SCIENCE STREAM</div>
        <h1 className="text-5xl tracking-[-1.5px] font-semibold mt-1">Good morning, Nakato.</h1>
      </div>

      {/* Quick Stats */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-10">
        {[
          { label: "Attendance Rate", value: "94%", sub: "This term" },
          { label: "Assignments Due", value: "3", sub: "This week" },
          { label: "Average Score", value: "78%", sub: "Mid-term exams" },
          { label: "Rank", value: "12", sub: "Out of 84 students" },
        ].map((stat, idx) => (
          <div key={idx} className="bg-white rounded-2xl p-6 border">
            <div className="text-4xl font-semibold tracking-tight">{stat.value}</div>
            <div className="text-sm text-gray-600 mt-1">{stat.label}</div>
            <div className="text-xs text-gray-400 mt-0.5">{stat.sub}</div>
          </div>
        ))}
      </div>

      <div className="grid md:grid-cols-2 gap-6">
        {/* Upcoming Assignments */}
        <div className="bg-white border rounded-3xl p-7">
          <div className="flex justify-between items-center mb-6">
            <div className="font-semibold">Upcoming Assignments</div>
            <Link href="/student/assignments" className="text-xs text-[#0a5c36]">View all →</Link>
          </div>
          <div className="space-y-4 text-sm">
            {[
              { subject: "Advanced Biology", title: "Photosynthesis Lab Report", due: "Tomorrow" },
              { subject: "Mathematics", title: "Calculus Worksheet", due: "Feb 18" },
              { subject: "Chemistry", title: "Organic Compounds Essay", due: "Feb 20" },
            ].map((a, i) => (
              <div key={i} className="flex justify-between items-center border-b pb-4 last:border-none last:pb-0">
                <div>
                  <div className="font-medium">{a.title}</div>
                  <div className="text-gray-500 text-xs">{a.subject}</div>
                </div>
                <div className="text-xs px-3 py-1 bg-orange-100 text-orange-700 rounded-full">{a.due}</div>
              </div>
            ))}
          </div>
        </div>

        {/* Recent Results */}
        <div className="bg-white border rounded-3xl p-7">
          <div className="flex justify-between items-center mb-6">
            <div className="font-semibold">Recent Exam Results</div>
            <Link href="/student/results" className="text-xs text-[#0a5c36]">View full report →</Link>
          </div>
          <div className="space-y-4 text-sm">
            {[
              { subject: "Physics", score: "82", grade: "B" },
              { subject: "Biology", score: "91", grade: "A" },
              { subject: "Mathematics", score: "67", grade: "C+" },
            ].map((r, i) => (
              <div key={i} className="flex justify-between items-center">
                <div>{r.subject}</div>
                <div className="font-mono font-medium">{r.score}% <span className="text-gray-400">({r.grade})</span></div>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Quick Links */}
      <div className="mt-6 grid grid-cols-2 md:grid-cols-4 gap-4">
        {[
          { label: "View Timetable", href: "/student/timetable" },
          { label: "Download Resources", href: "/student/resources" },
          { label: "Check Attendance", href: "/student/attendance" },
          { label: "School Announcements", href: "/student/announcements" },
        ].map((link, i) => (
          <Link key={i} href={link.href} className="block px-6 py-4 border bg-white rounded-2xl text-sm hover:bg-gray-50 transition-all">
            {link.label} →
          </Link>
        ))}
      </div>
    </div>
  );
}
