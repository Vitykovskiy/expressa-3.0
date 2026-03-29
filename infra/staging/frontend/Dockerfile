FROM node:24-alpine AS build

WORKDIR /app
COPY apps/customer-web/package.json apps/customer-web/package-lock.json* ./
RUN npm install
COPY apps/customer-web/ ./
RUN npm run build

FROM nginx:1.27-alpine

COPY infra/staging/frontend/default.conf /etc/nginx/conf.d/default.conf
COPY --from=build /app/dist /usr/share/nginx/html
EXPOSE 80
