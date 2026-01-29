import { defineConfig, globalIgnores } from "eslint/config";
import nextVitals from "eslint-config-next/core-web-vitals";
import nextTs from "eslint-config-next/typescript";

const eslintConfig = defineConfig([
  ...nextVitals,
  ...nextTs,
  // Override default ignores of eslint-config-next.
  globalIgnores([
    // Default ignores of eslint-config-next:
    ".next/**",
    "out/**",
    "build/**",
    "next-env.d.ts",
    "tests/**", // Ignore test files
  ]),
  {
    rules: {
      // Allow setState in useEffect for reset operations - make it a warning
      "react-hooks/exhaustive-deps": "warn",
      "react-hooks/set-state-in-effect": "warn", // Allow controlled state resets
    },
  },
]);

export default eslintConfig;
