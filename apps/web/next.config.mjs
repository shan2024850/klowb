import { fileURLToPath } from "node:url";
const config = {
  devIndicators: false,
  output: "standalone",
  outputFileTracingRoot: fileURLToPath(new URL("../../", import.meta.url)),
};

export default config;
