import { Router } from "express";
import {
  createApplication,
  getApplications,
  getApplication,
  updateApplication,
  deleteApplication,
} from "../controllers/applicationController.js";
import { protect, restrictTo } from "../middleware/authMiddleware.js";

const router = Router();

/**
 * POST /api/applications   — public submission of admission forms
 */
router.post("/", createApplication);

/**
 * Admin-only management routes
 */
router.get("/", protect, restrictTo("admin"), getApplications);
router.get("/:id", protect, restrictTo("admin"), getApplication);
router.patch("/:id", protect, restrictTo("admin"), updateApplication);
router.delete("/:id", protect, restrictTo("admin"), deleteApplication);

export default router;
