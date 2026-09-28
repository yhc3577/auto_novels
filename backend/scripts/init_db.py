"""init_db.py — 一键初始化所有 ORM 表.

用法：
    cd backend
    PYTHONPATH=. .venv/bin/python -m scripts.init_db

效果：
    按 Base.metadata.create_all 创建所有未存在的表（projects / chapters /
    chapter_records / users）。

注意：
    这是 demo 阶段的简化方案。生产环境应使用 Alembic 做版本化迁移。
    已存在的表不会被修改（不会加字段、改类型）。
"""

from __future__ import annotations

import asyncio

from sqlalchemy import text

from app.db import dispose_engine, get_engine
from app.models import Base  # noqa: F401  触发所有 model 注册到 Base.metadata
# 显式 import 各 model 确保它们被注册
from app.models import Chapter, ChapterRecord, Project, User  # noqa: F401


async def main() -> None:
    engine = get_engine()
    async with engine.begin() as conn:
        # 先打印当前有哪些表
        existing = (await conn.execute(
            text("SELECT tablename FROM pg_tables WHERE schemaname='public'")
        )).scalars().all()
        print(f"[init_db] existing tables: {sorted(existing) or '(none)'}")

        # create_all 只创建缺失的表，不动已有表
        await conn.run_sync(Base.metadata.create_all)
        print("[init_db] create_all done.")

        existing_after = (await conn.execute(
            text("SELECT tablename FROM pg_tables WHERE schemaname='public'")
        )).scalars().all()
        print(f"[init_db] tables now: {sorted(existing_after)}")

    await dispose_engine()


if __name__ == "__main__":
    asyncio.run(main())