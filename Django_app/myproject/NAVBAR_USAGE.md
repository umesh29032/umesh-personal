# Navbar Auto-Opening Feature

## How to Use

To make the navbar automatically open on any page, simply add this block to your template:

```html
{% block keep_nav_open %}true{% endblock %}
```

## Example

```html
{% extends 'accounts/base.html' %}
{% block title %}Your Page Title{% endblock %}
{% block keep_nav_open %}true{% endblock %}
{% block content %}
    <!-- Your page content here -->
{% endblock %}
```

## How It Works

1. **Template Block**: The `keep_nav_open` block sets a data attribute on the body element
2. **CSS**: When `data-keep-nav-open="true"`, the navbar automatically opens on desktop
3. **JavaScript**: The page highlighting logic automatically highlights the current page
4. **Responsive**: On mobile devices, the navbar stays closed by default

## Current Pages with Auto-Opening Navbar

- ✅ `home.html` - Home page
- ✅ `login.html` - Login page  
- ✅ `register.html` - Registration page
- ✅ `user_list.html` - User list page

## Features

- **Automatic Opening**: Navbar opens automatically on desktop when `keep_nav_open` is set to `true`
- **Page Highlighting**: Current page is automatically highlighted in the navigation
- **Submenu Support**: If current page is in a submenu, the submenu opens automatically
- **Responsive**: Works properly on both desktop and mobile devices
- **Smooth Animations**: All transitions are smooth and professional

## Adding to New Pages

Just add this line to any template that extends `base.html`:

```html
{% block keep_nav_open %}true{% endblock %}
```

That's it! The navbar will automatically open and highlight the current page. 