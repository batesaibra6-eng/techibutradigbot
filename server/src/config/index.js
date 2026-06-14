import dotenv from "dotenv";

// Load environment variables from .env file
dotenv.config();

/**
 * Centralised application configuration.
 * Every setting is read from environment variables with sensible defaults,
 * so the app behaves predictably across development and production.
 */
export const config = {
  env: process.env.NODE_ENV || "development",
  port: process.env.PORT || 5000,
  mongoUri: process.env.MONGO_URI || "mongodb://127.0.0.1:27017/mayuge_light_ss",

  jwt: {
    secret: process.env.JWT_SECRET || "dev_only_insecure_secret_change_me",
    expiresIn: process.env.JWT_EXPIRES_IN || "7d",
  },

  // Allowed CORS origins (comma separated in .env)
  corsOrigins: (process.env.CLIENT_URL || "http://localhost:5173")
    .split(",")
    .map((o) => o.trim())
    .filter(Boolean),

  // Seed admin credentials
  seedAdmin: {
    name: process.env.ADMIN_NAME || "Administrator",
    email: process.env.ADMIN_EMAIL || "admin@mayugelightss.sc.ug",
    password: process.env.ADMIN_PASSWORD || "ChangeMe123!",
  },

  isProduction: process.env.NODE_ENV === "production",
};
