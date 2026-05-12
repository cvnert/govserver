FROM node:22-alpine AS builder

WORKDIR /app

COPY package.json package-lock.json /app/
RUN npm config set registry https://registry.npmmirror.com
RUN npm ci

COPY . /app

ARG VITE_API_BASE=/api
ENV VITE_API_BASE=$VITE_API_BASE

RUN npm run build

FROM nginx:1.27-alpine

COPY nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=builder /app/dist /usr/share/nginx/html

EXPOSE 80
