# Dockerfile for the React frontend component

# Stage 1: Build the React app
FROM node:16 AS build

# Set working directory
WORKDIR /app

# Copy package.json and package-lock.json
COPY package*.json ./

# Install dependencies
RUN rm -rf node_modules && rm -rf package-lock.json
RUN npm install
RUN npm install --save-dev babel-loader @babel/core @babel/preset-env @babel/preset-react
RUN npm install rc-tree 

# Copy the rest of the application
COPY . .

# Build the application
RUN npm run build

# Stage 2: Serve the built React app using nginx
#FROM nginx:alpine

# Copy the built React app from Stage 1
#COPY --from=build /app/build /usr/share/nginx/html

# Copy the nginx configuration file
#COPY nginx.conf /etc/nginx/nginx.conf

# Expose the default port for nginx
EXPOSE 80

# Start nginx
CMD ["nginx", "-g", "daemon off;"]
