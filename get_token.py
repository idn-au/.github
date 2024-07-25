import os
import asyncio
import time

from dotenv import load_dotenv
from jwt import JWT, jwk_from_pem
from httpx import AsyncClient

load_dotenv()

CLIENT_ID = os.environ.get("CLIENT_ID", "")
INSTALLATION_ID = os.environ.get("INSTALLATION_ID", "")
PRIVATE_KEY = os.environ.get("PRIVATE_KEY", "")
TIMEOUT = 30.0
RETRIES = 3


def generate_jwt() -> str:
    signing_key = jwk_from_pem(PRIVATE_KEY.encode())

    payload = {
        # Issued at time
        "iat": int(time.time()),
        # JWT expiration time (10 minutes maximum)
        "exp": int(time.time()) + 600,
        # GitHub App's client ID
        "iss": CLIENT_ID,
    }

    # Create JWT
    jwt_instance = JWT()
    return jwt_instance.encode(payload, signing_key, alg="RS256")


async def get_access_token(jwt: str) -> str:
    token_client = AsyncClient(
        headers={
            "Accept": "application/vnd.github+json",
            "Authorization": f"Bearer {jwt}",
            "X-GitHub-Api-Version": "2022-11-28",
        },
        timeout=TIMEOUT,
    )

    async with token_client as client:
        r = await client.post(
            f"https://api.github.com/app/installations/{INSTALLATION_ID}/access_tokens"
        )
    r.raise_for_status()
    return r.json()["token"]


async def get_token():
    jwt = generate_jwt()
    token = await get_access_token(jwt)
    return token


if __name__ == "__main__":
    token = asyncio.run(get_token())
    print(token)
