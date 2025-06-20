# check my postgrey server is working or not
systemctl status postgresql
<!-- if not working how to run that? -->
# PostgreSQL Database Setup and Management

This is a quick guide to setting up and managing the PostgreSQL database for this project.

## Quick Commands Cheatsheet

Here are all the necessary commands in one place.

```bash
# --- 1. PostgreSQL Server Management ---

# Check if PostgreSQL server is running
systemctl status postgresql

# Start the PostgreSQL server if it's not running
sudo systemctl start postgresql

# (Optional) Enable the server to start automatically on system boot
sudo systemctl enable postgresql


# --- 2. View Databases & Users ---

# List all existing databases
sudo -u postgres psql -c "\l"

                             List of databases
   Name    |  Owner   | Encoding | Collate | Ctype |   Access privileges   
-----------+----------+----------+---------+-------+-----------------------
 mydb      | postgres | UTF8     | en_IN   | en_IN | =Tc/postgres         +
           |          |          |         |       | postgres=CTc/postgres+
           |          |          |         |       | myuser=CTc/postgres
 postgres  | postgres | UTF8     | en_IN   | en_IN | 
 template0 | postgres | UTF8     | en_IN   | en_IN | =c/postgres          +
           |          |          |         |       | postgres=CTc/postgres
 template1 | postgres | UTF8     | en_IN   | en_IN | =c/postgres          +
           |          |          |         |       | postgres=CTc/postgres
(4 rows)

# List all existing users (roles)
sudo -u postgres psql -c "\du"


# --- 3. Reset User Password ---

# To reset a password, you first need to log into the psql shell.
# Replace 'your_username' and 'your_new_password' with your actual credentials.
sudo -u postgres psql -c "ALTER USER your_username WITH PASSWORD 'your_new_password';"

# Example:
# sudo -u postgres psql -c "ALTER USER myuser WITH PASSWORD 'supersecret123';"


# --- 4. Restore Database from Backup ---

# This command restores the database from the latest backup file.
# Make sure you have created the database and user first.
# It will prompt for the password of the user you specify (-U).

# a. (If needed) Create a new database and user first
# sudo -u postgres psql -c "CREATE DATABASE myproject;"
# sudo -u postgres psql -c "CREATE USER myuser WITH PASSWORD 'mypassword';"
# sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE myproject TO myuser;"

# b. Restore the database from the .sql file
psql -U myuser -d myproject -f mydb_backup_20250620.sql
```

## How to Connect with pgAdmin

1.  **Open pgAdmin**.
2.  Right-click on **Servers** -> **Create** -> **Server...**.
3.  **General Tab**: Give it a name (e.g., "Local Django Project").
4.  **Connection Tab**:
    *   **Host**: `localhost`
    *   **Port**: `5432`
    *   **Maintenance Database**: `myproject`
    *   **Username**: The username you created (e.g., `myuser`).
    *   **Password**: The password you set for that user.
5.  Click **Save**.

<!-- connection failed: connection to server at "127.0.0.1", port 5432 failed: FATAL: no pg_hba.conf entry for host "127.0.0.1", user "myuser", database "postgres", SSL encryption
connection to server at "127.0.0.1", port 5432 failed: FATAL: no pg_hba.conf entry for host "127.0.0.1", user "myuser", database "postgres", no encryption -->
echo 'host    all             all             127.0.0.1/32            md5' | sudo tee -a /etc/postgresql/14/main/pg_hba.conf
