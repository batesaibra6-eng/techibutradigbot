import Link from 'next/link';

export default function Home() {
  return (
    <div className="min-h-screen bg-white">
      {/* Navbar */}
      <nav className="fixed top-0 w-full bg-white/95 backdrop-blur border-b z-50">
        <div className="max-w-7xl mx-auto px-6 flex items-center justify-between h-20">
          <div className="flex items-center gap-3">
            <div className="w-9 h-9 bg-[#0a5c36] rounded-full flex items-center justify-center">
              <span className="text-white font-bold">ML</span>
            </div>
            <span className="font-semibold text-xl">Mayuge Light</span>
          </div>

          <div className="hidden md:flex items-center gap-8 text-sm">
            <a href="#about" className="nav-link">About</a>
            <a href="#academics" className="nav-link">Academics</a>
            <a href="#admissions" className="nav-link">Admissions</a>
            <a href="#gallery" className="nav-link">Gallery</a>
          </div>

          <div className="flex items-center gap-3">
            <Link href="/portals" className="px-5 py-2 rounded-full border text-sm font-medium">
              Portals
            </Link>
            <Link href="/apply" className="px-5 py-2 rounded-full bg-[#0a5c36] text-white text-sm font-medium">
              Apply Now
            </Link>
          </div>
        </div>
      </nav>

      {/* Hero */}
      <section className="h-[100dvh] flex items-center justify-center bg-[linear-gradient(rgba(0,0,0,0.6),rgba(0,0,0,0.65))] bg-[url('/uploads/compund view.jpg')] bg-cover bg-center pt-16">
        <div className="text-center text-white px-6 max-w-4xl">
          <div className="text-sm tracking-[3px] mb-4">EST. 2006 • MAYUGE, UGANDA</div>
          <h1 className="text-7xl md:text-8xl font-semibold tracking-tighter mb-6">
            MAYUGE LIGHT<br />SECONDARY SCHOOL
          </h1>
          <p className="text-xl mb-10">Nurturing Excellence. Building Futures.</p>
          
          <div className="flex flex-col sm:flex-row gap-4 justify-center">
            <Link href="/apply" className="px-10 py-4 bg-white text-[#0a5c36] font-semibold rounded-full">
              Begin Your Journey
            </Link>
            <a href="#about" className="px-10 py-4 border border-white/70 rounded-full font-semibold">
              Learn More
            </a>
          </div>
        </div>
      </section>

      {/* About */}
      <section id="about" className="max-w-6xl mx-auto px-6 py-20">
        <div className="grid md:grid-cols-2 gap-12">
          <div>
            <div className="text-[#0a5c36] text-sm tracking-widest mb-2">OUR STORY</div>
            <h2 className="text-5xl tracking-tight font-semibold">A beacon of excellence in Eastern Uganda.</h2>
          </div>
          <div className="text-lg text-gray-600">
            Mayuge Light Secondary School delivers world-class education to over 1,200 students across O-Level and A-Level.
          </div>
        </div>
      </section>

      {/* Academics */}
      <section id="academics" className="bg-zinc-50 py-16">
        <div className="max-w-6xl mx-auto px-6">
          <h3 className="text-center text-4xl font-semibold mb-10">O-Level &amp; A-Level Excellence</h3>
          <div className="grid md:grid-cols-2 gap-6">
            <div className="bg-white p-8 rounded-3xl border">
              <h4 className="font-semibold text-2xl">Ordinary Level (S1–S4)</h4>
              <p className="mt-3 text-gray-600">Comprehensive curriculum with strong focus on sciences and arts.</p>
            </div>
            <div className="bg-[#0f172a] text-white p-8 rounded-3xl">
              <h4 className="font-semibold text-2xl">Advanced Level (S5–S6)</h4>
              <p className="mt-3 text-white/80">Specialized streams in Sciences, Arts, and Business.</p>
            </div>
          </div>
        </div>
      </section>

      {/* Admissions */}
      <section id="admissions" className="max-w-3xl mx-auto px-6 py-20 text-center">
        <h2 className="text-5xl font-semibold tracking-tight">Ready to join Mayuge Light?</h2>
        <p className="mt-4 text-lg text-gray-600">Applications for 2026 are now open.</p>
        <Link href="/apply" className="inline-block mt-8 px-10 py-4 bg-[#0a5c36] text-white rounded-full font-semibold">
          Start Application
        </Link>
      </section>

      {/* Gallery */}
      <section id="gallery" className="bg-zinc-900 py-16 text-white">
        <div className="max-w-6xl mx-auto px-6">
          <h3 className="text-4xl font-semibold mb-8">Campus Life</h3>
          <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
            {[
              '/uploads/studnts.jpeg',
              '/uploads/compund view.jpg',
              '/uploads/choir members.jpeg',
              '/uploads/gate.jpg',
              '/uploads/a level student.jpg',
              '/uploads/compound 2.jpg',
            ].map((src, i) => (
              <img key={i} src={src} className="rounded-2xl aspect-video object-cover" alt="" />
            ))}
          </div>
        </div>
      </section>

      <footer className="border-t py-10 text-center text-sm text-gray-500">
        © 2026 Mayuge Light Secondary School
      </footer>
    </div>
  );
}
