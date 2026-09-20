import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./app/**/*.{ts,tsx}",
    "./components/**/*.{ts,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        bull: "#22c55e",
        bear: "#ef4444",
      },
    },
  },
  plugins: [],
};

export default config;
