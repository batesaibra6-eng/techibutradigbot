import Application from "../models/Application.js";
import catchAsync, { notFound } from "../utils/catchAsync.js";
import AppError from "../utils/AppError.js";

/**
 * POST /api/applications   (public)
 * Submit a new admission application from the Admissions page.
 */
export const createApplication = catchAsync(async (req, res, next) => {
  const application = await Application.create(req.body);

  res.status(201).json({
    success: true,
    message:
      "Your application has been received. Our admissions team will contact you shortly.",
    data: { application },
  });
});

/**
 * GET /api/applications     (admin)
 * List all applications with optional status filter + pagination.
 */
export const getApplications = catchAsync(async (req, res) => {
  const page = Math.max(parseInt(req.query.page, 10) || 1, 1);
  const limit = Math.min(parseInt(req.query.limit, 10) || 20, 100);
  const skip = (page - 1) * limit;

  const filter = {};
  if (req.query.status) filter.status = req.query.status;

  const [items, total] = await Promise.all([
    Application.find(filter).sort("-createdAt").skip(skip).limit(limit),
    Application.countDocuments(filter),
  ]);

  res.json({
    success: true,
    count: items.length,
    total,
    page,
    pages: Math.ceil(total / limit),
    data: { applications: items },
  });
});

/**
 * GET /api/applications/:id  (admin)
 */
export const getApplication = catchAsync(async (req, res, next) => {
  const application = await Application.findById(req.params.id);
  if (!application) return next(notFound("Application"));
  res.json({ success: true, data: { application } });
});

/**
 * PATCH /api/applications/:id  (admin)
 * Update an application's status (Accept / Reject / Reviewing...).
 */
export const updateApplication = catchAsync(async (req, res, next) => {
  const { status } = req.body;
  const valid = ["Pending", "Reviewing", "Accepted", "Rejected"];
  if (status && !valid.includes(status)) {
    return next(new AppError("Invalid status value.", 400));
  }

  const application = await Application.findByIdAndUpdate(
    req.params.id,
    { status },
    { new: true, runValidators: true }
  );
  if (!application) return next(notFound("Application"));
  res.json({ success: true, data: { application } });
});

/**
 * DELETE /api/applications/:id  (admin)
 */
export const deleteApplication = catchAsync(async (req, res, next) => {
  const application = await Application.findByIdAndDelete(req.params.id);
  if (!application) return next(notFound("Application"));
  res.json({ success: true, message: "Application deleted successfully" });
});
