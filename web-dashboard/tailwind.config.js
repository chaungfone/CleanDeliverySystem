/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        primary: "#2196F3",
        secondary: "#009688",
        accent: "#E3F2FD",
        neutral: {
          99: "#FAFAFA",
          90: "#E1E2E1",
          10: "#1B1B1B",
        }
      }
    },
  },
  plugins: [],
}
