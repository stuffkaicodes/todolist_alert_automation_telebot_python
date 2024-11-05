# Python-based Telegram bot designed to help users create and manage to-do lists and set alerts.
### By using a specific format, users can add tasks, set reminders, and receive timely notifications.

## Features

* Create To-Do Tasks: Add items to your to-do list using a simple format.
* Set Alerts: Schedule reminders for tasks at specific times.
* Mark Completed Tasks: Keep your list visually organized by checking off completed items. 

## Installation
*Prerequisites*

* Python 3.x
* A Telegram bot token For more information, visit the [Telegram Bot API documentation](https://core.telegram.org/bots)).
* (Optional) Python packages python-telegram-bot, schedule, and python-dotenv

### Setup

* Clone the repository: bash


    `git clone https://github.com/yourusername/todo-telegram-bot.git
    cd todo-telegram-bot`


* Install dependencies: bash

    `pip install -r requirements.txt`

* Create a .env file:

    `Add your bot token in a .env file in the project root directory:

    makefile

    TELEGRAM_TOKEN=your_bot_token_here`

* Run the bot: bash

    `python3 main.py`

## Usage

* Start the Bot: Send `/start` to initiate the bot.

* Ask the Bot for help: Send `/help` to request for message format. 

* Add a Task: Send a message in the format:

```
For a Task : [Task name] - [Task Description]

For an Alert : [Task name] @ [date/time in YYYY-MM-DD HH:MM format]


