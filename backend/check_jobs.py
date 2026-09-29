import asyncio
from app.db.session import async_session
from sqlalchemy import text

async def main():
    async with async_session() as s:
        r = await s.execute(text(
            "SELECT status, stage, progress, error FROM jobs ORDER BY created_at DESC LIMIT 3"
        ))
        for row in r:
            print(f"status={row.status} stage={row.stage} progress={row.progress:.1f}% error={row.error}")

asyncio.run(main())
