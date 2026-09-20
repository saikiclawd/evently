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
        flora: {
          gold:     "#B8860B",
          "gold-lt":"#F5EDD2",
          rose:     "#9B5E6A",
          "rose-lt":"#F5E6E9",
          sage:     "#5E7E6A",
          "sage-lt":"#E2EDE5",
          cream:    "#FDFAF6",
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
