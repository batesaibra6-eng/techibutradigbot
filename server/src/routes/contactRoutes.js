import { Router } from "express";
import {
  createMessage,
  getMessages,
  updateMessage,
  deleteMessage,
} from "../controllers/contactController.js";
import { protect, restrictTo } from "../middleware/authMiddleware.js";

const router = Router();

/**
 * POST /api/contact   — public submission of contact form
 */
router.post("/", createMessage);

/**
 * Admin-only management routes
 */
router.get("/", protect, restrictTo("admin"), getMessages);
router.patch("/:id", protect, restrictTo("admin"), updateMessage);
router.delete("/:id", protect, restrictTo("admin"), deleteMessage);

export default router;
