# osu!chan backend API

## Requirements

- Python 3 (untested below 3.7.3)


## Setup (bash)

1. Create and enter a virtual environment (recommended)
    ```shell
    $ python3 -m venv env
    $ source env/Scripts/activate
    ```    
2. Install dependencies
    ```shell
    $ pip install -r requirements.txt
    ```
3. Setup new PostgreSQL database
    1. Install PostgreSQL (if using local database)
    2. Enter psql shell
    3. Create a new database
        ```sql
        CREATE DATABASE osuchan;
        ```
    4. Create a new user for django
        ```sql
        CREATE USER django WITH PASSWORD 'password';
        ```
    5. Modify user connection parameters
        ```sql
        ALTER ROLE django SET client_encoding TO 'utf8';
        ALTER ROLE django SET default_transaction_isolation TO 'read committed';
        ALTER ROLE django SET timezone TO 'UTC';
        ```
    6. Give django user all permissions on database
        ```sql
        GRANT ALL PRIVILEGES ON DATABASE osuchan TO django;
        ```
4. Add a custom domain to your hosts file that resolves to localhost
5. Create an [osu apiv2 oauth client](https://github.com/int-and-his-friends/osu-api-v2/wiki/Oauth-clients) for your development environment with the redirect uri as `<custom host>/osuauth/callback` where `<custom host>` is the host you defined in the previous step
6. Make a copy of `local_settings.template.py` named `local_settings.py` and modify contents for sensitive/environment-specific info (and ensure it isn't being committed)
7. Run migrations
    ```shell
    $ python manage.py migrate
    ```
8. Start development server
    ```shell
    $ python manage.py runserver
    ```
