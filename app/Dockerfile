FROM node:22-alpine

WORKDIR /app

COPY app/package*.json ./

RUN npm install --production

COPY app/ .

CMD ["node", "server.js"]
