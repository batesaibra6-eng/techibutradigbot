import jwt from "jsonwebtoken";
import User from "../models/User.js";
import { config } from "../config/index.js";
import AppError from "../utils/AppError.js";
import catchAsync from "../utils/catchAsync.js";

/**
 * Sign a JWT for a given user id.
 */
const signToken = (id) =>
  jwt.sign({ id }, config.jwt.secret, { expiresIn: config.jwt.expiresIn });

/**
 * POST /api/auth/register
 * Creates a new admin/editor account. Protected in production so only an
 * existing admin can create new users.
 */
export const register = catchAsync(async (req, res, next) => {
  const { name, email, password } = req.body;

  if (!name || !email || !password) {
    return next(new AppError("Name, email and password are required.", 400));
  }

  const user = await User.create({ name, email, password, role: "admin" });
  const token = signToken(user._id);

  res.status(201).json({
    success: true,
    message: "Account created successfully",
    data: { user, token },
  });
});

/**
 * POST /api/auth/login
 * Authenticates an admin and returns a JWT.
 */
export const login = catchAsync(async (req, res, next) => {
  const { email, password } = req.body;

  if (!email || !password) {
    return next(new AppError("Please provide email and password.", 400));
  }

  // explicitly select password (excluded by default)
  const user = await User.findOne({ email }).select("+password");
  if (!user || !(await user.comparePassword(password))) {
    return next(new AppError("Incorrect email or password.", 401));
  }

  const token = signToken(user._id);

  res.json({
    success: true,
    message: "Logged in successfully",
    data: { user, token },
  });
});

/**
 * GET /api/auth/me
 * Returns the profile of the currently authenticated user.
 */
export const getMe = catchAsync(async (req, res) => {
  res.json({ success: true, data: { user: req.user } });
});
