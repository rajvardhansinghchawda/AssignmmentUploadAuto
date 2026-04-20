/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        background: "#0b1326",
        surface: "#0b1326",
        "surface-container-lowest": "#060e20",
        "surface-container-low": "#131b2e",
        "surface-container": "#171f33",
        "surface-container-high": "#222a3d",
        "surface-container-highest": "#2d3449",
        "surface-bright": "#31394d",
        "surface-variant": "#2d3449",
        primary: "#bbc3ff",
        "primary-container": "#3d5afe",
        "primary-fixed": "#dee0ff",
        error: "#ffb4ab",
        "on-surface": "#dae2fd",
        "on-surface-variant": "#c5c5d9",
        "on-primary-container": "#f1f0ff",
        "outline-variant": "#444656",
      },
      fontFamily: {
        display: ['Space Grotesk', 'sans-serif'],
        sans: ['Inter', 'sans-serif'],
        mono: ['JetBrains Mono', 'Roboto Mono', 'monospace'],
      },
      boxShadow: {
        glow: '0 0 40px rgba(218, 226, 253, 0.05)',
        bloom: '0 0 15px rgba(61, 90, 254, 0.4)',
        success: '0 0 15px rgba(187, 195, 255, 0.4)',
        error: '0 0 15px rgba(255, 180, 171, 0.4)'
      }
    },
  },
  plugins: [],
}
