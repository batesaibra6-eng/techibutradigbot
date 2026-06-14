export default function ParentAttendance() {
  return (
    <div>
      <h2 className="text-4xl font-semibold tracking-tight mb-8">Attendance Summary</h2>
      <div className="bg-white border rounded-3xl p-9 max-w-lg">
        <div className="text-7xl font-semibold tracking-tighter text-emerald-600">94%</div>
        <div className="mt-1 text-sm">Present this term</div>
        
        <div className="mt-8 text-sm space-y-3">
          <div className="flex justify-between"><span>Days Present</span> <span className="font-medium">94 days</span></div>
          <div className="flex justify-between"><span>Days Absent</span> <span className="font-medium">6 days</span></div>
        </div>
      </div>
    </div>
  );
}
