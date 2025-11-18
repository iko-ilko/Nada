export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  darkMode: "class",
  theme: {
    extend: {
      colors: {
        primary: "#81c147",
        "background-light": "#F9FAF5",
        "background-dark": "#121212",
        "text-light": "#1f2937",
        "text-dark": "#e5e7eb",
        "subtext-light": "#6b7280",
        "subtext-dark": "#9ca3af",
        "surface-light": "#FFFFFF",
        "surface-dark": "#1E1E1E",
        "text-light-primary": "#1C1C1E",
        "text-dark-primary": "#E1E1E1",
        "text-light-secondary": "#6C757D",
        "text-dark-secondary": "#9E9E9E",
      },
      fontFamily: {
        display: ["Noto Sans KR", "sans-serif"],
      },
      borderRadius: {
        DEFAULT: "1.5rem",
      },
    },
  },
  plugins: [],
}
