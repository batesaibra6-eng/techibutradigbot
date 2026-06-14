import jwt from "jsonwebtoken";
import User from "../models/User.js";
import { config } from "../config/index.js";
import AppError from "../utils/AppError.js";
import catchAsync from "../utils/catchAsync.js";

/**
 * Protects a route: verifies the Bearer token from the Authorization header
 * and attaches the authenticated user document to req.user.
 */
export const protect = catchAsync(async (req, res, next) => {
  let token;

  if (req.headers.authorization?.startsWith("Bearer")) {
    token = req.headers.authorization.split(" ")[1];
  }

  if (!token) {
    return next(new AppError("You are not logged in. Please log in to continue.", 401));
  }

  const decoded = jwt.verify(token, config.jwt.secret);
  const user = await User.findById(decoded.id);

  if (!user) {
    return next(new AppError("The user belonging to this token no longer exists.", 401));
  }

  req.user = user;
  next();
});

/**
 * Restricts a route to users with one of the allowed roles.
 * Must run after `protect`.
 */
export const restrictTo = (...roles) => (req, res, next) => {
  if (!roles.includes(req.user?.role)) {
    return next(new AppError("You do not have permission to perform this action.", 403));
  }
  return next();
};
