FROM ruby:3.3-alpine3.20

WORKDIR /app

ENV BUNDLE_PATH=/app/vendor/bundle
ENV BUNDLER_VERSION='2.5.14'

COPY . /app

RUN apk update && \
  apk upgrade && \
  apk add --no-cache jq build-base curl bash python3 && \
  gem install bundler -v $BUNDLER_VERSION

RUN rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/* && \
    truncate -s 0 /var/log/*log

RUN bundle config set --local path 'vendor/bundle'
RUN bundle install

RUN python3 -m venv venv

ENV PATH="/app/venv/bin:$PATH"
RUN pip3 install requests

EXPOSE 4000

ENTRYPOINT ["bundle"]
CMD ["exec", "jekyll", "serve"]

