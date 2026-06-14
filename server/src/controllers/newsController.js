import News from "../models/News.js";
import catchAsync, { notFound } from "../utils/catchAsync.js";
import AppError from "../utils/AppError.js";

/**
 * GET /api/news
 * Public. Returns published news posts with pagination + optional filters.
 * Query params: page, limit, category, search
 */
export const getNews = catchAsync(async (req, res) => {
  const page = Math.max(parseInt(req.query.page, 10) || 1, 1);
  const limit = Math.min(parseInt(req.query.limit, 10) || 9, 50);
  const skip = (page - 1) * limit;

  const filter = { isPublished: true };
  if (req.query.category && req.query.category !== "All") {
    filter.category = req.query.category;
  }
  if (req.query.search) {
    filter.$text = { $search: req.query.search };
  }

  const [items, total] = await Promise.all([
    News.find(filter).sort("-createdAt").skip(skip).limit(limit),
    News.countDocuments(filter),
  ]);

  res.json({
    success: true,
    count: items.length,
    total,
    page,
    pages: Math.ceil(total / limit),
    data: { news: items },
  });
});

/**
 * GET /api/news/featured
 * Public. Returns the latest featured news items for the homepage preview.
 */
export const getFeatured = catchAsync(async (req, res) => {
  let items = await News.find({ isPublished: true, featured: true })
    .sort("-createdAt")
    .limit(3);

  // Fallback: if nothing is explicitly featured, show the 3 latest posts
  if (items.length === 0) {
    items = await News.find({ isPublished: true }).sort("-createdAt").limit(3);
  }

  res.json({ success: true, count: items.length, data: { news: items } });
});

/**
 * GET /api/news/:slug
 * Public. Returns a single post by its slug.
 */
export const getNewsBySlug = catchAsync(async (req, res, next) => {
  const post = await News.findOne({ slug: req.params.slug, isPublished: true });
  if (!post) return next(notFound("Article"));
  res.json({ success: true, data: { news: post } });
});

/**
 * POST /api/news            (admin)
 * Create a new news post.
 */
export const createNews = catchAsync(async (req, res, next) => {
  const { title, excerpt, content, category, image, featured } = req.body;
  if (!title || !excerpt || !content) {
    return next(new AppError("Title, excerpt and content are required.", 400));
  }

  const post = await News.create({
    title,
    excerpt,
    content,
    category,
    image,
    featured,
    author: req.user?.name || "Mayuge Light SS",
  });

  res.status(201).json({ success: true, data: { news: post } });
});

/**
 * PUT /api/news/:id         (admin)
 * Update an existing post.
 */
export const updateNews = catchAsync(async (req, res, next) => {
  const post = await News.findByIdAndUpdate(req.params.id, req.body, {
    new: true,
    runValidators: true,
  });
  if (!post) return next(notFound("Article"));
  res.json({ success: true, data: { news: post } });
});

/**
 * DELETE /api/news/:id      (admin)
 * Remove a post permanently.
 */
export const deleteNews = catchAsync(async (req, res, next) => {
  const post = await News.findByIdAndDelete(req.params.id);
  if (!post) return next(notFound("Article"));
  res.json({ success: true, message: "Article deleted successfully" });
});
