/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,jsx}"],
  theme: {
    extend: {
      colors: {
        dark: {
          bg: "#0B0E11",
          surface: "#12161B",
          card: "#161B22",
          border: "#21272F",
        },
        accent: {
          DEFAULT: "#58A6FF",
          dim: "#1F3A5F",
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
