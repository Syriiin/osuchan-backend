# osu!chan backend API

## Requirements

- Docker (and docker-compose)

## Setup

1. Add a custom domain to your host machine hosts file that resolves to localhost
2. Create an osu apiv2 oauth client [from your osu! account settings](https://osu.ppy.sh/home/account/edit) for your development environment with the redirect uri as `<custom host>:3000/osuauth/callback` where `<custom host>` is the host you defined in the previous step (port 3000 is used because it is the default used by the web app development server which will proxy through to the backend)
3. Make a copy of `local_settings.template.py` named `local_settings.py` and modify contents for sensitive/environment-specific info (and ensure it isn't being committed)
4. Configure beatmap cache volume permissions (may need `sudo`)
    ```shell
    $ mkdir -p data/beatmaps    # create volume directory
    $ chown 5678 data/beatmaps  # change ownership to uid 5678 (explicit id of user running api inside container)
    $ chmod 600 data/beatmaps   # change permissions to only allow read/write for owner
    ```
5. Run migrations
    ```shell
    $ scripts/migrate
    ```
6. Start server
    ```shell
    $ docker-compose up
    ```
