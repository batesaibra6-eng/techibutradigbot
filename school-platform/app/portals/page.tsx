import Link from 'next/link';

export default function Portals() {
  const portals = [
    {
      title: "Student Portal",
      description: "Access your results, assignments, attendance, timetable, and learning materials.",
      icon: "🎓",
      href: "/student",
      color: "bg-blue-600"
    },
    {
      title: "Parent Portal",
      description: "Monitor your child's performance, pay fees, and communicate with teachers.",
      icon: "👨‍👩‍👧",
      href: "/parent",
      color: "bg-emerald-600"
    },
    {
      title: "Teacher Portal",
      description: "Manage classes, upload marks, take attendance, and access teaching resources.",
      icon: "📚",
      href: "/teacher",
      color: "bg-amber-600"
    },
    {
      title: "Head Teacher",
      description: "School-wide analytics, staff oversight, and strategic management dashboard.",
      icon: "🏫",
      href: "/headteacher",
      color: "bg-purple-700"
    },
    {
      title: "Admissions Office",
      description: "Process applications, schedule interviews, and manage new student enrollment.",
      icon: "📝",
      href: "/admissions",
      color: "bg-rose-600"
    },
    {
      title: "Finance Portal",
      description: "Fee management, billing, payments, and financial reporting.",
      icon: "💰",
      href: "/finance",
      color: "bg-teal-700"
    }
  ];

  return (
    <div className="min-h-screen bg-zinc-950 text-white">
      <nav className="border-b border-white/10">
        <div className="max-w-6xl mx-auto px-6 h-20 flex items-center justify-between">
          <Link href="/" className="flex items-center gap-3 text-white">
            <div className="w-9 h-9 bg-white rounded-full flex items-center justify-center">
              <span className="text-[#0a5c36] font-bold text-xl">ML</span>
            </div>
            <span className="font-semibold">Mayuge Light</span>
          </Link>
          <Link href="/" className="text-sm text-white/70 hover:text-white">← Back to Website</Link>
        </div>
      </nav>

      <div className="max-w-5xl mx-auto px-6 pt-16 pb-24">
        <div className="max-w-2xl">
          <div className="text-[#c5a14a] tracking-[3px] text-sm">SECURE ACCESS</div>
          <h1 className="text-7xl tracking-[-3px] font-semibold mt-3 mb-4">School Portals</h1>
          <p className="text-xl text-white/70">Access your personalized dashboard based on your role.</p>
        </div>

        <div className="mt-16 grid md:grid-cols-2 gap-4">
          {portals.map((portal, index) => (
            <Link 
              key={index} 
              href={portal.href}
              className="portal-card group block border border-white/10 bg-zinc-900 rounded-3xl p-8 hover:border-white/30"
            >
              <div className="text-5xl mb-8 opacity-80">{portal.icon}</div>
              <div className="font-semibold text-3xl tracking-tight mb-3">{portal.title}</div>
              <p className="text-white/60 text-[15px] leading-snug pr-4">{portal.description}</p>
              <div className="mt-8 inline-flex items-center text-sm font-medium text-[#c5a14a] group-hover:gap-2 transition-all">
                Access Portal <span className="ml-1 transition">→</span>
              </div>
            </Link>
          ))}
        </div>

        <div className="mt-20 pt-8 border-t border-white/10 text-center text-xs text-white/50">
          All portals use multi-factor authentication. Contact the ICT office for account assistance.
        </div>
      </div>
    </div>
  );
}
