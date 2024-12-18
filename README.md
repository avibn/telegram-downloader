# Telegram Downloader 📁

## Table of Contents

-   [About](#about)
-   [Telethon Version](#telethon_version)
-   [Getting Started](#getting_started)
-   [Usage](#usage)

## About<a name = "about"></a>

This project is a Telegram bot designed for personal use, leveraging the [local Telegram Bot API server](https://github.com/tdlib/telegram-bot-api) to download large video files sent or forwarded to the bot, directly to a specified local directory.

It's a simple solution that doesn't require a desktop or graphical client, and maintains the original file name. It's particularly useful for forwarding large video files 🎬 to download onto a NAS system.

## Telethon Version<a name = "telethon_version"></a>

I initially rewrote the bot using [Telethon](https://docs.telethon.dev), which offers more control over the download process. With Telethon, you could potentially track download progress or stop downloads midway, but these features aren’t fully implemented yet.

Despite this, I decided to stick with the **Bot API** version for its faster download speeds, even though it means giving up some of that control.

If you’re still interested in exploring the Telethon version, it’s available on the [telethon-migrate branch](https://github.com/avibn/telegram-downloader/tree/telethon-migrate).

## Getting Started<a name = "getting_started"></a>

### Docker Setup

Using Docker is the easiest way to set this up. Follow these steps:

1. Ensure Docker and Docker Compose are installed on your system.

2. Clone this repository and navigate to the project directory.

3. Set up your environment variables. You need to provide values for the following variables:
   | Variable | Description |
   | --- | --- |
   | `TELEGRAM_API_ID` | Your Telegram API ID. You can get this from [my.telegram.org](https://my.telegram.org/auth?to=apps). |
   | `TELEGRAM_API_HASH` | Your Telegram API Hash. You can get this from [my.telegram.org](https://my.telegram.org/auth?to=apps). |
   | `TELEGRAM_LOCAL` | Set this to `true` to use the local Telegram Bot API server. |
   | `BOT_TOKEN` | The token for your Telegram bot. You can create a new bot and get the token from [BotFather](https://t.me/botfather). |
   | `USER_ID` | Your Telegram user ID. This is the user that is allowed to send files to be downloaded with the bot (usually yourself). If you don't know your ID, you can use the `/info` command on the bot. |
   | `CHAT_ID` | The ID of the chat that the bot is allowed to download from. This can be the same as your `USER_ID` if you want to send files directly via DM to the bot. If you don't know the chat ID, you can use the `/info` command on the bot. |
   | `DOWNLOAD_TO_DIR` | The output directory where you want to download the files to (e.g., your downloads folder). |
   | `BOT_API_DIR` | The directory where the local bot API stores its files. You can alternatively edit the docker-compose file to use a Docker volume instead. In my case, I wanted to store it in a specific directory. |

    You can also set the environment variables in a .env file - just make sure to uncomment the `env_file: .env` lines in `docker-compose.prod.yml`.

4. Run the Docker Compose file for production:

    ```bash
    docker compose -f docker-compose.prod.yml up -d
    ```

    This command will start both services (local bot API and the bot).

5. Your bot should now be running. You can check the status of your Docker containers with:

    ```bash
    docker ps
    ```

### Manual Setup

If you prefer a manual setup, follow these steps:

1. You can use `docker-compose.api.yml` to run just the local bot API server. Alternatively, you can build it yourself if you wish.

2. Install the `uv` package manager:

    ```bash
    pip install uv
    ```

3. Install the required dependencies using `uv`:

    ```bash
    uv install
    ```

4. Create a `.env` file in the project root and add your environment variables. You can use the `.example.env` file as a template.

5. Run the bot using `uv`:

    ```bash
    uv run python run.py
    ```

This will start the bot in your local environment, using `uv` to manage your environment and dependencies.

## Usage<a name = "usage"></a>

<p align="center">
  <img src="/public/screenshot.png" alt="Telegram bot screenshot" width="600">
</p>

To use the bot, simply direct message it or add it to a group, depending on what you set as the `CHAT_ID`.

You can use the `/help` command to learn more about how to use the bot.

To download a video file, simply send/forward it to the bot. The bot will then ask you to confirm the download with a 'Yes' or 'No' button. Once you confirm, the bot will download the video file and notify you once the download is complete.
