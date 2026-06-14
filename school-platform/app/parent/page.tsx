import Link from 'next/link';

export default function ParentDashboard() {
  return (
    <div>
      <div className="mb-10">
        <div className="text-xs tracking-[2px] text-[#0a5c36]">PARENT DASHBOARD</div>
        <h1 className="text-5xl tracking-[-1.5px] font-semibold mt-1">Hello, Mrs. Nakato.</h1>
        <p className="text-lg text-gray-600 mt-2">Monitoring: <span className="font-medium text-black">Nakato Sarah (S5 PCB)</span></p>
      </div>

      <div className="grid md:grid-cols-3 gap-5">
        <div className="bg-white border p-7 rounded-3xl">
          <div className="text-sm text-gray-500">Current Term Average</div>
          <div className="text-6xl font-semibold tracking-tighter mt-1">78%</div>
          <div className="text-emerald-600 text-sm mt-1">↑ 4% from last term</div>
        </div>
        
        <div className="bg-white border p-7 rounded-3xl">
          <div className="text-sm text-gray-500">Attendance</div>
          <div className="text-6xl font-semibold tracking-tighter mt-1">94%</div>
          <div className="text-xs mt-1">2 absences this term</div>
        </div>

        <div className="bg-white border p-7 rounded-3xl">
          <div className="text-sm text-gray-500">Fees Balance</div>
          <div className="text-5xl font-semibold tracking-tighter mt-1 text-orange-600">UGX 420,000</div>
          <Link href="/parent/fees" className="text-xs mt-2 inline-block text-[#0a5c36]">Pay now →</Link>
        </div>
      </div>

      <div className="mt-8 grid md:grid-cols-2 gap-5">
        <Link href="/parent/performance" className="block bg-white border p-7 rounded-3xl hover:shadow-sm">
          <div className="font-semibold mb-1">View Academic Performance</div>
          <div className="text-sm text-gray-500">Mid-term results and subject breakdown</div>
        </Link>
        <Link href="/parent/fees" className="block bg-white border p-7 rounded-3xl hover:shadow-sm">
          <div className="font-semibold mb-1">Pay School Fees</div>
          <div className="text-sm text-gray-500">Mobile Money • Bank • Card</div>
        </Link>
      </div>
    </div>
  );
}
