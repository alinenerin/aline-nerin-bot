import asyncio
from telethon import TelegramClient
from telethon.sessions import StringSession

API_ID = 38147284
API_HASH = '3b800cbaac2561c038c7d03432adc307'
STRING_SESSION = '1AZWarzUBuxaOZ4K0vnFn7_xiaZfNWYjfvxPZMUfDJc7zRzSW20W0RvWKZuBJX3ud8iCH1gEp4IUHiokwCRmTx491dpyWmqp5IWdVsKuYgAgotyqYKU-B1wIgHv85Ql44_N5BW7S7NA4CsevXYYgwjFTmv9YvoyjgCxCDjf9RkzWkKnYKLIKhGY_iaCrKexylyKyOupxaKkfC5Td6mRlUIYMde2NJqWB3yUrbsf-FNkG9A0m6ZPULlLGpJO9lvP2RrPxIWMe9MWMXUzuREf_f9YNnvk5hfSfP7blGhc22SKBVe4CLtZCn3J45jXvWul2JnOcpiA4kGkALqh6RMhda5skYDQSG_KI='

async def main():
    client = TelegramClient(StringSession(STRING_SESSION), API_ID, API_HASH)
    try:
        await client.connect()
        if not await client.is_user_authorized():
            print("Session INVALID or EXPIRED")
        else:
            me = await client.get_me()
            print(f"Success! Connected as: {me.first_name} (@{me.username})")
    except Exception as e:
        print(f"Error connecting: {e}")
    finally:
        await client.disconnect()

if __name__ == '__main__':
    asyncio.run(main())
