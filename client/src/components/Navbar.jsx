import { useState, useEffect } from "react";
import { Link, NavLink, useLocation } from "react-router-dom";
import { motion, AnimatePresence } from "framer-motion";
import { FiChevronDown, FiMenu, FiX, FiPhone } from "react-icons/fi";
import { SCHOOL } from "../data/school.js";

/**
 * Sticky navigation bar with a dropdown menu, active-link highlighting,
 * scroll-aware styling, and a fully responsive mobile drawer.
 */
const navLinks = [
  { to: "/", label: "Home" },
  { to: "/about", label: "About" },
  {
    to: "/academics",
    label: "Academics",
    children: [
      { to: "/academics", label: "Subjects & Departments" },
      { to: "/academics", label: "Academic Calendar", hash: "#calendar" },
      { to: "/academics", label: "Performance", hash: "#performance" },
    ],
  },
  {
    to: "/student-life",
    label: "Student Life",
    children: [
      { to: "/student-life", label: "Clubs & Societies" },
      { to: "/student-life", label: "Sports", hash: "#sports" },
      { to: "/student-life", label: "Gallery", hash: "#gallery" },
    ],
  },
  { to: "/news", label: "News" },
  { to: "/contact", label: "Contact" },
];

export default function Navbar() {
  const [scrolled, setScrolled] = useState(false);
  const [mobileOpen, setMobileOpen] = useState(false);
  const [openDropdown, setOpenDropdown] = useState(null);
  const location = useLocation();

  // Detect scroll to add a solid background after leaving the hero
  useEffect(() => {
    const onScroll = () => setScrolled(window.scrollY > 30);
    window.addEventListener("scroll", onScroll);
    return () => window.removeEventListener("scroll", onScroll);
  }, []);

  // Close the mobile drawer on route change
  useEffect(() => {
    setMobileOpen(false);
    setOpenDropdown(null);
  }, [location]);

  return (
    <>
      {/* Top utility bar */}
      <div className="hidden bg-navy-950 text-navy-200 lg:block">
        <div className="container-custom flex h-9 items-center justify-between text-xs">
          <div className="flex items-center gap-6">
            <span className="flex items-center gap-1.5">
              <FiPhone className="text-gold-400" /> {SCHOOL.phone}
            </span>
            <span>{SCHOOL.email}</span>
          </div>
          <div className="flex items-center gap-2">
            <span className="italic text-gold-400">"{SCHOOL.motto}"</span>
          </div>
        </div>
      </div>

      {/* Main navbar */}
      <header
        className={`sticky top-0 z-50 w-full transition-all duration-300 ${
          scrolled
            ? "bg-white/95 shadow-soft backdrop-blur"
            : "bg-white shadow-sm"
        }`}
      >
        <nav className="container-custom flex h-16 items-center justify-between lg:h-20">
          {/* Logo */}
          <Link to="/" className="flex items-center gap-3">
            <img
              src="/images/logo.png"
              alt="Mayuge Light SS logo"
              className="h-10 w-10 rounded-full object-cover ring-2 ring-gold-300 lg:h-12 lg:w-12"
            />
            <div className="leading-tight">
              <span className="block font-display text-base font-bold text-navy-900 lg:text-lg">
                Mayuge Light
              </span>
              <span className="block text-[10px] font-medium uppercase tracking-widest text-gold-600 lg:text-xs">
                Secondary School
              </span>
            </div>
          </Link>

          {/* Desktop links */}
          <ul className="hidden items-center gap-1 lg:flex">
            {navLinks.map((link) => (
              <li
                key={link.label}
                className="relative"
                onMouseEnter={() => link.children && setOpenDropdown(link.label)}
                onMouseLeave={() => setOpenDropdown(null)}
              >
                <NavLink
                  to={link.to}
                  className={({ isActive }) =>
                    `nav-link px-3 py-2 ${
                      isActive
                        ? "text-gold-600 after:absolute after:bottom-0 after:left-3 after:right-3 after:h-0.5 after:rounded-full after:bg-gold-500"
                        : ""
                    }`
                  }
                >
                  {link.label}
                  {link.children && <FiChevronDown className="ml-0.5 inline" />}
                </NavLink>

                {/* Dropdown */}
                {link.children && (
                  <AnimatePresence>
                    {openDropdown === link.label && (
                      <motion.ul
                        initial={{ opacity: 0, y: 10 }}
                        animate={{ opacity: 1, y: 0 }}
                        exit={{ opacity: 0, y: 10 }}
                        transition={{ duration: 0.2 }}
                        className="absolute left-0 top-full w-60 overflow-hidden rounded-xl bg-white p-2 shadow-card ring-1 ring-navy-100"
                      >
                        {link.children.map((child) => (
                          <li key={child.label}>
                            <Link
                              to={child.to + (child.hash || "")}
                              className="block rounded-lg px-4 py-2.5 text-sm text-navy-700 transition-colors hover:bg-navy-50 hover:text-gold-600"
                            >
                              {child.label}
                            </Link>
                          </li>
                        ))}
                      </motion.ul>
                    )}
                  </AnimatePresence>
                )}
              </li>
            ))}
          </ul>

          {/* CTA + mobile toggle */}
          <div className="flex items-center gap-2">
            <Link to="/admissions" className="btn-primary hidden sm:inline-flex">
              Apply Now
            </Link>
            <button
              onClick={() => setMobileOpen((v) => !v)}
              className="rounded-lg p-2 text-navy-700 transition-colors hover:bg-navy-50 lg:hidden"
              aria-label="Toggle menu"
            >
              {mobileOpen ? <FiX size={24} /> : <FiMenu size={24} />}
            </button>
          </div>
        </nav>

        {/* Mobile drawer */}
        <AnimatePresence>
          {mobileOpen && (
            <motion.div
              initial={{ height: 0, opacity: 0 }}
              animate={{ height: "auto", opacity: 1 }}
              exit={{ height: 0, opacity: 0 }}
              transition={{ duration: 0.3 }}
              className="overflow-hidden border-t border-navy-100 bg-white lg:hidden"
            >
              <ul className="container-custom space-y-1 py-4">
                {navLinks.map((link) => (
                  <li key={link.label}>
                    <NavLink
                      to={link.to}
                      className={({ isActive }) =>
                        `block rounded-lg px-4 py-3 text-sm font-medium transition-colors ${
                          isActive
                            ? "bg-navy-900 text-white"
                            : "text-navy-700 hover:bg-navy-50"
                        }`
                      }
                    >
                      {link.label}
                    </NavLink>
                  </li>
                ))}
                <li className="pt-2">
                  <Link to="/admissions" className="btn-primary w-full">
                    Apply Now
                  </Link>
                </li>
              </ul>
            </motion.div>
          )}
        </AnimatePresence>
      </header>
    </>
  );
}
