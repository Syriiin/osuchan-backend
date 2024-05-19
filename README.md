# osu!chan backend API

## Requirements

- Docker

## Setup

1. Add a custom domain to your host machine hosts file that resolves to localhost
2. Create an osu apiv2 oauth client [from your osu! account settings](https://osu.ppy.sh/home/account/edit) for your development environment with the redirect uri as `<custom host>:3000/osuauth/callback` where `<custom host>` is the host you defined in the previous step (port 3000 is used because it is the default used by the web app development server which will proxy through to the backend)
3. Make a copies local config files and modify contents for sensitive/environment-specific info (and ensure it isn't being committed)
   - `local_settings.template.py` -> `local_settings.py`
   - `.env.template` -> `.env`
4. Configure beatmap cache volume permissions (may need `sudo`)
   ```shell
   $ mkdir -p data/beatmaps    # create volume directory
   $ chown 5678 data/beatmaps  # change ownership to uid 5678 (explicit id of user running api inside container)
   $ chmod 700 data/beatmaps   # give full permissions for owner
   ```
5. Run migrations
   ```shell
   $ scripts/manage migrate
   ```
6. Start server
   ```shell
   $ docker compose up
   ```

## Setup dev environment

1. [Install poetry](https://python-poetry.org/docs/)
2. Install dependencies locally (for IDE, code formatting, etc...)
   ```
   $ poetry install
   ```

## Common Issues

### Permission issues

If you get permission issues about the `data` directory when building the image, ensure the `data` directory itself is owned by the running user or atleast has permissions allowing the running user to read, and only have docker volume specific permissions set for the sub directories.

## Additional Notes

### Static files

When running with the production config `compose.prod.yml` gunicorn will be used instead of djangos development server, so static files will need to be manually set up (ie. with a reverse proxy) to be served under the route `/backendstatic/`.
