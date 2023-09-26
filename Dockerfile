FROM python:3.11-alpine

LABEL org.opencontainers.image.source=https://github.com/sweeneytr/polymer
LABEL org.opencontainers.image.description="Polymer DB Server"
LABEL org.opencontainers.image.licenses=MIT

ARG APP_PATH=/opt/${APP_NAME}

ENV \
  PYTHONDONTWRITEBYTECODE=1 \
  PYTHONUNBUFFERED=1 \
  PYTHONFAULTHANDLER=1

# Don't cache PIP because that cache will bloat the final image
ENV \
  PIP_NO_CACHE_DIR=true \
  PIP_DISABLE_PIP_VERSION_CHECK=true

WORKDIR /opt/polymer
COPY /dist/*.whl ./
COPY requirements.txt ./
COPY alembic.ini ./
COPY alembic/ alembic/
COPY logging.yaml ./

# Install runtime dependencies
RUN apk --no-cache add libpq libstdc++

# Done as one command so we don't increase the size of the final image with the dev packages.
RUN apk --no-cache add git build-base gcc rust cargo musl-dev postgresql-dev libffi-dev \
  && pip install ./polymer*.whl --requirement requirements.txt \
  && apk del git build-base gcc rust cargo musl-dev postgresql-dev libffi-dev

RUN addgroup -S app && adduser -S app -G app
RUN chown -R app:app /opt/polymer
USER app

# export as environment variables for the CMD
ENV APP_NAME=polymer
EXPOSE 8080/tcp

ENTRYPOINT ["uvicorn", "polymer.app:app", "--proxy-headers", "--host=0.0.0.0", "--port=8080"]
CMD [ "--log-config=logging.yaml" ]