FROM python:3.13-slim-bookworm AS python-base

# Version env vars
ENV POETRY_VERSION="1.8.5"

# Build path env vars
ENV POETRY_PATH="/opt/poetry"
ENV APPDEPS_PATH="/opt/appdeps"
ENV APP_PATH="/app"
ENV BEATMAPS_PATH=/beatmaps

VOLUME ${BEATMAPS_PATH}
# chmod 777 so that this volume can be read/written by other containers that might use different uids
RUN mkdir ${BEATMAPS_PATH} && chmod -R 777 ${BEATMAPS_PATH}

# Poetry env vars
ENV POETRY_INSTALLER_MAX_WORKERS=10
ENV POETRY_VIRTUALENVS_IN_PROJECT=true

# Python env vars
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Update PATH env var (prepend for precedence over global python)
ENV PATH="${APPDEPS_PATH}/.venv/bin:${POETRY_PATH}/bin:$PATH"

# Install tini
RUN apt-get update
RUN apt-get install -y tini

# --------------------------------------------------------------------------------

FROM python-base AS builder

# Install poetry
RUN python -m venv ${POETRY_PATH}
RUN ${POETRY_PATH}/bin/pip install poetry==${POETRY_VERSION}

# Install dependencies
WORKDIR ${APPDEPS_PATH}
COPY pyproject.toml poetry.lock ./
RUN poetry install --only main

# --------------------------------------------------------------------------------

FROM python-base AS tooling

# Install additional tooling packages
RUN apt-get install -y postgresql-client

# Copy in poetry
COPY --from=builder ${POETRY_PATH} ${POETRY_PATH}

# Copy in app dependencies
COPY --from=builder ${APPDEPS_PATH} ${APPDEPS_PATH}

# Install remaining dev dependencies
WORKDIR ${APPDEPS_PATH}
RUN poetry install

# Set workdir to path where code should be mounted
WORKDIR ${APP_PATH}

# Create user to run app
RUN adduser -u 10001 --disabled-password --gecos "" appuser
USER appuser

# --------------------------------------------------------------------------------

FROM tooling AS development-runner

# Run development server
EXPOSE 8000
ENTRYPOINT [ "tini", "--" ]
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000", "--noreload"]

# --------------------------------------------------------------------------------

FROM python-base AS production-runner

# Create user to run app
RUN adduser -u 10001 --disabled-password --gecos "" appuser
USER appuser

# Copy in app dependencies
COPY --from=builder ${APPDEPS_PATH} ${APPDEPS_PATH}

# Copy in source code
WORKDIR ${APP_PATH}
COPY . ./

# Run production server
EXPOSE 8000
ENTRYPOINT [ "tini", "--" ]
CMD ["gunicorn", "--workers", "9", "--timeout", "120", "--bind", "0.0.0.0:8000", "osuchan.wsgi"]
