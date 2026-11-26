/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,ts,jsx,tsx}'],
  theme: {
    extend: {
      colors: {
        obsidian: '#0b0d10',
        charcoal: '#111419',
        slatePanel: '#161b22',
        gridLine: '#232a35',
        cyanAccent: '#38bdf8',
        emeraldAccent: '#34d399',
        amberAccent: '#fbbf24',
        coralAccent: '#fb7185',
        violetAccent: '#a78bfa',
      },
      fontFamily: {
        sans: ['Inter', 'SF Pro Display', 'system-ui', 'sans-serif'],
        mono: ['JetBrains Mono', 'SF Mono', 'Menlo', 'monospace'],
      },
    },
  },
  plugins: [],
}
