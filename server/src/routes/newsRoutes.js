import { Router } from "express";
import {
  getNews,
  getFeatured,
  getNewsBySlug,
  createNews,
  updateNews,
  deleteNews,
} from "../controllers/newsController.js";
import { protect, restrictTo } from "../middleware/authMiddleware.js";

const router = Router();

/**
 * PUBLIC routes — view published news
 * GET /api/news              — paginated, filterable list
 * GET /api/news/featured     — homepage featured preview
 * GET /api/news/:slug        — single article
 */
router.get("/", getNews);
router.get("/featured", getFeatured);
router.get("/:slug", getNewsBySlug);

/**
 * ADMIN routes — manage news (requires a valid JWT)
 * POST   /api/news           — create
 * PUT    /api/news/:id       — update
 * DELETE /api/news/:id       — delete
 */
router.use(protect, restrictTo("admin"));
router.post("/", createNews);
router.put("/:id", updateNews);
router.delete("/:id", deleteNews);

export default router;
