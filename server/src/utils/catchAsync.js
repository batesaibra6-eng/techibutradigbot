import AppError from "./AppError.js";

/**
 * Wraps an async route handler so that rejected promises are forwarded
 * to Express' error-handling middleware instead of crashing the server.
 *
 * Usage:
 *   router.get("/", catchAsync(async (req, res) => { ... }));
 */
const catchAsync = (fn) => (req, res, next) => {
  Promise.resolve(fn(req, res, next)).catch(next);
};

export default catchAsync;

/**
 * Factory: creates an AppError for a "resource not found" scenario.
 */
export const notFound = (resource = "Resource") =>
  new AppError(`${resource} not found`, 404);
