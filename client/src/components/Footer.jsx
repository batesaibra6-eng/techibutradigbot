import { Link } from "react-router-dom";
import { motion } from "framer-motion";
import {
  FiMapPin,
  FiPhone,
  FiMail,
  FiFacebook,
  FiTwitter,
  FiInstagram,
  FiYoutube,
  FiArrowUpRight,
} from "react-icons/fi";
import { SCHOOL } from "../data/school.js";

const quickLinks = [
  { to: "/about", label: "About Us" },
  { to: "/academics", label: "Academics" },
  { to: "/admissions", label: "Admissions" },
  { to: "/student-life", label: "Student Life" },
  { to: "/news", label: "News & Events" },
  { to: "/contact", label: "Contact" },
];

const programmes = [
  "Ordinary Level (O-Level)",
  "Advanced Level (A-Level)",
  "Sciences Department",
  "Humanities Department",
  "Co-curricular Activities",
  "Boarding Section",
];

const socials = [
  { icon: FiFacebook, href: SCHOOL.socials.facebook, label: "Facebook" },
  { icon: FiTwitter, href: SCHOOL.socials.twitter, label: "Twitter" },
  { icon: FiInstagram, href: SCHOOL.socials.instagram, label: "Instagram" },
  { icon: FiYoutube, href: SCHOOL.socials.youtube, label: "YouTube" },
];

export default function Footer() {
  return (
    <footer className="bg-navy-950 text-navy-200">
      {/* CTA strip */}
      <div className="border-b border-white/5">
        <div className="container-custom grid items-center gap-6 py-10 md:grid-cols-2">
          <div>
            <h3 className="text-2xl font-bold text-white">
              Ready to join our family?
            </h3>
            <p className="mt-2 text-navy-300">
              Admissions are open for O-Level and A-Level. Begin your journey
              with Mayuge Light SS today.
            </p>
          </div>
          <div className="flex flex-wrap gap-3 md:justify-end">
            <Link to="/admissions" className="btn-primary">
              Apply for Admission
            </Link>
            <Link to="/contact" className="btn-outline">
              Contact Us
            </Link>
          </div>
        </div>
      </div>

      {/* Main footer */}
      <div className="container-custom grid gap-10 py-14 md:grid-cols-2 lg:grid-cols-4">
        {/* Brand */}
        <div>
          <Link to="/" className="flex items-center gap-3">
            <img
              src="/images/logo.png"
              alt="School logo"
              className="h-12 w-12 rounded-full object-cover ring-2 ring-gold-400"
            />
            <span className="font-display text-lg font-bold text-white">
              Mayuge Light SS
            </span>
          </Link>
          <p className="mt-4 text-sm leading-relaxed text-navy-300">
            {SCHOOL.tagline}. A centre of academic excellence and character
            formation in Mayuge, Uganda.
          </p>
          <div className="mt-5 flex gap-3">
            {socials.map(({ icon: Icon, href, label }) => (
              <motion.a
                key={label}
                href={href}
                target="_blank"
                rel="noreferrer"
                aria-label={label}
                whileHover={{ y: -3 }}
                className="flex h-10 w-10 items-center justify-center rounded-full bg-white/5 text-navy-200 transition-colors hover:bg-gold-500 hover:text-navy-950"
              >
                <Icon />
              </motion.a>
            ))}
          </div>
        </div>

        {/* Quick links */}
        <div>
          <h4 className="mb-4 font-semibold uppercase tracking-wider text-white">
            Quick Links
          </h4>
          <ul className="space-y-2.5 text-sm">
            {quickLinks.map((link) => (
              <li key={link.to}>
                <Link
                  to={link.to}
                  className="group inline-flex items-center gap-1 text-navy-300 transition-colors hover:text-gold-400"
                >
                  <FiArrowUpRight className="opacity-0 transition-opacity group-hover:opacity-100" />
                  {link.label}
                </Link>
              </li>
            ))}
          </ul>
        </div>

        {/* Programmes */}
        <div>
          <h4 className="mb-4 font-semibold uppercase tracking-wider text-white">
            Programmes
          </h4>
          <ul className="space-y-2.5 text-sm">
            {programmes.map((p) => (
              <li key={p} className="text-navy-300">
                {p}
              </li>
            ))}
          </ul>
        </div>

        {/* Contact */}
        <div>
          <h4 className="mb-4 font-semibold uppercase tracking-wider text-white">
            Get in Touch
          </h4>
          <ul className="space-y-3 text-sm">
            <li className="flex gap-3">
              <FiMapPin className="mt-0.5 shrink-0 text-gold-400" />
              <span>{SCHOOL.address}</span>
            </li>
            <li className="flex gap-3">
              <FiPhone className="mt-0.5 shrink-0 text-gold-400" />
              <a href={`tel:${SCHOOL.phone}`} className="hover:text-gold-400">
                {SCHOOL.phone}
              </a>
            </li>
            <li className="flex gap-3">
              <FiMail className="mt-0.5 shrink-0 text-gold-400" />
              <a href={`mailto:${SCHOOL.email}`} className="hover:text-gold-400">
                {SCHOOL.email}
              </a>
            </li>
          </ul>
        </div>
      </div>

      {/* Bottom bar */}
      <div className="border-t border-white/5">
        <div className="container-custom flex flex-col items-center justify-between gap-2 py-5 text-xs text-navy-400 sm:flex-row">
          <p>
            © {new Date().getFullYear()} {SCHOOL.name}. All rights reserved.
          </p>
          <p>
            Designed with care for the Mayuge Light SS community ·{" "}
            <span className="text-gold-400">{SCHOOL.motto}</span>
          </p>
        </div>
      </div>
    </footer>
  );
}
