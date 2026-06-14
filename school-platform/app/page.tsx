import Link from 'next/link';

export default function MayugeLightSchool() {
  return (
    <div className="min-h-screen bg-white">
      {/* Navigation */}
      <nav className="fixed top-0 left-0 right-0 z-50 bg-white/95 backdrop-blur-lg border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-6 flex items-center justify-between h-20">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 bg-[#0a5c36] rounded-full flex items-center justify-center">
              <span className="text-white font-bold text-xl">ML</span>
            </div>
            <div>
              <div className="font-semibold text-xl tracking-tight">Mayuge Light</div>
              <div className="text-[10px] text-gray-500 -mt-1">SECONDARY SCHOOL</div>
            </div>
          </div>

          <div className="hidden md:flex items-center gap-9 text-sm font-medium">
            <a href="#about" className="nav-link text-gray-700">About</a>
            <a href="#academics" className="nav-link text-gray-700">Academics</a>
            <a href="#admissions" className="nav-link text-gray-700">Admissions</a>
            <a href="#gallery" className="nav-link text-gray-700">Gallery</a>
            <a href="#contact" className="nav-link text-gray-700">Contact</a>
          </div>

          <div className="flex items-center gap-3">
            <Link 
              href="/portals" 
              className="px-5 py-2.5 text-sm font-semibold rounded-full border border-[#0a5c36] text-[#0a5c36] hover:bg-[#0a5c36] hover:text-white transition-colors"
            >
              Portals
            </Link>
            <Link 
              href="/apply" 
              className="px-6 py-2.5 text-sm font-semibold rounded-full bg-[#0a5c36] text-white hover:bg-[#084a2b] transition-colors"
            >
              Apply Now
            </Link>
          </div>
        </div>
      </nav>

      {/* Hero Section */}
      <section className="school-hero h-[100dvh] flex items-center justify-center pt-20">
        <div className="max-w-5xl mx-auto px-6 text-center text-white">
          <div className="inline-block px-4 py-1.5 rounded-full bg-white/10 backdrop-blur text-sm mb-6 tracking-[3px]">
            EST. 2006 • MAYUGE, UGANDA
          </div>
          <h1 className="text-7xl md:text-8xl font-semibold tracking-tighter leading-none mb-6">
            MAYUGE LIGHT<br />SECONDARY SCHOOL
          </h1>
          <p className="max-w-md mx-auto text-xl text-white/90 mb-10">
            Nurturing Excellence.<br />Building Futures.
          </p>
          <div className="flex flex-col sm:flex-row gap-4 justify-center">
            <Link 
              href="/apply" 
              className="px-10 py-4 rounded-full bg-white text-[#0a5c36] font-semibold text-lg hover:bg-white/90 transition-all active:scale-[0.985]"
            >
              Begin Your Journey
            </Link>
            <a 
              href="#about" 
              className="px-10 py-4 rounded-full border-2 border-white/70 hover:bg-white/10 font-semibold text-lg transition-all"
            >
              Learn More
            </a>
          </div>
        </div>
      </section>

      {/* Trust Bar */}
      <div className="bg-[#0f172a] py-5">
        <div className="max-w-6xl mx-auto px-6 flex flex-wrap justify-center items-center gap-x-12 gap-y-4 text-white/70 text-sm tracking-widest">
          <div>UGANDA NATIONAL EXAMINATIONS BOARD</div>
          <div>REGISTERED • UNEB 1306</div>
          <div>MINISTRY OF EDUCATION &amp; SPORTS</div>
        </div>
      </div>

      {/* About Section */}
      <section id="about" className="max-w-6xl mx-auto px-6 pt-24 pb-20">
        <div className="grid md:grid-cols-12 gap-x-12 gap-y-10 items-center">
          <div className="md:col-span-7">
            <div className="uppercase tracking-[4px] text-xs font-medium text-[#0a5c36] mb-3">OUR STORY</div>
            <h2 className="text-6xl tracking-[-2.5px] font-semibold leading-none mb-8">A beacon of excellence in Eastern Uganda.</h2>
            <div className="space-y-5 text-[17px] text-gray-600 max-w-2xl">
              <p>Mayuge Light Secondary School was founded with a clear mission: to deliver world-class secondary education that prepares young Ugandans for success in higher education and beyond.</p>
              <p>Today, we proudly serve over 1,200 students across O-Level and A-Level, supported by a dedicated team of 60+ qualified teachers and staff.</p>
            </div>
          </div>
          <div className="md:col-span-5">
            <div className="bg-zinc-100 p-9 rounded-3xl">
              <div className="grid grid-cols-2 gap-8">
                <div>
                  <div className="font-mono text-5xl font-semibold text-[#0a5c36] tracking-tighter">1,200+</div>
                  <div className="text-sm mt-1 text-gray-600">Students</div>
                </div>
                <div>
                  <div className="font-mono text-5xl font-semibold text-[#0a5c36] tracking-tighter">60+</div>
                  <div className="text-sm mt-1 text-gray-600">Qualified Teachers</div>
                </div>
                <div>
                  <div className="font-mono text-5xl font-semibold text-[#0a5c36] tracking-tighter">96%</div>
                  <div className="text-sm mt-1 text-gray-600">UNEB Pass Rate</div>
                </div>
                <div>
                  <div className="font-mono text-5xl font-semibold text-[#0a5c36] tracking-tighter">18</div>
                  <div className="text-sm mt-1 text-gray-600">Years of Excellence</div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Academics */}
      <section id="academics" className="bg-zinc-50 py-20">
        <div className="max-w-6xl mx-auto px-6">
          <div className="text-center mb-14">
            <div className="text-xs tracking-[4px] text-[#0a5c36] mb-3 font-medium">ACADEMIC PROGRAMS</div>
            <h3 className="text-6xl tracking-[-2px] font-semibold">O-Level &amp; A-Level Excellence</h3>
          </div>

          <div className="grid md:grid-cols-2 gap-6">
            {/* O-Level Card */}
            <div className="bg-white rounded-3xl p-9 border border-gray-100">
              <div className="uppercase text-xs tracking-[2px] text-[#c5a14a] mb-3">SENIOR 1 — SENIOR 4</div>
              <h4 className="text-4xl tracking-tight font-semibold mb-4">Ordinary Level (O-Level)</h4>
              <p className="text-gray-600 mb-8">Comprehensive curriculum covering Sciences, Arts, and Languages. Students prepare for UNEB UCE examinations.</p>
              <div className="flex flex-wrap gap-2">
                {['Mathematics', 'Physics', 'Chemistry', 'Biology', 'English', 'History', 'Geography', 'Literature'].map(subject => (
                  <span key={subject} className="px-4 py-1 text-sm bg-gray-100 rounded-full">{subject}</span>
                ))}
              </div>
            </div>

            {/* A-Level Card */}
            <div className="bg-[#0f172a] text-white rounded-3xl p-9">
              <div className="uppercase text-xs tracking-[2px] text-[#c5a14a] mb-3">SENIOR 5 — SENIOR 6</div>
              <h4 className="text-4xl tracking-tight font-semibold mb-4">Advanced Level (A-Level)</h4>
              <p className="text-white/80 mb-8">Specialized streams in Sciences, Arts, and Business. Students sit for UNEB UACE examinations.</p>
              <div className="flex flex-wrap gap-2">
                {['PCB', 'PCM', 'BAM', 'HEG', 'LEG', 'Arts', 'Sciences'].map(stream => (
                  <span key={stream} className="px-4 py-1 text-sm bg-white/10 rounded-full">{stream}</span>
                ))}
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Admissions CTA */}
      <section id="admissions" className="max-w-5xl mx-auto px-6 py-24 text-center">
        <div className="max-w-xl mx-auto">
          <div className="text-[#0a5c36] text-xs tracking-[4px] mb-4 font-medium">NEW STUDENTS WELCOME</div>
          <h2 className="text-6xl tracking-[-2px] font-semibold mb-6">Ready to join the Mayuge Light family?</h2>
          <p className="text-xl text-gray-600 mb-9">Applications for the 2026 academic year are now open. Secure your child&apos;s future today.</p>
          <Link href="/apply" className="inline-block px-12 py-4 rounded-full bg-[#0a5c36] text-white text-lg font-semibold hover:bg-[#084a2b] active:scale-[0.985] transition-all">
            Start Application →
          </Link>
          <div className="mt-6 text-sm text-gray-500">Application deadline: 31st January 2026</div>
        </div>
      </section>

      {/* Gallery */}
      <section id="gallery" className="bg-zinc-900 py-20 text-white">
        <div className="max-w-6xl mx-auto px-6">
          <div className="flex justify-between items-end mb-9">
            <div>
              <div className="uppercase tracking-[3px] text-xs text-[#c5a14a]">LIFE AT MAYUGE LIGHT</div>
              <h3 className="text-white text-5xl tracking-[-1.5px] font-semibold mt-2">Campus &amp; Community</h3>
            </div>
            <Link href="/gallery" className="text-sm font-medium hover:text-[#c5a14a] transition-colors hidden md:block">VIEW FULL GALLERY →</Link>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-4">
              {[
              { src: '/uploads/studnts.jpeg', alt: 'Students in uniform' },
              { src: '/uploads/compund view.jpg', alt: 'School compound' },
              { src: '/uploads/choir members.jpeg', alt: 'School choir' },
              { src: '/uploads/gate.jpg', alt: 'School gate' },
              { src: '/uploads/a level student.jpg', alt: 'A-Level student' },
              { src: '/uploads/compound 2.jpg', alt: 'Campus view' },
            ].map((img, idx) => (
              <div key={idx} className="overflow-hidden rounded-2xl aspect-[16/10] relative group">
                <img 
                  src={img.src} 
                  alt={img.alt} 
                  className="gallery-img w-full h-full object-cover" 
                />
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Contact */}
      <section id="contact" className="max-w-4xl mx-auto px-6 py-24 text-center">
        <div className="text-xs tracking-[3px] text-[#0a5c36]">GET IN TOUCH</div>
        <h3 className="text-6xl tracking-[-2px] font-semibold mt-3 mb-8">We&apos;re here to help.</h3>
        
        <div className="grid md:grid-cols-3 gap-8 text-left max-w-3xl mx-auto mt-10">
          <div>
            <div className="font-semibold mb-1">Address</div>
            <div className="text-gray-600">Mayuge Light Secondary School<br />P.O. Box 1306, Mayuge<br />Uganda</div>
          </div>
          <div>
            <div className="font-semibold mb-1">Phone</div>
            <div className="text-gray-600">+256 774 277 212<br />+256 757 136 280</div>
          </div>
          <div>
            <div className="font-semibold mb-1">Email</div>
            <div className="text-gray-600">info@mayugelight.ac.ug<br />admissions@mayugelight.ac.ug</div>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="bg-[#0f172a] text-white/70 py-12 border-t border-white/10">
        <div className="max-w-6xl mx-auto px-6 flex flex-col md:flex-row justify-between items-center gap-4 text-sm">
          <div>© {new Date().getFullYear()} Mayuge Light Secondary School. All Rights Reserved.</div>
          <div className="flex gap-8">
            <Link href="/privacy" className="hover:text-white">Privacy</Link>
            <Link href="/terms" className="hover:text-white">Terms</Link>
            <Link href="/portals" className="hover:text-white">Staff &amp; Student Portals</Link>
          </div>
        </div>
      </footer>
    </div>
  );
}
