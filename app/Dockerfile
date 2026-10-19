# Stage 1: run the unit tests. A failing test fails the image build,
# so a broken commit never reaches the registry.
ARG BASE_IMAGE=node:22-alpine
FROM ${BASE_IMAGE} AS test
WORKDIR /app
COPY . .
RUN node --test && touch /tmp/tests-passed

# Stage 2: runtime image
FROM ${BASE_IMAGE}
WORKDIR /app
ARG GIT_SHA=dev
ENV GIT_SHA=$GIT_SHA \
    NODE_ENV=production \
    PORT=3000
COPY --from=test /tmp/tests-passed /tmp/tests-passed
COPY package.json server.js version.json ./
COPY public ./public
USER node
EXPOSE 3000
CMD ["node", "server.js"]
