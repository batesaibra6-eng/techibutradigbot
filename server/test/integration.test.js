/**
 * End-to-end integration test for the Mayuge Light SS API.
 * Spins up an in-memory MongoDB, starts the Express server, and exercises
 * every endpoint (public + admin) with supertest-style HTTP calls.
 *
 * Run with:  node test/integration.test.js
 */
import { MongoMemoryServer } from "mongodb-memory-server";
import mongoose from "mongoose";
import http from "http";

// We import the app factory by bootstrapping it after setting env vars.
// Easiest reliable path: start the real server.js via a child process is heavy,
// so instead we re-create the Express app inline using its modules.

const BASE = "http://localhost:5099";
const request = async (method, path, body, token) => {
  const headers = { "Content-Type": "application/json" };
  if (token) headers.Authorization = `Bearer ${token}`;
  const res = await fetch(`${BASE}${path}`, {
    method,
    headers,
    body: body ? JSON.stringify(body) : undefined,
  });
  const text = await res.text();
  let json = null;
  try { json = JSON.parse(text); } catch { json = text; }
  return { status: res.status, json };
};

let passed = 0, failed = 0;
const assert = (cond, msg) => {
  if (cond) { passed++; console.log(`  ✅ ${msg}`); }
  else { failed++; console.log(`  ❌ ${msg}`); }
};

let mongo, server;

async function main() {
  console.log("\n🧪 Mayuge Light SS API — Integration Tests\n");

  // 1. Start in-memory MongoDB
  mongo = await MongoMemoryServer.create();
  process.env.MONGO_URI = mongo.getUri();
  process.env.JWT_SECRET = "test-secret";
  process.env.NODE_ENV = "development";
  process.env.PORT = "5099";
  process.env.CLIENT_URL = "*";

  // 2. Import app + start server after env is set
  const { startServer } = await import("../src/server.js");
  server = await startServer();
  console.log("  🚀 Test server running\n");

  // 3. Health check
  console.log("▸ Health & root");
  let r = await request("GET", "/api/health");
  assert(r.status === 200, "GET /api/health returns 200");

  // 4. Register admin
  console.log("▸ Auth");
  r = await request("POST", "/api/auth/register", {
    name: "Test Admin", email: "admin@test.com", password: "password123",
  });
  assert(r.status === 201, "POST /api/auth/register returns 201");

  r = await request("POST", "/api/auth/login", {
    email: "admin@test.com", password: "password123",
  });
  assert(r.status === 200, "POST /api/auth/login returns 200");
  assert(!!r.json.data?.token, "Login returns a JWT token");
  const token = r.json.data.token;

  r = await request("GET", "/api/auth/me", null, token);
  assert(r.status === 200, "GET /api/auth/me (authed) returns 200");

  r = await request("POST", "/api/auth/login", {
    email: "admin@test.com", password: "wrong",
  });
  assert(r.status === 401, "Login with wrong password returns 401");

  // 5. News — public reads (empty initially)
  console.log("▸ News");
  r = await request("GET", "/api/news");
  assert(r.status === 200, "GET /api/news returns 200");
  assert(r.json.data.news.length === 0, "News list is empty initially");

  // 6. News — admin create
  r = await request("POST", "/api/news", {
    title: "Test Article Title",
    excerpt: "Short excerpt for testing.",
    content: "Full body content of the article.\nSecond paragraph.",
    category: "Achievement",
    image: "/images/test.jpg",
    featured: true,
  }, token);
  assert(r.status === 201, "POST /api/news (admin) returns 201");
  assert(!!r.json.data.news.slug, "Created article has a slug");
  const slug = r.json.data.news.slug;
  const id = r.json.data.news._id;

  // 7. News — public read now populated
  r = await request("GET", "/api/news");
  assert(r.json.data.news.length === 1, "News list has 1 article");
  r = await request("GET", "/api/news/featured");
  assert(r.json.data.news.length === 1, "Featured endpoint returns the article");
  r = await request("GET", `/api/news/${slug}`);
  assert(r.status === 200, "GET /api/news/:slug returns 200");
  r = await request("GET", "/api/news/nonexistent-slug");
  assert(r.status === 404, "GET unknown slug returns 404");

  // 8. News — unauthorized create blocked
  r = await request("POST", "/api/news", { title: "x", excerpt: "y", content: "z" });
  assert(r.status === 401, "POST /api/news without token returns 401");

  // 9. News — admin delete
  r = await request("DELETE", `/api/news/${id}`, null, token);
  assert(r.status === 200, "DELETE /api/news/:id (admin) returns 200");

  // 10. Applications — public submit
  console.log("▸ Applications");
  r = await request("POST", "/api/applications", {
    studentName: "Jane Doe",
    classApplying: "S.1 (Senior One)",
    parentName: "Mr. Doe",
    email: "doe@test.com",
    phone: "+256700000000",
  });
  assert(r.status === 201, "POST /api/applications returns 201");
  const appId = r.json.data.application._id;

  r = await request("GET", "/api/applications", null, token);
  assert(r.status === 200, "GET /api/applications (admin) returns 200");
  assert(r.json.data.applications.length === 1, "Applications list has 1 record");

  r = await request("PATCH", `/api/applications/${appId}`, { status: "Accepted" }, token);
  assert(r.status === 200, "PATCH application status returns 200");
  assert(r.json.data.application.status === "Accepted", "Application status updated to Accepted");

  r = await request("GET", "/api/applications"); // no token
  assert(r.status === 401, "GET applications without token returns 401");

  r = await request("DELETE", `/api/applications/${appId}`, null, token);
  assert(r.status === 200, "DELETE application returns 200");

  // 11. Contact — public submit
  console.log("▸ Contact");
  r = await request("POST", "/api/contact", {
    name: "Visitor", email: "v@test.com", message: "Hello there!",
  });
  assert(r.status === 201, "POST /api/contact returns 201");
  const msgId = r.json.data.contact._id;

  r = await request("GET", "/api/contact", null, token);
  assert(r.status === 200, "GET /api/contact (admin) returns 200");
  assert(r.json.data.messages.length === 1, "Messages list has 1 record");

  r = await request("PATCH", `/api/contact/${msgId}`, { isRead: true }, token);
  assert(r.status === 200, "PATCH message returns 200");
  assert(r.json.data.contact.isRead === true, "Message marked as read");

  r = await request("DELETE", `/api/contact/${msgId}`, null, token);
  assert(r.status === 200, "DELETE message returns 200");

  // 12. Validation
  console.log("▸ Validation");
  r = await request("POST", "/api/contact", { name: "x" });
  assert(r.status === 400, "Missing fields returns 400");

  r = await request("GET", "/api/nonexistent");
  assert(r.status === 404, "Unknown route returns 404");

  // Summary
  console.log(`\n──────────────────────────────`);
  console.log(`✅ Passed: ${passed}   ❌ Failed: ${failed}`);
  console.log(`──────────────────────────────\n`);

  await cleanup();
  process.exit(failed > 0 ? 1 : 0);
}

async function cleanup() {
  if (server) server.close();
  if (mongo) await mongo.stop();
  await mongoose.disconnect();
}

main().catch(async (e) => {
  console.error("💥 Test harness error:", e);
  await cleanup();
  process.exit(1);
});
