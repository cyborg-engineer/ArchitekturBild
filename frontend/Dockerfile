FROM node:20-alpine

WORKDIR /app/frontend

ARG NEXT_PUBLIC_API_BASE_URL=http://localhost:8000
ENV NEXT_PUBLIC_API_BASE_URL=$NEXT_PUBLIC_API_BASE_URL

COPY frontend/package.json ./package.json
COPY frontend/package-lock.json ./package-lock.json

RUN npm ci

COPY frontend ./

RUN npm run build

EXPOSE 3000

CMD ["npm", "run", "start", "--", "--hostname", "0.0.0.0", "--port", "3000"]
