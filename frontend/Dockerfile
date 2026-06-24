# Stage 1: build
FROM node:22-slim AS builder

WORKDIR /usr/src/app

ENV PATH /usr/src/app/node_modules/.bin:$PATH

COPY package.json ./

RUN npm install

COPY . .

RUN npm run build

# Stage 2: serve with nginx
FROM nginx:1.25-alpine

COPY --from=builder /usr/src/app/dist /usr/share/nginx/html

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
