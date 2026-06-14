import ContactMessage from "../models/ContactMessage.js";
import catchAsync, { notFound } from "../utils/catchAsync.js";
import AppError from "../utils/AppError.js";

/**
 * POST /api/contact   (public)
 * Store a message submitted from the Contact page.
 */
export const createMessage = catchAsync(async (req, res, next) => {
  const { name, email, message } = req.body;
  if (!name || !email || !message) {
    return next(new AppError("Name, email and message are required.", 400));
  }

  const doc = await ContactMessage.create(req.body);

  res.status(201).json({
    success: true,
    message: "Thank you for reaching out! We will get back to you soon.",
    data: { contact: doc },
  });
});

/**
 * GET /api/contact    (admin)
 * List all contact messages with pagination.
 */
export const getMessages = catchAsync(async (req, res) => {
  const page = Math.max(parseInt(req.query.page, 10) || 1, 1);
  const limit = Math.min(parseInt(req.query.limit, 10) || 20, 100);
  const skip = (page - 1) * limit;

  const filter = {};
  if (req.query.unread === "true") filter.isRead = false;

  const [items, total] = await Promise.all([
    ContactMessage.find(filter).sort("-createdAt").skip(skip).limit(limit),
    ContactMessage.countDocuments(filter),
  ]);

  res.json({
    success: true,
    count: items.length,
    total,
    page,
    pages: Math.ceil(total / limit),
    data: { messages: items },
  });
});

/**
 * PATCH /api/contact/:id  (admin)
 * Mark a message as read / unread.
 */
export const updateMessage = catchAsync(async (req, res, next) => {
  const { isRead } = req.body;
  const doc = await ContactMessage.findByIdAndUpdate(
    req.params.id,
    { isRead },
    { new: true }
  );
  if (!doc) return next(notFound("Message"));
  res.json({ success: true, data: { contact: doc } });
});

/**
 * DELETE /api/contact/:id  (admin)
 */
export const deleteMessage = catchAsync(async (req, res, next) => {
  const doc = await ContactMessage.findByIdAndDelete(req.params.id);
  if (!doc) return next(notFound("Message"));
  res.json({ success: true, message: "Message deleted successfully" });
});
