import mongoose from "mongoose";
import { config } from "./index.js";

/**
 * Establishes a connection to MongoDB using Mongoose.
 * Exits the process with an error code if the connection fails so that
 * the hosting platform (Render) can restart the service automatically.
 */
export const connectDB = async () => {
  try {
    mongoose.set("strictQuery", true);
    const conn = await mongoose.connect(config.mongoUri);

    console.log(`✅ MongoDB connected: ${conn.connection.host}`);
    return conn;
  } catch (error) {
    console.error(`❌ MongoDB connection error: ${error.message}`);
    process.exit(1);
  }
};
