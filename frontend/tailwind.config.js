/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        // Official Problem Statement Visual Identity
        navy: {
          DEFAULT: '#101F43',
          dark: '#0B152E',
          light: '#1B3168',
        },
        pink: {
          DEFAULT: '#EC008C',
          light: '#FDF2F8',
          border: '#FBCFE8',
          dark: '#C70076',
        },
        surface: {
          DEFAULT: '#FFFFFF',
          subtle: '#F5F7FA',
          border: '#E5E7EB',
          'border-subtle': '#E2E8F0',
        },
      },
      fontFamily: {
        sans: ['Plus Jakarta Sans', 'Inter', 'system-ui', '-apple-system', 'sans-serif'],
        mono: ['JetBrains Mono', 'Fira Code', 'monospace'],
      },
      boxShadow: {
        'xs': '0 1px 2px 0 rgba(16, 31, 67, 0.05)',
        'sm': '0 1px 3px 0 rgba(16, 31, 67, 0.08), 0 1px 2px 0 rgba(16, 31, 67, 0.04)',
        'md': '0 4px 6px -1px rgba(16, 31, 67, 0.08), 0 2px 4px -1px rgba(16, 31, 67, 0.04)',
      },
    },
  },
  plugins: [],
}
