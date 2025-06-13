/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html", // Crucial for Vite's main HTML file
    "./src/**/*.{js,ts,jsx,tsx}", // Scans all JS, TS, JSX, TSX files in src/
  ],
  theme: {
    extend: {},
  },
  plugins: [],
}
