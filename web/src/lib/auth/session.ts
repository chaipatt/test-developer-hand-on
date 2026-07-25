// Name of the httpOnly cookie holding the backend-issued JWT. The browser
// never reads it; the BFF forwards it to the Python API as a Bearer token.
export const SESSION_COOKIE = "lf_session";

// Roles as returned by the backend's GET /auth/me.
export type Role = "user" | "admin";
