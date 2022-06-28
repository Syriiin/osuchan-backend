# osu!chan backend API

## Requirements

- Docker

## Setup

1. Add a custom domain to your host machine hosts file that resolves to localhost
2. Create an osu apiv2 oauth client [from your osu! account settings](https://osu.ppy.sh/home/account/edit) for your development environment with the redirect uri as `<custom host>:3000/osuauth/callback` where `<custom host>` is the host you defined in the previous step (port 3000 is used because it is the default used by the web app development server which will proxy through to the backend)
3. Make a copy of `local_settings.template.py` named `local_settings.py` and modify contents for sensitive/environment-specific info (and ensure it isn't being committed)
4. Configure beatmap cache volume permissions (may need `sudo`)
    ```shell
    $ mkdir -p data/beatmaps    # create volume directory
    $ chown 5678 data/beatmaps  # change ownership to uid 5678 (explicit id of user running api inside container)
    $ chmod 600 data/beatmaps   # give atleast read/write permissions for owner
    ```
5. Run migrations
    ```shell
    $ scripts/migrate
    ```
6. Start server
    ```shell
    $ docker compose up
    ```

## Common Issues

### Permission issues

If you get permission issues about the `data` directory when building the image, ensure the `data` directory itself is owned by the running user or atleast has permissions allowing the running user to read, and only have docker volume specific permissions set for the sub directories.


## Additional Notes

### Static files

When running with the production config `docker-compose.prod.yml` gunicorn will be used instead of djangos development server, so static files will need to be manually set up (ie. with a reverse proxy) to be served under the route `/backendstatic/`.
