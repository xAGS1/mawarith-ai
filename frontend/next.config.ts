import type { NextConfig } from "next";

const config: NextConfig = {
  // Local previews use both hosts. Next dev otherwise blocks resources requested
  // from 127.0.0.1 when the server advertises localhost, preventing hydration.
  allowedDevOrigins: ["127.0.0.1"],
};

export default config;
