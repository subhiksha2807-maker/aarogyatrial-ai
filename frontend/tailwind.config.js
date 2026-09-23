/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,ts,jsx,tsx}'],
  theme: { extend: { colors: { ink: '#173333', teal: { 50: '#ecfdf9', 100: '#d0f5ec', 500: '#159985', 600: '#0c806f', 700: '#096558', 900: '#173f3a' } }, boxShadow: { soft: '0 10px 30px rgba(18, 66, 61, 0.08)' } } },
  plugins: [],
}
