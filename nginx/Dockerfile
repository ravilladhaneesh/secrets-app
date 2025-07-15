FROM nginx:alpine

RUN echo "Hello"

RUN ls -la

COPY certs/domain.cert.pem /etc/nginx/certs/domain.cert.pem
COPY certs/private.key.pem /etc/nginx/certs/private.key.pem
COPY nginx-default.conf /etc/nginx/conf.d/default.conf

# EXPOSE 80
EXPOSE 443


EXPOSE 5000