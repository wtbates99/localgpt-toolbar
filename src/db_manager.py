import sqlite3
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional, Generator


@dataclass
class ChatMessage:
    id: Optional[int]
    user_message: str
    assistant_message: str
    context_id: Optional[int]
    timestamp: datetime
    thread_id: Optional[int]
    context_name: Optional[str] = None


@dataclass
class Context:
    id: Optional[int]
    name: str
    content: str
    created_at: datetime
    updated_at: datetime


class DatabaseManager:
    def __init__(self, db_path: str):
        self.db_path = db_path
        self._initialize_db()

    @contextmanager
    def get_connection(self) -> Generator[sqlite3.Connection, None, None]:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
        finally:
            conn.close()

    def _initialize_db(self) -> None:
        with self.get_connection() as conn:
            conn.executescript(
                """
                CREATE TABLE IF NOT EXISTS contexts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL UNIQUE,
                    content TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );

                CREATE TABLE IF NOT EXISTS chat_messages (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_message TEXT NOT NULL,
                    assistant_message TEXT NOT NULL,
                    context_id INTEGER,
                    thread_id INTEGER,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (context_id) REFERENCES contexts (id)
                );

                CREATE INDEX IF NOT EXISTS idx_chat_thread_id ON chat_messages(thread_id);
                CREATE INDEX IF NOT EXISTS idx_chat_timestamp ON chat_messages(timestamp);
            """
            )

    def add_message(self, message: ChatMessage) -> int:
        with self.get_connection() as conn:
            cursor = conn.execute(
                """
                INSERT INTO chat_messages (user_message, assistant_message, context_id, thread_id, timestamp)
                VALUES (?, ?, ?, ?, ?)
            """,
                (
                    message.user_message,
                    message.assistant_message,
                    message.context_id,
                    message.thread_id,
                    message.timestamp,
                ),
            )
            conn.commit()
            return cursor.lastrowid

    def get_messages(
        self,
        thread_id: Optional[int] = None,
        context_id: Optional[int] = None,
        limit: int = 100,
    ) -> List[ChatMessage]:
        with self.get_connection() as conn:
            query = """
                SELECT * FROM chat_messages
                WHERE thread_id = COALESCE(?, thread_id)
                AND context_id = COALESCE(?, context_id)
                ORDER BY timestamp ASC
                LIMIT ?
            """
            cursor = conn.execute(query, (thread_id, context_id, limit))
            return [ChatMessage(**dict(row)) for row in cursor.fetchall()]

    def get_contexts(self) -> List[Context]:
        with self.get_connection() as conn:
            cursor = conn.execute("SELECT * FROM contexts ORDER BY name")
            contexts = []
            for row in cursor.fetchall():
                row_dict = dict(row)
                # Convert timestamp strings to datetime objects
                row_dict["created_at"] = datetime.fromisoformat(
                    row_dict["created_at"].replace("Z", "+00:00")
                )
                row_dict["updated_at"] = datetime.fromisoformat(
                    row_dict["updated_at"].replace("Z", "+00:00")
                )
                contexts.append(Context(**row_dict))
            return contexts

    def add_context(self, context: Context) -> int:
        with self.get_connection() as conn:
            cursor = conn.execute(
                """
                INSERT INTO contexts (name, content, created_at, updated_at)
                VALUES (?, ?, ?, ?)
                """,
                (context.name, context.content, context.created_at, context.updated_at),
            )
            conn.commit()
            return cursor.lastrowid

    def update_context(self, context: Context) -> None:
        with self.get_connection() as conn:
            conn.execute(
                """
                UPDATE contexts
                SET content = ?, updated_at = ?
                WHERE id = ?
                """,
                (context.content, context.updated_at, context.id),
            )
            conn.commit()

    def delete_context(self, context_id: int) -> None:
        with self.get_connection() as conn:
            conn.execute("DELETE FROM contexts WHERE id = ?", (context_id,))
            conn.commit()

    def search_messages(
        self, query: str, search_type: str = "All", limit: int = 50
    ) -> List[ChatMessage]:
        """Search messages containing the given query."""
        with self.get_connection() as conn:
            sql_query = """
                SELECT m.*, c.name as context_name
                FROM chat_messages m
                LEFT JOIN contexts c ON m.context_id = c.id
                WHERE
            """

            if search_type == "User Messages":
                sql_query += "m.user_message LIKE ?"
            elif search_type == "Assistant Responses":
                sql_query += "m.assistant_message LIKE ?"
            else:  # All
                sql_query += "(m.user_message LIKE ? OR m.assistant_message LIKE ?)"

            sql_query += """
                ORDER BY m.timestamp DESC
                LIMIT ?
            """

            if search_type == "All":
                params = (f"%{query}%", f"%{query}%", limit)
            else:
                params = (f"%{query}%", limit)

            cursor = conn.execute(sql_query, params)
            rows = cursor.fetchall()
            messages = []
            for row in rows:
                row_dict = dict(row)
                # Extract context_name before creating ChatMessage
                context_name = row_dict.pop("context_name", None)
                # Convert timestamp string to datetime object
                if isinstance(row_dict["timestamp"], str):
                    row_dict["timestamp"] = datetime.fromisoformat(
                        row_dict["timestamp"].replace("Z", "+00:00")
                    )
                # Create ChatMessage with the remaining fields
                message = ChatMessage(**row_dict, context_name=context_name)
                messages.append(message)
            return messages
