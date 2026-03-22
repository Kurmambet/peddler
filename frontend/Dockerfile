# # Stage 1: Сборка приложения для прода (скорее всего надо будет менять)
# FROM node:20-alpine as build-stage

# WORKDIR /app

# # Копируем файлы зависимостей
# COPY package*.json ./

# # Устанавливаем зависимости
# RUN npm install

# # Копируем исходный код
# COPY . .

# # Задаем базовый URL для API (важно для Nginx проксирования)
# # В продакшене фронт будет обращаться к /api, а Nginx перенаправит запрос на бэкенд
# ENV VITE_API_URL=/api/v1

# # Собираем проект
# RUN npm run build

# # Stage 2: Запуск в Nginx
# FROM nginx:alpine as production-stage

# # Копируем собранные файлы из предыдущего этапа
# COPY --from=build-stage /app/dist /usr/share/nginx/html

# # Копируем наш конфиг nginx
# COPY nginx.conf /etc/nginx/conf.d/default.conf

# EXPOSE 80

# CMD ["nginx", "-g", "daemon off;"]



# FROM node:20-alpine

# WORKDIR /app

# # Копируем только package.json для кэширования слоев
# COPY package*.json ./
# RUN npm install
# COPY . .

# # Открываем порт Vite
# EXPOSE 5173

# # Запускаем в режиме разработки с флагом --host, 
# # чтобы Vite был доступен извне контейнера
# CMD ["npm", "run", "dev", "--", "--host"]
