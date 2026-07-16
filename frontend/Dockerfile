FROM node:22-alpine

WORKDIR /app

# Install deps first for layer caching.
COPY package.json ./
RUN npm install

COPY . .

EXPOSE 5173

# Dev server; compose overrides with an install+dev command against the bind mount.
CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0", "--port", "5173"]
