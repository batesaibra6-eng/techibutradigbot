import { Routes, Route } from "react-router-dom";
import { Suspense, lazy } from "react";

import Navbar from "./components/Navbar.jsx";
import Footer from "./components/Footer.jsx";
import ScrollProgress from "./components/ScrollProgress.jsx";
import Loader from "./components/Loader.jsx";
import NotFound from "./pages/NotFound.jsx";

// Lazy-load pages for code-splitting and faster initial load
const Home = lazy(() => import("./pages/Home.jsx"));
const About = lazy(() => import("./pages/About.jsx"));
const Academics = lazy(() => import("./pages/Academics.jsx"));
const Admissions = lazy(() => import("./pages/Admissions.jsx"));
const StudentLife = lazy(() => import("./pages/StudentLife.jsx"));
const News = lazy(() => import("./pages/News.jsx"));
const NewsDetail = lazy(() => import("./pages/NewsDetail.jsx"));
const Contact = lazy(() => import("./pages/Contact.jsx"));
const Admin = lazy(() => import("./pages/Admin.jsx"));

export default function App() {
  return (
    <div className="flex min-h-screen flex-col">
      <ScrollProgress />
      <Navbar />

      <main className="flex-1">
        <Suspense fallback={<Loader full />}>
          <Routes>
            <Route path="/" element={<Home />} />
            <Route path="/about" element={<About />} />
            <Route path="/academics" element={<Academics />} />
            <Route path="/admissions" element={<Admissions />} />
            <Route path="/student-life" element={<StudentLife />} />
            <Route path="/news" element={<News />} />
            <Route path="/news/:slug" element={<NewsDetail />} />
            <Route path="/contact" element={<Contact />} />
            <Route path="/admin" element={<Admin />} />
            <Route path="*" element={<NotFound />} />
          </Routes>
        </Suspense>
      </main>

      <Footer />
    </div>
  );
}
