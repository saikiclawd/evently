/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,jsx}"],
  theme: {
    extend: {
      colors: {
        dark: {
          bg: "#FAF8F5",
          surface: "#FFFFFF",
          card: "#FFFFFF",
          border: "#E8E2DA",
        },
        accent: {
          DEFAULT: "#2563EB",
          dim: "#DBEAFE",
        },
      },
      fontFamily: {
        sans: ["DM Sans", "system-ui", "sans-serif"],
        mono: ["JetBrains Mono", "monospace"],
      },
    },
  },
  plugins: [],
};
