/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  darkMode: "class",
  theme: {
    extend: {
      colors: {
        'light-blue': '#dbeafe',
        'soft-blue': '#bfdbfe',
        'light-cyan': '#e0f7fa',
        'dark-blue': '#1e3a8a',
        'bright-blue': '#2563eb',
        'deep-blue': '#1d4ed8',
      },
    },
  },
  plugins: [],
}

