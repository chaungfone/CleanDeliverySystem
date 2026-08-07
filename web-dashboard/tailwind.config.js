/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        primary: "#1976D2",
        secondary: "#009688",
        accent: "#E3F2FD",
        neutral: {
          400: "#4B5563", // gray-600 (~7.3:1 on white) - WCAG AA for hints/empty-state text
          99: "#FAFAFA",
          90: "#E1E2E1",
          10: "#1B1B1B",
        }
      }
    },
  },
  plugins: [],
}
