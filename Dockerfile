FROM nginx:alpine-slim

COPY target/rss.xml /usr/share/nginx/html
