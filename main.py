import os
import sys
import rumps
import sqlite3
from datetime import datetime
from openai import OpenAI


class ChatToolbar(rumps.App):
    def __init__(self):
        super(ChatToolbar, self).__init__("💭")
        self.api_key = os.environ.get("OPENAI_API_KEY")
        self.client = None
        self.setup_database()
        self.setup_client()

    def setup_client(self):
        try:
            self.client = OpenAI(api_key=self.api_key)
        except Exception as e:
            rumps.alert("API Key Error", "Please set your OpenAI API key in settings.")

    def setup_database(self):
        # ... existing database setup code ...

        # Add settings table
        self.cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS settings (
                key TEXT PRIMARY KEY,
                value TEXT
            )
        """
        )
        self.conn.commit()

    @rumps.clicked("New Chat")
    def new_chat(self, _):
        # Get available contexts
        self.cursor.execute("SELECT name FROM contexts")
        contexts = self.cursor.fetchall()
        context_names = [c[0] for c in contexts]

        # Create context selection window if contexts exist
        selected_context = None
        if context_names:
            context_response = rumps.Window(
                message="Select context (optional):",
                title="Use Context",
                default_text="",
                ok="Select",
                cancel="Skip",
                dimensions=(300, 100),
            ).run()
            if context_response.clicked and context_response.text in context_names:
                self.cursor.execute(
                    "SELECT content FROM contexts WHERE name = ?",
                    (context_response.text,),
                )
                selected_context = self.cursor.fetchone()[0]

        # Create query window
        response = rumps.Window(
            message="Enter your query:",
            title="Chat",
            default_text="",
            ok="Send",
            dimensions=(300, 100),
        ).run()

        if response.clicked:
            query = response.text
            if selected_context:
                query = f"Context: {selected_context}\n\nQuery: {query}"

            chat_response = self.get_chat_response(query)
            if chat_response:
                self.store_chat(query, chat_response)
                rumps.Window(message=chat_response, title="Response", ok="Close").run()

    @rumps.clicked("View History")
    def view_history(self, _):
        # Get last 10 chats
        self.cursor.execute(
            """
            SELECT timestamp, query, response
            FROM chats
            ORDER BY timestamp DESC
            LIMIT 10
        """
        )
        chats = self.cursor.fetchall()

        if not chats:
            rumps.alert("No History", "No chat history found.")
            return

        history_text = "\n\n".join(
            [
                f"Time: {chat[0]}\nQuery: {chat[1]}\nResponse: {chat[2]}"
                for chat in chats
            ]
        )

        rumps.Window(
            message=history_text,
            title="Chat History",
            ok="Close",
            dimensions=(500, 400),
        ).run()

    @rumps.clicked("Manage Contexts")
    def manage_contexts_menu(self, _):
        # Submenu for context management
        self.cursor.execute("SELECT name, content FROM contexts")
        contexts = self.cursor.fetchall()

        options = ["Add New Context"]
        if contexts:
            options.append("Delete Context")
            options.append("View Contexts")

        response = rumps.Window(
            message="Select action:",
            title="Manage Contexts",
            default_text="",
            ok="Select",
            cancel="Cancel",
            dimensions=(300, 100),
        ).run()

        if response.clicked:
            if response.text == "Add New Context":
                self.add_context()
            elif response.text == "Delete Context":
                self.delete_context()
            elif response.text == "View Contexts":
                self.view_contexts()

    def add_context(self):
        response = rumps.Window(
            message="Enter context name and content (name:content):",
            title="Add Context",
            default_text="",
            ok="Save",
            dimensions=(300, 100),
        ).run()

        if response.clicked and ":" in response.text:
            name, content = response.text.split(":", 1)
            self.cursor.execute(
                "INSERT INTO contexts (name, content) VALUES (?, ?)",
                (name.strip(), content.strip()),
            )
            self.conn.commit()
            rumps.alert("Success", f"Context '{name.strip()}' added!")

    def delete_context(self):
        self.cursor.execute("SELECT name FROM contexts")
        contexts = [c[0] for c in self.cursor.fetchall()]

        if not contexts:
            rumps.alert("No Contexts", "No contexts to delete.")
            return

        response = rumps.Window(
            message="Select context to delete:",
            title="Delete Context",
            default_text="",
            ok="Delete",
            cancel="Cancel",
            dimensions=(300, 100),
        ).run()

        if response.clicked and response.text in contexts:
            self.cursor.execute("DELETE FROM contexts WHERE name = ?", (response.text,))
            self.conn.commit()
            rumps.alert("Success", f"Context '{response.text}' deleted!")

    def view_contexts(self):
        self.cursor.execute("SELECT name, content FROM contexts")
        contexts = self.cursor.fetchall()

        if not contexts:
            rumps.alert("No Contexts", "No contexts found.")
            return

        contexts_text = "\n\n".join(
            [f"Name: {ctx[0]}\nContent: {ctx[1]}" for ctx in contexts]
        )

        rumps.Window(
            message=contexts_text,
            title="Stored Contexts",
            ok="Close",
            dimensions=(400, 300),
        ).run()

    @rumps.clicked("Settings")
    def settings(self, _):
        response = rumps.Window(
            message="Enter OpenAI API Key:",
            title="Settings",
            default_text=self.api_key or "",
            ok="Save",
            dimensions=(300, 100),
            secure=True,
        ).run()

        if response.clicked:
            self.api_key = response.text
            self.cursor.execute(
                "INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)",
                ("openai_api_key", self.api_key),
            )
            self.conn.commit()
            self.setup_client()
            rumps.alert("Success", "API key updated!")

    def get_chat_response(self, query):
        if not self.client:
            rumps.alert("Error", "Please set your OpenAI API key in settings.")
            return None

        try:
            chat_completion = self.client.chat.completions.create(
                messages=[{"role": "user", "content": query}],
                model="gpt-4-turbo-preview",
            )
            return chat_completion.choices[0].message.content
        except Exception as e:
            rumps.alert("Error", f"Failed to get response: {str(e)}")
            return None

    def store_chat(self, query, response):
        self.cursor.execute(
            "INSERT INTO chats (timestamp, query, response) VALUES (?, ?, ?)",
            (datetime.now(), query, response),
        )
        self.conn.commit()


if __name__ == "__main__":
    ChatToolbar().run()
