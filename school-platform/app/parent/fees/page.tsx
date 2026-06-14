export default function Fees() {
  return (
    <div className="max-w-xl">
      <h2 className="text-4xl tracking-tight font-semibold mb-9">School Fees</h2>
      
      <div className="bg-white border rounded-3xl p-8">
        <div className="flex justify-between mb-8">
          <div>
            <div className="text-sm text-gray-500">Current Balance</div>
            <div className="text-5xl font-semibold tracking-tighter">UGX 420,000</div>
          </div>
          <div className="text-right text-sm">
            <div>Due Date</div>
            <div className="font-medium">15 March 2026</div>
          </div>
        </div>

        <button className="w-full py-4 rounded-2xl bg-[#0a5c36] text-white font-medium">
          Pay Now (MTN / Airtel / Bank)
        </button>

        <div className="mt-8 text-xs text-gray-500">
          Payment history available in your account. All transactions are secured.
        </div>
      </div>
    </div>
  );
}
