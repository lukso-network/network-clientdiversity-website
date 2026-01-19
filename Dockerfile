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

# Production stage - lightweight static server
FROM nginx:alpine

COPY --from=builder /app/_site /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Run as non-root
RUN chown -R nginx:nginx /usr/share/nginx/html
USER nginx

EXPOSE 4000
