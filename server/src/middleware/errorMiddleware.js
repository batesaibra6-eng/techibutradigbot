import AppError from "../utils/AppError.js";

/**
 * Convert Mongoose validation / cast / duplicate-key errors into a uniform
 * operational AppError so the final handler can return a clean JSON response.
 */
const handleMongooseError = (err) => {
  // Validation error
  if (err.name === "ValidationError") {
    const messages = Object.values(err.errors).map((e) => e.message);
    return new AppError(`Invalid input: ${messages.join(". ")}`, 400);
  }

  // Duplicate key
  if (err.code === 11000) {
    const field = Object.keys(err.keyValue || {})[0] || "field";
    return new AppError(
      `A record with that ${field} already exists. Please use a different value.`,
      409
    );
  }

  // Bad ObjectId
  if (err.name === "CastError") {
    return new AppError(`Invalid ${err.path}: ${err.value}`, 400);
  }

  return err;
};

/**
 * Central error handler. Mounted last in the Express stack.
 */
// eslint-disable-next-line no-unused-vars
export const errorHandler = (err, req, res, next) => {
  let error = handleMongooseError(err);
  if (!(error instanceof AppError)) {
    error = new AppError(error.message || "Internal server error", error.statusCode || 500);
  }

  const statusCode = error.statusCode || 500;
  const response = {
    success: false,
    message: error.message || "Something went wrong",
  };

  // Include validation details in development for easier debugging
  if (process.env.NODE_ENV !== "production" && err.stack) {
    response.stack = err.stack;
  }

  // Log unexpected (non-operational) errors for monitoring
  if (!error.isOperational) {
    console.error("💥 Unexpected error:", err);
  }

  res.status(statusCode).json(response);
};

/**
 * 404 handler — fires when no route matches the request.
 */
// eslint-disable-next-line no-unused-vars
export const notFound = (req, res, next) => {
  res.status(404).json({
    success: false,
    message: `Route not found: ${req.originalUrl}`,
  });
};

export default errorHandler;
