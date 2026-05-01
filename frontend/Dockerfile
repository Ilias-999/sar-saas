# Build arguments
ARG NGINX_IMAGE=nginx:alpine
ARG APP_PORT=80

FROM ${NGINX_IMAGE}

# Set environment variables
ENV NGINX_PORT=${APP_PORT}

COPY ./public /usr/share/nginx/html
COPY ./nginx.conf /etc/nginx/conf.d/default.conf

# Expose port
EXPOSE ${APP_PORT}
