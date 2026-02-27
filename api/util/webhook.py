import httpx

from api.env import Settings


async def send_flagged_webhook(*, unit_id: int):
    webhook_url = Settings().flag_webhook
    if not webhook_url:
        return

    content = f"Unit {unit_id} has been flagged. [VISIT HERE](<https://vvzapi.ch/unit/{unit_id}>)"

    async with httpx.AsyncClient() as client:
        await client.post(webhook_url, json={"content": content})
