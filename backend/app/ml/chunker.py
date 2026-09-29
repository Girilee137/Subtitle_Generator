MAX_CHUNK_SECONDS = 30.0


def chunk_intervals(intervals: list[tuple[float, float]]) -> list[tuple[float, float]]:
    chunks: list[tuple[float, float]] = []
    for start, end in intervals:
        cursor = max(0.0, start - 0.3)
        limit = end + 0.3
        while cursor < limit:
            chunk_end = min(cursor + MAX_CHUNK_SECONDS, limit)
            chunks.append((round(cursor, 3), round(chunk_end, 3)))
            cursor = chunk_end
    return chunks
