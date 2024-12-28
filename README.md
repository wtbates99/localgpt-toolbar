# Toolbar Chat

Toolbar Chat is a chat application that uses OpenAI's API to answer questions. The idea is to have a chat window that can be accessed from the system tray, and stores the chat history in a database that is completely local to the user.

## Features

- Chat with OpenAI's API
- Context manager
- Search history
- Settings

## Usage

Set your openapi key as an environment variable:
`export OPENAI_API_KEY=your_key`

Make sure that you have python installed, then run the following command to install the dependencies:
`pip install -r requirements.txt`

To use the application, simply run the `src/main.py` file. The application will start in the system tray. You can then access the chat window by clicking the icon in the system tray.
