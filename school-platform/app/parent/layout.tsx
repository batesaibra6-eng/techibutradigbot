import Link from 'next/link';

export default function ParentLayout({ children }: { children: React.ReactNode }) {
  return (
    <div className="min-h-screen bg-zinc-50">
      <nav className="bg-white border-b sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-6 h-16 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 bg-[#0a5c36] rounded-full flex items-center justify-center">
              <span className="text-white text-sm font-bold">ML</span>
            </div>
            <div className="font-semibold">Mayuge Light • Parent Portal</div>
          </div>
          <div className="flex items-center gap-4 text-sm">
            <div className="text-gray-600">Mrs. Nakato Florence</div>
            <Link href="/" className="text-xs px-4 py-1.5 rounded-full border hover:bg-gray-50">Logout</Link>
          </div>
        </div>
      </nav>

      <div className="max-w-7xl mx-auto px-6 flex">
        <div className="w-60 py-8 pr-8 hidden lg:block">
          <div className="space-y-1 text-sm">
            {[
              { label: "Dashboard", href: "/parent" },
              { label: "Child's Performance", href: "/parent/performance" },
              { label: "Attendance", href: "/parent/attendance" },
              { label: "Fees & Payments", href: "/parent/fees" },
              { label: "Messages", href: "/parent/messages" },
              { label: "Report Cards", href: "/parent/reports" },
            ].map((item, i) => (
              <Link key={i} href={item.href} className="block px-4 py-2.5 rounded-xl hover:bg-white hover:shadow-sm transition-all text-gray-700">
                {item.label}
              </Link>
            ))}
          </div>
        </div>
        <div className="flex-1 py-8">{children}</div>
      </div>
    </div>
  );
}
