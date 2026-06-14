import mongoose from "mongoose";

/**
 * Admission applications submitted through the Admissions page form.
 */
const applicationSchema = new mongoose.Schema(
  {
    studentName: {
      type: String,
      required: [true, "Student name is required"],
      trim: true,
    },
    dateOfBirth: {
      type: Date,
    },
    gender: {
      type: String,
      enum: ["Male", "Female", ""],
      default: "",
    },
    classApplying: {
      type: String,
      required: [true, "Please select the class you are applying for"],
      trim: true,
    },
    previousSchool: {
      type: String,
      trim: true,
      default: "",
    },
    parentName: {
      type: String,
      required: [true, "Parent / guardian name is required"],
      trim: true,
    },
    parentRelationship: {
      type: String,
      trim: true,
      default: "",
    },
    email: {
      type: String,
      required: [true, "Email is required"],
      lowercase: true,
      trim: true,
      match: [/^\S+@\S+\.\S+$/, "Please provide a valid email address"],
    },
    phone: {
      type: String,
      required: [true, "Phone number is required"],
      trim: true,
    },
    address: {
      type: String,
      trim: true,
      default: "",
    },
    message: {
      type: String,
      trim: true,
      default: "",
    },
    status: {
      type: String,
      enum: ["Pending", "Reviewing", "Accepted", "Rejected"],
      default: "Pending",
    },
  },
  { timestamps: true }
);

export default mongoose.model("Application", applicationSchema);
