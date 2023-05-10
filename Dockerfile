FROM python:3.9-slim-buster as python-base

# Version env vars
ENV POETRY_VERSION="1.3.2"

# Build path env vars
ENV POETRY_PATH="/opt/poetry"
ENV APPDEPS_PATH="/opt/appdeps"
ENV APP_PATH="/app"

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
RUN apt-get install tini

# --------------------------------------------------------------------------------

FROM python-base as builder

# Install poetry
RUN python -m venv ${POETRY_PATH}
RUN ${POETRY_PATH}/bin/pip install poetry==${POETRY_VERSION}

# Install dependencies
WORKDIR ${APPDEPS_PATH}
COPY pyproject.toml poetry.lock ./
RUN poetry install --no-dev

# --------------------------------------------------------------------------------

FROM python-base as development-tooling

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

FROM development-tooling as development-runner

# Run development server
EXPOSE 8000
ENTRYPOINT [ "tini", "--" ]
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]

# --------------------------------------------------------------------------------

FROM python-base as production-runner

# Create user to run app
RUN adduser -u 10001 --disabled-password --gecos "" appuser
USER appuser

# Copy in app dependencies
COPY --from=builder ${APPDEPS_PATH} ${APPDEPS_PATH}

# Copy in source code
WORKDIR ${APP_PATH}
COPY . ./

# Build app
RUN python manage.py collectstatic --no-input

# Run production server
EXPOSE 8000
ENTRYPOINT [ "tini", "--" ]
CMD ["gunicorn", "--workers", "5", "--timeout", "120", "--bind", "0.0.0.0:8000", "osuchan.wsgi"]
