import express from "express";
import cors from "cors";
import helmet from "helmet";
import compression from "compression";
import morgan from "morgan";
import rateLimit from "express-rate-limit";
import mongoSanitize from "express-mongo-sanitize";
import hpp from "hpp";

import { config } from "./config/index.js";
import { connectDB } from "./config/db.js";
import apiRoutes from "./routes/index.js";
import { errorHandler, notFound } from "./middleware/errorMiddleware.js";

/**
 * Mayuge Light Secondary School — Express application entry point.
 * Bootstraps middleware, connects to MongoDB, and mounts the REST API.
 */
const app = express();

// --- Trust proxy (needed when behind Render's load balancer) ---
app.set("trust proxy", 1);

// --- Security & hardening middleware ---
app.use(helmet());
app.use(
  cors({
    origin: config.corsOrigins,
    credentials: true,
    methods: ["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
  })
);

// --- Body parsers with size limits ---
app.use(express.json({ limit: "1mb" }));
app.use(express.urlencoded({ extended: true, limit: "1mb" }));

// --- Prevent NoSQL injection & HTTP parameter pollution ---
app.use(mongoSanitize());
app.use(hpp());

// --- Rate limiting (protect against brute-force / abuse) ---
const limiter = rateLimit({
  windowMs: 15 * 60 * 1000, // 15 minutes
  max: 200, // limit each IP to 200 requests per window
  standardHeaders: true,
  legacyHeaders: false,
  message: { success: false, message: "Too many requests, please try again later." },
});
app.use("/api", limiter);

// --- Logging & compression ---
if (!config.isProduction) {
  app.use(morgan("dev"));
} else {
  app.use(morgan("combined"));
}
app.use(compression());

// --- Health check (used by Render + uptime monitors) ---
app.get("/api/health", (req, res) => {
  res.json({
    success: true,
    status: "ok",
    timestamp: new Date().toISOString(),
    uptime: process.uptime(),
    environment: config.env,
  });
});

// --- API routes ---
app.use("/api", apiRoutes);

// --- Serve the built React frontend in production ---
import path from "path";
import { fileURLToPath } from "url";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const clientBuild = path.join(__dirname, "../../client/dist");

if (config.isProduction) {
  app.use(express.static(clientBuild));
  // SPA fallback: any non-API route returns index.html
  app.get(/^\/(?!api).*/, (req, res) => {
    res.sendFile(path.join(clientBuild, "index.html"));
  });
}

// --- 404 & central error handlers (must be last) ---
app.use(notFound);
app.use(errorHandler);

/**
 * Start the server once MongoDB is connected.
 */
export async function startServer() {
  await connectDB();

  const PORT = config.port;
  const server = app.listen(PORT, () => {
    console.log(`🚀 Server running in ${config.env} mode on port ${PORT}`);
    if (config.isProduction) {
      console.log(`🌐 Frontend served from ${clientBuild}`);
    }
  });

  // Graceful shutdown
  process.on("unhandledRejection", (err) => {
    console.error("💥 Unhandled Rejection:", err.name, err.message);
    server.close(() => process.exit(1));
  });

  return server;
}

// Only auto-start when this file is executed directly (not imported in tests)
const isMainModule = process.argv[1] === fileURLToPath(import.meta.url);

if (isMainModule) {
  startServer();
}

export default app;
