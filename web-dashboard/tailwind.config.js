/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        // Brand "water blue" — the anchor color for the Clean Delivery brand.
        primary: {
          DEFAULT: "#1976D2",
          50: "#EFF7FE",
          100: "#E3F2FD", // legacy `accent` tint
          200: "#C4E2F9",
          300: "#92CCF2",
          400: "#55ABE6",
          500: "#1976D2",
          600: "#1665B4",
          700: "#12528F",
          800: "#10416E",
          900: "#0D3557",
        },
        // Teal accent — complements the blue for secondary/success touches.
        secondary: {
          DEFAULT: "#009688",
          50: "#E7F6F5",
          100: "#C7ECE9",
          200: "#9DDCD8",
          300: "#66C8C2",
          400: "#2FB0A8",
          500: "#009688",
          600: "#008076",
          700: "#00685F",
          800: "#00524B",
          900: "#043E39",
        },
        accent: "#E3F2FD",
        neutral: {
          400: "#4B5563", // gray-600 (~7.3:1 on white) - WCAG AA for hints/empty-state text
          99: "#F5F7FA",  // page canvas / subtle hover fill (cool neutral)
          90: "#E4E8EF",  // borders and dividers (cool neutral)
          10: "#16181D",  // near-black text
        },
        // Semantic status colors tuned to the brand (light-tint backgrounds).
        status: {
          success: "#16A34A",
          warning: "#D97706",
          danger: "#DC2626",
          info: "#1976D2",
        },
      },
      fontFamily: {
        sans: [
          "Inter",
          "Noto Sans Myanmar",
          "Pyidaungsu",
          "system-ui",
          "-apple-system",
          "Segoe UI",
          "sans-serif",
        ],
      },
      boxShadow: {
        card: "0 1px 2px rgba(16, 24, 40, 0.04), 0 1px 3px rgba(16, 24, 40, 0.06)",
        "card-hover": "0 10px 24px -6px rgba(16, 24, 40, 0.10), 0 4px 12px -4px rgba(16, 24, 40, 0.06)",
        drawer: "-10px 0 32px rgba(16, 24, 40, 0.14)",
        modal: "0 24px 56px -12px rgba(16, 24, 40, 0.22)",
        pop: "0 6px 16px -4px rgba(25, 118, 210, 0.35)",
      },
      keyframes: {
        "fade-in": {
          from: { opacity: "0" },
          to: { opacity: "1" },
        },
        "fade-in-up": {
          from: { opacity: "0", transform: "translateY(10px)" },
          to: { opacity: "1", transform: "translateY(0)" },
        },
        "scale-in": {
          from: { opacity: "0", transform: "scale(0.96) translateY(6px)" },
          to: { opacity: "1", transform: "scale(1) translateY(0)" },
        },
        "slide-in-right": {
          from: { transform: "translateX(100%)" },
          to: { transform: "translateX(0)" },
        },
      },
      animation: {
        "fade-in": "fade-in 0.25s ease-out both",
        "fade-in-up": "fade-in-up 0.3s ease-out both",
        "scale-in": "scale-in 0.22s ease-out both",
        "slide-in-right": "slide-in-right 0.3s ease-out both",
      },
    },
  },
  plugins: [],
}
