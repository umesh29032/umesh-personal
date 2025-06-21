module.exports = {
  content: [
    "../accounts/templates/**/*.html",
    "../templates/**/*.html",
    "../theme/templates/**/*.html",
    "../**/*.py",
  ],
  theme: {
    extend: {
      colors: {
        primary: '#2c3e50',
        secondary: '#3498db',
        accent: '#2980b9',
        textlight: '#ecf0f1',
        textdark: '#2c3e50',
        backgroundlight: '#f8f9fa',
        danger: '#e74c3c',
        dangerhover: '#c0392b',
      },
      boxShadow: {
        nav: '0 4px 6px rgba(0, 0, 0, 0.1)',
        sidenav: '4px 0 15px rgba(0, 0, 0, 0.1)',
      },
    },
  },
  plugins: [],
}