import { defineConfig, globalIgnores } from "eslint/config";
import next from "eslint-config-next/core-web-vitals";
import ts from "eslint-config-next/typescript";
import a11y from "eslint-plugin-jsx-a11y";

export default defineConfig([...next, ...ts, {
  files: ["**/*.tsx"],
  rules: a11y.flatConfigs.recommended.rules,
}, globalIgnores([".next/**", "next-env.d.ts", "test-results/**", "playwright-report/**"])]);
