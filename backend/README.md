(backend) C:\projects\peddler\peddler\backend>uv add fastapi sqlalchemy uvicorn[standard] daphne asyncpg alembic python-jose[cryptography] passlib python-dotenv redis aioredis pydantic pydantic-settings python-dateutil pytest pytest-asyncio httpx black flake8 mypy

uv run uvicorn app.main:app --reload

C:\Users\pitrv>tasklist | findstr uvicorn
uvicorn.exe 8200 Console 5 4 548 КБ

C:\Users\pitrv>taskkill /PID 8200 /F
Успешно: Процесс, с идентификатором 8200, успешно завершен.

curl -X POST <http://127.0.0.1:8000/api/v1/auth/register> ^
-H "Content-Type: application/json" ^
-d "{\"username\": \"userA\", \"password\": \"passA12345\"}"

{"username":"userA","id":2,"is_active":true,"created_at":"2025-11-30T15:48:49.301430Z"}

curl -X POST <http://127.0.0.1:8000/api/v1/auth/register> ^
-H "Content-Type: application/json" ^
-d "{\"username\": \"userB\", \"password\": \"passB12345\"}"

{"username":"userB","id":3,"is_active":true,"created_at":"2025-11-30T15:49:03.507033Z"}

curl -X POST <http://127.0.0.1:8000/api/v1/auth/login> ^
-H "Content-Type: application/json" ^
-d "{\"username\": \"userA\", \"password\": \"passA12345\"}"

{"access_token":"eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIyIiwiaWF0IjoxNzY0NTE3ODQ0LCJleHAiOjE3NjUxMjI2NDR9.eMGWxI4wKat_rD8ist774O2iMWN-lfB4o0OnzdrnUXs","token_type":"bearer"}

curl -X POST <http://127.0.0.1:8000/api/v1/messages> ^
-H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIyIiwiaWF0IjoxNzY0NTE3ODQ0LCJleHAiOjE3NjUxMjI2NDR9.eMGWxI4wKat_rD8ist774O2iMWN-lfB4o0OnzdrnUXs" ^
-H "Content-Type: application/json" ^
-d "{\"receiver_id\": 3, \"content\": \"Привет, как дела?\"}"

{"content":"Привет, как дела?","id":1,"sender_id":2,"receiver_id":3,"is_read":false,"created_at":"2025-11-30T15:52:08.679220Z"}

curl <http://127.0.0.1:8000/api/v1/messages/3> ^
-H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIyIiwiaWF0IjoxNzY0NTE3ODQ0LCJleHAiOjE3NjUxMjI2NDR9.eMGWxI4wKat_rD8ist774O2iMWN-lfB4o0OnzdrnUXs"

[{"content":"Привет, как дела?","id":1,"sender_id":2,"receiver_id":3,"is_read":false,"created_at":"2025-11-30T15:52:08.679220Z"}]
