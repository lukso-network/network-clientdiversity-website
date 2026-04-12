FROM ruby:3.3-alpine3.20 AS builder

WORKDIR /app

ENV BUNDLE_PATH=/app/vendor/bundle
ENV BUNDLER_VERSION='2.5.14'

COPY . /app

RUN apk add --no-cache jq build-base curl bash python3 && \
    gem install bundler -v $BUNDLER_VERSION

RUN bundle config set --local path 'vendor/bundle' && \
    bundle install

RUN python3 -m venv venv
ENV PATH="/app/venv/bin:$PATH"
RUN pip3 install requests

RUN bundle exec jekyll build

# Production stage - lightweight Python server
FROM python:3.12-alpine

WORKDIR /app

COPY --from=builder /app/_site /app/_site
COPY server.py /app/server.py

# Create non-root user
RUN adduser -D -u 1000 appuser && \
    chown -R appuser:appuser /app
USER appuser

ENV PORT=4000
ENV STATIC_DIR=/app/_site
ENV DATA_PATH=/data

EXPOSE 4000

CMD ["python", "/app/server.py"]
