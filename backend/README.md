(backend) C:\projects\peddler\peddler\backend>uv add fastapi sqlalchemy uvicorn[standard] daphne asyncpg alembic python-jose[cryptography] passlib[bcrypt] python-dotenv redis aioredis pydantic pydantic-settings python-dateutil pytest pytest-asyncio httpx black flake8 mypy

uv run uvicorn app.main:app --reload
