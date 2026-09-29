import asyncio
from app.db.session import async_session
from sqlalchemy import text

async def main():
    async with async_session() as s:
        # Latest completed job info
        job = (await s.execute(text(
            "SELECT job_id, chunks_total, chunks_done, stage FROM jobs WHERE status='COMPLETED' ORDER BY created_at DESC LIMIT 1"
        ))).one()
        print(f"Job: {job.job_id} | chunks: {job.chunks_done}/{job.chunks_total} | stage: {job.stage}")

        # Track info
        tracks = (await s.execute(text(
            "SELECT track_id, language, kind FROM subtitle_tracks ORDER BY created_at DESC LIMIT 5"
        ))).all()
        for t in tracks:
            print(f"Track: {t.track_id} | lang={t.language} | kind={t.kind}")

        if tracks:
            tid = tracks[0].track_id
            # First 20 segments
            segs = (await s.execute(text(
                f"SELECT idx, start_time, end_time, text FROM subtitle_segments WHERE track_id='{tid}' ORDER BY idx LIMIT 20"
            ))).all()
            print(f"\nFirst 20 segments of track {tid}:")
            for seg in segs:
                print(f"  [{seg.idx}] {seg.start_time:.2f}s-{seg.end_time:.2f}s | {seg.text!r}")

            total = (await s.execute(text(
                f"SELECT COUNT(*) FROM subtitle_segments WHERE track_id='{tid}'"
            ))).scalar()
            print(f"\nTotal segments: {total}")

        # Job chunks - check if results are repeating
        chunks = (await s.execute(text(
            f"SELECT idx, start_s, end_s, status, result FROM job_chunks WHERE job_id='{job.job_id}' ORDER BY idx LIMIT 10"
        ))).all()
        print(f"\nJob chunks ({len(chunks)}):")
        for c in chunks:
            words = c.result.get('words', []) if c.result else []
            preview = ' '.join(w.get('word','') for w in words[:8]) if words else '(empty)'
            print(f"  chunk[{c.idx}] {c.start_s:.1f}-{c.end_s:.1f}s | {len(words)} words | {preview!r}")

asyncio.run(main())
