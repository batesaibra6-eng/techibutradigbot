import { Router } from "express";
import authRoutes from "./authRoutes.js";
import newsRoutes from "./newsRoutes.js";
import applicationRoutes from "./applicationRoutes.js";
import contactRoutes from "./contactRoutes.js";

const router = Router();

/**
 * API root — confirms the server is reachable and lists available resources.
 * GET /api
 */
router.get("/", (req, res) => {
  res.json({
    success: true,
    message: "Welcome to the Mayuge Light Secondary School API",
    version: "1.0.0",
    endpoints: {
      auth: "/api/auth",
      news: "/api/news",
      applications: "/api/applications",
      contact: "/api/contact",
      health: "/api/health",
    },
  });
});

router.use("/auth", authRoutes);
router.use("/news", newsRoutes);
router.use("/applications", applicationRoutes);
router.use("/contact", contactRoutes);

export default router;
