FROM node:24-alpine AS build

WORKDIR /app

ARG API_BASE_URL
ARG WS_BASE_URL
ARG NODE_ENV=development

# Copy package files first for better layer caching
COPY frontend /app
RUN rm -rf /app/node_modules /app/dist
COPY frontend/package.json frontend/yarn.lock frontend/.yarnrc.yml /app/
RUN corepack enable && yarn --frozen-lockfile

ENV VITE_API_BASE_URL=${API_BASE_URL}
ENV VITE_WS_URL_BASE=${WS_BASE_URL}
ENV NODE_ENV=${NODE_ENV}

# Copy sources and build
RUN yarn build

# Production image
FROM nginx:stable-alpine

COPY --from=build /app/dist /usr/share/nginx/html
COPY frontend/nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80