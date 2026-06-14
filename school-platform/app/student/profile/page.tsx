export default function Profile() {
  return (
    <div className="max-w-2xl">
      <h2 className="text-4xl tracking-tight font-semibold mb-8">My Profile</h2>
      
      <div className="bg-white border rounded-3xl p-9">
        <div className="flex items-center gap-6">
          <div className="w-24 h-24 rounded-2xl overflow-hidden border">
            <img src="/uploads/a level student girl.jpg" alt="Profile photo" className="w-full h-full object-cover" />
          </div>
          <div>
            <div className="text-3xl font-semibold">Nakato Sarah</div>
            <div className="text-gray-500">Senior 5 • Science (PCB)</div>
            <div className="text-sm mt-1 text-[#0a5c36]">Student ID: ML-2023-0847</div>
          </div>
        </div>

        <div className="mt-10 grid grid-cols-2 gap-y-8 text-sm">
          <div><span className="text-gray-500">Date of Birth</span><br />14 March 2008</div>
          <div><span className="text-gray-500">Gender</span><br />Female</div>
          <div><span className="text-gray-500">Class Teacher</span><br />Mr. Okello James</div>
          <div><span className="text-gray-500">House</span><br />Nile House</div>
          <div><span className="text-gray-500">Parent / Guardian</span><br />Mrs. Nakato Florence</div>
          <div><span className="text-gray-500">Contact</span><br />+256 772 456 891</div>
        </div>
      </div>
    </div>
  );
}
