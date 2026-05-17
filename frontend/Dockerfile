FROM node:22-slim

WORKDIR /usr/src/app

ENV PATH /usr/src/app/node_modules/.bin:$PATH

COPY package.json .

RUN npm i

COPY . .

# start app
CMD ["vite", "--host"]