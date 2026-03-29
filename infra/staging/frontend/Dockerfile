FROM node:24-alpine AS customer-build

WORKDIR /app
COPY apps/customer-web/package.json apps/customer-web/package-lock.json* ./
RUN npm install
COPY apps/customer-web/ ./
RUN npm run build

FROM node:24-alpine AS backoffice-build

WORKDIR /app
COPY apps/backoffice-web/package.json apps/backoffice-web/package-lock.json* ./
RUN npm install
COPY apps/backoffice-web/ ./
RUN npm run build

FROM nginx:1.27-alpine

COPY infra/staging/frontend/default.conf /etc/nginx/conf.d/default.conf
COPY --from=customer-build /app/dist /usr/share/nginx/html
COPY --from=backoffice-build /app/dist /usr/share/nginx/html/backoffice
EXPOSE 80
