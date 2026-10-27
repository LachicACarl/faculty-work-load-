import { defineConfig, mergeConfig } from "vitest/config";
import viteConfig from "./vite.config";

export default mergeConfig(
  viteConfig,
  defineConfig({
    envDir: "./src/test",
    test: {
      environment: "jsdom",
      setupFiles: ["./src/test/setup.ts"],
      include: ["src/**/*.test.{ts,tsx}"],
      exclude: [
        "**/node_modules/**",
        "**/dist/**",
        "**/coverage/**",
        "**/.git/**",
        "**/.tmp/**",
        "**/tmp/**",
      ],
      clearMocks: true,
      restoreMocks: true,
      unstubGlobals: true,
    },
  }),
);
