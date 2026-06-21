/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,jsx}'],
  theme: {
    extend: {
      colors: {
        ink: '#171b2e',
        muted: '#6f7387',
        canvas: '#f7f8fc',
        primary: '#6759e8',
        cyan: '#25b7d3'
      },
      fontFamily: {
        sans: ['DM Sans', 'sans-serif'],
        display: ['Manrope', 'sans-serif']
      },
      boxShadow: {
        card: '0 16px 45px rgba(33, 31, 80, 0.07)',
        glow: '0 16px 34px rgba(103, 89, 232, 0.28)'
      }
    }
  },
  plugins: []
}
