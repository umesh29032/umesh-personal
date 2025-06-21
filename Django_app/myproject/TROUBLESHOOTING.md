# Troubleshooting Guide

## Page Not Loading or Styling Broken?

### Quick Fix Steps:

1. **Rebuild Tailwind CSS:**
   ```bash
   python build_tailwind.py build
   ```

2. **Collect Static Files:**
   ```bash
   python manage.py collectstatic --noinput
   ```

3. **Clear Browser Cache:**
   - Press `Ctrl+Shift+R` (or `Cmd+Shift+R` on Mac)
   - Or clear browser cache completely

4. **Test the Setup:**
   - Go to: `http://localhost:8000/accounts/test/`
   - This page will show if Tailwind is working

### Common Issues:

#### Issue: Page looks broken, no styling
**Solution:**
- Check if `theme/static/css/dist/styles.css` exists
- Run `python build_tailwind.py build`
- Make sure Django server is running

#### Issue: Custom colors not working
**Solution:**
- Custom colors are now defined in CSS variables in `base.html`
- They should work with classes like `bg-primary`, `text-secondary`, etc.

#### Issue: CDN still loading
**Solution:**
- CDN has been removed from `base.html`
- Only local CSS is being used now

#### Issue: Development mode not working
**Solution:**
```bash
cd theme/static_src
npm run dev
```

### Test Page
Visit `http://localhost:8000/accounts/test/` to see:
- ✅ Standard Tailwind colors (blue, green, red)
- ✅ Custom colors (primary, secondary, accent, danger)
- ✅ Buttons and hover effects
- ✅ Responsive design

### Performance Check
Run the performance checker:
```bash
python performance_check.py
```

This will show:
- Response time
- Page size
- External resources being used
- Performance recommendations

### If Nothing Works:
1. **Fallback to CDN:**
   Add this back to `base.html` temporarily:
   ```html
   <script src="https://cdn.tailwindcss.com"></script>
   ```

2. **Check Node.js:**
   ```bash
   node --version
   npm --version
   ```

3. **Reinstall Dependencies:**
   ```bash
   cd theme/static_src
   rm -rf node_modules package-lock.json
   npm install
   npm run build
   ```

### File Locations:
- **Local CSS:** `theme/static/css/dist/styles.css`
- **Static Files:** `staticfiles/theme/css/dist/styles.css`
- **Config:** `theme/tailwind.config.js`
- **Source:** `theme/static_src/src/styles.css`

### Support:
If you're still having issues, check:
1. Django server logs
2. Browser console for errors
3. Network tab for failed requests
4. File permissions on generated CSS files 