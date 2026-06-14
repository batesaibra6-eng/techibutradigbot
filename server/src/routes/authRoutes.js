import { Router } from "express";
import { register, login, getMe } from "../controllers/authController.js";
import { protect } from "../middleware/authMiddleware.js";

const router = Router();

/**
 * POST /api/auth/register  — create an admin account
 * POST /api/auth/login     — authenticate & receive a JWT
 * GET  /api/auth/me        — current user profile (protected)
 */
router.post("/register", register);
router.post("/login", login);
router.get("/me", protect, getMe);

export default router;
