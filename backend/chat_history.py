from fastapi import APIRouter, Header, HTTPException, Request
from psycopg import AsyncConnection
from psycopg.rows import DictRow
from psycopg_pool import AsyncConnectionPool

from utils.google_auth import GoogleIdentity, verify_google_credential

router = APIRouter()


async def setup_chat_history(
    pool: AsyncConnectionPool[AsyncConnection[DictRow]],
) -> None:
    async with pool.connection() as conn:
        await conn.execute(
            """
            CREATE TABLE IF NOT EXISTS stride_users (
                google_sub TEXT PRIMARY KEY,
                email TEXT NOT NULL,
                created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
                updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
            )
            """
        )
        await conn.execute(
            """
            CREATE TABLE IF NOT EXISTS stride_chats (
                google_sub TEXT NOT NULL
                    REFERENCES stride_users (google_sub) ON DELETE CASCADE,
                chat_id TEXT NOT NULL,
                title TEXT NOT NULL,
                created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
                updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
                PRIMARY KEY (google_sub, chat_id)
            )
            """
        )
        await conn.execute(
            """
            CREATE TABLE IF NOT EXISTS stride_chat_messages (
                id BIGSERIAL PRIMARY KEY,
                google_sub TEXT NOT NULL,
                chat_id TEXT NOT NULL,
                role TEXT NOT NULL CHECK (role IN ('user', 'assistant')),
                content TEXT NOT NULL,
                created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
                FOREIGN KEY (google_sub, chat_id)
                    REFERENCES stride_chats (google_sub, chat_id)
                    ON DELETE CASCADE
            )
            """
        )
        await conn.execute(
            """
            CREATE INDEX IF NOT EXISTS stride_chat_messages_order_idx
            ON stride_chat_messages (google_sub, chat_id, id)
            """
        )


async def store_chat_message(
    pool: AsyncConnectionPool[AsyncConnection[DictRow]],
    identity: GoogleIdentity,
    chat_id: str,
    role: str,
    content: str,
) -> None:
    async with pool.connection() as conn:
        await conn.execute(
            """
            INSERT INTO stride_users (google_sub, email)
            VALUES (%s, %s)
            ON CONFLICT (google_sub)
            DO UPDATE SET email = EXCLUDED.email, updated_at = now()
            """,
            (identity.subject, identity.email),
        )

        if role == "user":
            title = " ".join(content.split())[:80] or "New chat"
            await conn.execute(
                """
                INSERT INTO stride_chats (google_sub, chat_id, title)
                VALUES (%s, %s, %s)
                ON CONFLICT (google_sub, chat_id)
                DO UPDATE SET updated_at = now()
                """,
                (identity.subject, chat_id, title),
            )
        else:
            await conn.execute(
                """
                UPDATE stride_chats
                SET updated_at = now()
                WHERE google_sub = %s AND chat_id = %s
                """,
                (identity.subject, chat_id),
            )

        await conn.execute(
            """
            INSERT INTO stride_chat_messages
                (google_sub, chat_id, role, content)
            VALUES (%s, %s, %s, %s)
            """,
            (identity.subject, chat_id, role, content),
        )


@router.get("/chats")
async def list_chats(
    request: Request,
    authorization: str | None = Header(default=None),
):
    identity = verify_google_credential(authorization)
    pool: AsyncConnectionPool[AsyncConnection[DictRow]] = (
        request.state.context.pool
    )
    async with pool.connection() as conn:
        cursor = await conn.execute(
            """
            SELECT chat_id, title, updated_at
            FROM stride_chats
            WHERE google_sub = %s
            ORDER BY updated_at DESC
            """,
            (identity.subject,),
        )
        chats = await cursor.fetchall()

    return [
        {
            "chat_id": chat["chat_id"],
            "title": chat["title"],
            "updated_at": chat["updated_at"],
        }
        for chat in chats
    ]


@router.get("/chats/{chat_id}")
async def get_chat(
    chat_id: str,
    request: Request,
    authorization: str | None = Header(default=None),
):
    identity = verify_google_credential(authorization)
    pool: AsyncConnectionPool[AsyncConnection[DictRow]] = (
        request.state.context.pool
    )
    async with pool.connection() as conn:
        chat_cursor = await conn.execute(
            """
            SELECT title
            FROM stride_chats
            WHERE google_sub = %s AND chat_id = %s
            """,
            (identity.subject, chat_id),
        )
        chat = await chat_cursor.fetchone()
        if chat is None:
            raise HTTPException(status_code=404, detail="Chat not found.")

        message_cursor = await conn.execute(
            """
            SELECT role, content
            FROM stride_chat_messages
            WHERE google_sub = %s AND chat_id = %s
            ORDER BY id
            """,
            (identity.subject, chat_id),
        )
        messages = await message_cursor.fetchall()

    return {
        "chat_id": chat_id,
        "title": chat["title"],
        "messages": [
            {"role": message["role"], "content": message["content"]}
            for message in messages
        ],
    }
