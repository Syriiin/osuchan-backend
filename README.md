# osu!chan backend API

## Requirements

- Python 3 (untested below 3.7.3)


## Setup (bash)

1. Create and enter a virtual environment (recommended)
    ```
    $ python3 -m venv env
    $ source env/Scripts/activate
    ```    
2. Install dependencies
    ```
    $ pip install -r requirements.txt
    ```
3. Setup new PostgreSQL database
4. Make a copy of `local_settings.template.py` named `local_settings.py` and modify contents for sensitive info (and ensure it isn't being committed)
5. Run migrations
    ```
    $ python manage.py migrate
    ```
6. Start development server
    ```
    $ python manage.py runserver
    ```
