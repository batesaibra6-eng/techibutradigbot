import { Link } from "react-router-dom";
import { motion } from "framer-motion";
import { FiCalendar, FiArrowRight } from "react-icons/fi";

const categoryColors = {
  Achievement: "bg-green-100 text-green-700",
  Event: "bg-blue-100 text-blue-700",
  Sports: "bg-orange-100 text-orange-700",
  Academics: "bg-purple-100 text-purple-700",
  Announcement: "bg-gold-100 text-gold-700",
  General: "bg-navy-100 text-navy-700",
};

/**
 * Card used to preview news articles on the Home and News pages.
 */
export default function NewsCard({ article, index = 0 }) {
  const date = new Date(article.createdAt || article.date).toLocaleDateString(
    "en-GB",
    { day: "numeric", month: "short", year: "numeric" }
  );
  const badge = categoryColors[article.category] || categoryColors.General;

  return (
    <motion.article
      initial={{ opacity: 0, y: 30 }}
      whileInView={{ opacity: 1, y: 0 }}
      viewport={{ once: true, }}
      transition={{ duration: 0.5, delay: index * 0.1 }}
      whileHover={{ y: -8 }}
      className="group flex flex-col overflow-hidden rounded-2xl bg-white shadow-card ring-1 ring-navy-100 transition-shadow hover:shadow-soft"
    >
      {/* Image */}
      <Link to={`/news/${article.slug}`} className="relative block aspect-[16/10] overflow-hidden">
        <img
          src={article.image || "/images/campus/campus-1.jpg"}
          alt={article.title}
          loading="lazy"
          className="h-full w-full object-cover transition-transform duration-700 group-hover:scale-110"
        />
        <span className={`absolute left-4 top-4 rounded-full px-3 py-1 text-xs font-semibold ${badge}`}>
          {article.category}
        </span>
      </Link>

      {/* Body */}
      <div className="flex flex-1 flex-col p-5">
        <p className="flex items-center gap-2 text-xs text-navy-400">
          <FiCalendar /> {date}
        </p>
        <h3 className="mt-2 line-clamp-2 text-lg font-bold text-navy-900 transition-colors group-hover:text-gold-600">
          <Link to={`/news/${article.slug}`}>{article.title}</Link>
        </h3>
        <p className="mt-2 line-clamp-3 flex-1 text-sm leading-relaxed text-navy-500">
          {article.excerpt}
        </p>
        <Link
          to={`/news/${article.slug}`}
          className="mt-4 inline-flex items-center gap-1.5 text-sm font-semibold text-gold-600 transition-colors hover:text-gold-700"
        >
          Read More <FiArrowRight className="transition-transform group-hover:translate-x-1" />
        </Link>
      </div>
    </motion.article>
  );
}
