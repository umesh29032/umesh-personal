# Kapil Enterprises - Business Management System

A comprehensive business management system built with Django for Kapil Enterprises. This application helps manage inventory, users, and business operations efficiently.

## Features

- **User Authentication**: Secure login and registration system with email verification
- **Role-Based Access Control**: Different user types (Admin, Supplier, Karigar, Kapde Wala) with specific permissions
- **Dashboard**: Interactive dashboard with business metrics and quick actions
- **User Management**: Add, edit, and remove users with different roles
- **Skills Management**: Track and manage employee skills
- **Responsive Design**: Works seamlessly on desktop and mobile devices
- **Google Authentication**: Sign in with Google account

## Tech Stack

- **Backend**: Django 5.2
- **Database**: PostgreSQL
- **Frontend**: Tailwind CSS
- **Authentication**: Django AllAuth
- **API**: Django REST Framework
- **Caching**: Redis

## Installation

### Prerequisites

- Python 3.10+
- PostgreSQL
- Redis (optional, for caching)
- Node.js and npm (for Tailwind CSS)

### Setup

1. Clone the repository:
   ```bash
   git clone https://github.com/your-username/kapil-enterprises.git
   cd kapil-enterprises
   ```

2. Create and activate a virtual environment:
   ```bash
   python -m venv env
   source env/bin/activate  # On Windows: env\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Create a `.env` file in the project root with the following variables:
   ```
   SECRET_KEY=your_secret_key
   DEBUG=True
   DATABASE_NAME=mydb
   DATABASE_USER=myuser
   DATABASE_PASSWORD=mypassword
   DATABASE_HOST=localhost
   DATABASE_PORT=5432
   GOOGLE_CLIENT_ID=your_google_client_id
   GOOGLE_SECRET=your_google_secret
   ```

5. Run migrations:
   ```bash
   python manage.py migrate
   ```

6. Create a superuser:
   ```bash
   python manage.py createsuperuser
   ```

7. Install and build Tailwind CSS:
   ```bash
   python manage.py tailwind install
   python manage.py tailwind build
   ```

8. Run the development server:
   ```bash
   python manage.py runserver
   ```

Visit `http://127.0.0.1:8000/` in your browser to access the application.

## Development

### Tailwind CSS

To watch for changes in Tailwind CSS:

```bash
python manage.py tailwind start
```

### Running Tests

```bash
python manage.py test
```

## Project Structure

```
myproject/
├── accounts/            # User authentication and management
├── core/                # Core functionality and utilities
├── myproject/           # Project settings and main URLs
├── templates/           # Global templates
├── theme/               # Tailwind CSS configuration
├── staticfiles/         # Collected static files
├── media/               # User-uploaded files
├── DOCUMENTATION.md     # Comprehensive project documentation
└── update_docs.py       # Script to update documentation
```

## Documentation

This project maintains detailed documentation in the `DOCUMENTATION.md` file, which includes:
- Project overview
- Technology stack
- Key features
- Project structure
- Changelog of all updates
- User roles and permissions
- Database schema
- API endpoints
- Installation and setup instructions
- Development guidelines
- Deployment instructions
- Troubleshooting tips
- Future enhancement plans

### Updating Documentation

To keep the documentation up to date, use the provided script:

```bash
# Make the script executable (first time only)
chmod +x update_docs.py

# Run the script to add new changes to the documentation
./update_docs.py
```

The script will guide you through adding new changes to the documentation in a structured format.

## Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is proprietary and confidential. Unauthorized copying, distribution, or use is strictly prohibited.

## Contact

For support or inquiries, please contact support@kapilenterprises.com
