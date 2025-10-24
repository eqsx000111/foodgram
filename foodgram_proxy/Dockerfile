FROM nginx:1.22.1
COPY nginx.conf /etc/nginx/templates/default.conf.template
COPY docs/ /usr/share/nginx/docs/
RUN chmod -R 755 /usr/share/nginx/docs/