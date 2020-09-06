# Fish sell telegram bot

A Telegram bot provides access to the fish-shop. You can choose a fish, get a descriptions of fish with a picture, add the fish to the cart, remove from the cart, and send a request for the payment. This bot use the api of [Elasticpath](https://www.elasticpath.com/) service (before it called Moltin).

## Enviroment settings

Create enviroment variables in the `.env` file:

`CLIENT_ID` - client_id key access to Elasticpath shop API (getting in Elasticpath dashboard).

`CLIENT_SECRET_TOKEN` - client_secret key access to Elasticpath shop API (getting in Elasticpath dashboard).

`TELEGRAM_TOKEN` - telegram bot token.

`DATABASE_PASSWORD` - [Redislab](https://redislabs.com/) database password.

`DATABASE_HOST` - Redislab database host.

`DATABASE_PORT` - Redislab database port.

## Getting Started

Create store in [Elasticpath](https://www.elasticpath.com/).

Create Redis online database in [Redislab](https://redislabs.com/).

Create Telegram bot.

Clone repository and install the required Python dependencies:

```bash
pip install -r requirements.txt
```

### Run the bot:

```bash
python fish_bot.py
```

### Building tools

[Python 3.8.1](https://www.python.org/downloads/release/python-381/) - Programming language.

[python-telegram-bot V11.1.0](https://github.com/python-telegram-bot/python-telegram-bot/tree/v11.1.0) - Telegram API wrapper.

## Additional script

`shop_access.py` provides the methods for manage shop by API.

## Example bot work

Add the bot in the telegram by username: `@fish_sales_bot`. Below is the bot work animation.

![screenshot](screenshot/fish_bot.gif)

## Deployment

This project is ready to be deployed. This bot was deployed on Heroku.

## Motivation

This project was created as part of online course for web developer [dvmn.org](https://dvmn.org/modules/).