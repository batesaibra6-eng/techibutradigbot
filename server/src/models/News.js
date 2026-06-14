import mongoose from "mongoose";

/**
 * News / blog posts published by the school.
 * Stored in MongoDB and served to the public News page via the REST API.
 */
const newsSchema = new mongoose.Schema(
  {
    title: {
      type: String,
      required: [true, "A title is required"],
      trim: true,
      maxlength: [200, "Title must be 200 characters or fewer"],
    },
    slug: {
      type: String,
      unique: true,
      lowercase: true,
      trim: true,
    },
    excerpt: {
      type: String,
      required: [true, "A short excerpt is required"],
      maxlength: [300, "Excerpt must be 300 characters or fewer"],
    },
    content: {
      type: String,
      required: [true, "Content is required"],
    },
    category: {
      type: String,
      enum: ["Announcement", "Event", "Achievement", "Sports", "Academics", "General"],
      default: "General",
    },
    image: {
      type: String,
      default: "",
    },
    author: {
      type: String,
      default: "Mayuge Light SS",
    },
    isPublished: {
      type: Boolean,
      default: true,
    },
    featured: {
      type: Boolean,
      default: false,
    },
  },
  { timestamps: true }
);

// Build a URL-friendly slug from the title before saving
newsSchema.pre("validate", function buildSlug(next) {
  if (this.title) {
    this.slug =
      this.slug ||
      this.title
        .toLowerCase()
        .replace(/[^a-z0-9]+/g, "-")
        .replace(/^-+|-+$/g, "");
  }
  next();
});

// Text index to power simple search on the News page
newsSchema.index({ title: "text", excerpt: "text", content: "text" });

export default mongoose.model("News", newsSchema);
