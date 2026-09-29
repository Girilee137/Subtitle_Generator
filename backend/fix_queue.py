import asyncio
from app.db.session import async_session
from sqlalchemy import text

async def main():
    async with async_session() as s:
        result = await s.execute(
            text("UPDATE queued_tasks SET queue_name = 'default' WHERE queue_name = 'gpu' AND status = 'QUEUED'")
        )
        await s.commit()
        print(f"Fixed {result.rowcount} stuck task(s): moved gpu->default queue")

asyncio.run(main())
