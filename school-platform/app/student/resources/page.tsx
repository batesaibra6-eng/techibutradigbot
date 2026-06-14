export default function Resources() {
  return (
    <div>
      <h2 className="text-4xl font-semibold tracking-tight mb-8">Learning Resources</h2>
      
      <div className="grid md:grid-cols-2 gap-4">
        {[
          { subject: "Advanced Biology", title: "Photosynthesis Notes", type: "PDF" },
          { subject: "Mathematics", title: "Integration Practice Questions", type: "PDF" },
          { subject: "Chemistry", title: "Organic Chemistry Video Lecture", type: "Video" },
          { subject: "Physics", title: "Mechanics Past Paper 2024", type: "PDF" },
        ].map((res, idx) => (
          <div key={idx} className="flex justify-between bg-white border px-7 py-6 rounded-3xl items-center">
            <div>
              <div className="font-medium">{res.title}</div>
              <div className="text-xs text-gray-500 mt-px">{res.subject}</div>
            </div>
            <button className="text-xs px-5 py-2 rounded-full border hover:bg-gray-50">Download</button>
          </div>
        ))}
      </div>
    </div>
  );
}
