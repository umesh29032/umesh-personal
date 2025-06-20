module.exports = {
  content: [
    "./accounts/templates/**/*.html",  // Accounts app templates from project root
    "./templates/**/*.html",          // Root-level templates if any
  ],
  theme: {
    extend: {
      colors: {
        'company-blue': '#1e40af',
      },
      fontFamily: {
        'sans': ['Inter', 'sans-serif'],
      },
    },
  },
  plugins: [],
}