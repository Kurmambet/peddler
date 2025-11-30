(backend) C:\projects\peddler\peddler\backend>uv add fastapi sqlalchemy uvicorn[standard] daphne asyncpg alembic python-jose[cryptography] passlib python-dotenv redis aioredis pydantic pydantic-settings python-dateutil pytest pytest-asyncio httpx black flake8 mypy

uv run uvicorn app.main:app --reload

C:\Users\pitrv>tasklist | findstr uvicorn
uvicorn.exe 8200 Console 5 4 548 КБ

C:\Users\pitrv>taskkill /PID 8200 /F
Успешно: Процесс, с идентификатором 8200, успешно завершен.
