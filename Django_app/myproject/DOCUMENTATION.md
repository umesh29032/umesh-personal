# Kapil Enterprises - Project Documentation

## Project Overview
This Django-based web application is designed for Kapil Enterprises to manage their business operations, including inventory management, user management, and business analytics.

## Technology Stack
- **Backend**: Django 
- **Frontend**: HTML, CSS, JavaScript, Tailwind CSS
- **Database**: SQLite (Development) / PostgreSQL (Production)
- **Authentication**: Django Authentication + Google OAuth

## Key Features
- User authentication (Email & Google OAuth)
- Role-based access control (Admin, Staff, Karigar)
- Inventory management
- User management
- Skills management for employees
- Dashboard with analytics
- Responsive design for mobile and desktop

## Project Structure
- **accounts/**: User authentication and management
- **core/**: Core functionality and utilities
- **myproject/**: Project settings and main URLs
- **theme/**: Tailwind CSS configuration and styling
- **templates/**: Global templates
- **staticfiles/**: Collected static files

## Changelog

### June 20, 2023
- **UI Enhancements**:
  - Fixed login, register, and Google authentication pages
  - Standardized styling across authentication pages
  - Added consistent 20px top margin to main content area
  - Fixed card icons in dashboard by adding proper sizing (48px × 48px)

### June 18, 2023
- **Dashboard Improvements**:
  - Enhanced header bar with better navigation
  - Added dropdown menu functionality
  - Improved mobile responsiveness
  - Fixed overlapping logo issues
  - Added search functionality
  - Created systematic grid layout for dashboard

### June 15, 2023
- **Authentication System**:
  - Implemented email-based authentication
  - Added Google OAuth integration
  - Created password reset functionality
  - Designed login and registration pages

### June 10, 2023
- **Initial Setup**:
  - Created Django project structure
  - Set up Tailwind CSS
  - Configured user models with custom fields
  - Established basic navigation and layout

## User Roles and Permissions
- **Admin**: Full access to all features and management capabilities
- **Staff**: Access to inventory and limited user management
- **Karigar**: Limited access to assigned tasks and personal information

## Database Schema
- **User**: Extended Django user model with additional fields
- **Skill**: Skills that can be assigned to users
- **UserSkill**: Many-to-many relationship between users and skills

## API Endpoints
- `/api/users/`: User management
- `/api/inventory/`: Inventory management
- `/api/skills/`: Skills management

## Installation and Setup
1. Clone the repository
2. Create a virtual environment: `python -m venv env`
3. Activate the environment: `source env/bin/activate` (Linux/Mac) or `env\Scripts\activate` (Windows)
4. Install dependencies: `pip install -r requirements.txt`
5. Run migrations: `python manage.py migrate`
6. Create a superuser: `python manage.py createsuperuser`
7. Run the development server: `python manage.py runserver`

## Development Guidelines
- Follow PEP 8 style guide for Python code
- Use Tailwind CSS for styling
- Write tests for new features
- Document code changes in this file
- Use Git feature branches for new development

## Deployment
- Collect static files: `python manage.py collectstatic`
- Configure production settings in `settings.py`
- Set up PostgreSQL database for production
- Configure web server (Nginx/Apache) and WSGI server (Gunicorn/uWSGI)

## Troubleshooting
- Check `TROUBLESHOOTING.md` for common issues and solutions
- Ensure proper environment variables are set
- Verify database connections and migrations
- Check browser console for frontend errors

## Future Enhancements
- Implement advanced reporting and analytics
- Add customer relationship management (CRM) features
- Integrate payment processing
- Develop mobile application
- Implement real-time notifications

## Contact
For any questions or support, contact the development team at [email protected] 