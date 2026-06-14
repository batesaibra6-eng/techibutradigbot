/**
 * Database seed script.
 * Creates a default admin user and a handful of sample news posts so the
 * website has content to display immediately after deployment.
 *
 * Run with:  npm run seed
 */
import mongoose from "mongoose";
import User from "./models/User.js";
import News from "./models/News.js";
import { config } from "./config/index.js";
import { connectDB } from "./config/db.js";
import { sampleNews } from "./data/sampleNews.js";

const seed = async () => {
  try {
    await connectDB();

    console.log("🌱 Clearing existing data...");
    await Promise.all([User.deleteMany({}), News.deleteMany({})]);

    // --- Admin account ---
    const { name, email, password } = config.seedAdmin;
    const admin = await User.create({ name, email, password, role: "admin" });
    console.log(`👤 Admin created → ${admin.email} (password: ${password})`);

    // --- News posts ---
    await News.insertMany(sampleNews);
    console.log(`📰 Inserted ${sampleNews.length} news articles`);

    console.log("✅ Seed complete!");
    process.exit(0);
  } catch (error) {
    console.error("❌ Seed failed:", error.message);
    process.exit(1);
  }
};

seed();
