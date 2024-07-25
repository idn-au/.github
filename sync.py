import asyncio
import json
import os

from httpx import AsyncClient

from get_token import get_token

LOCAL = False  # for local testing
TIMEOUT = 30.0


async def list_repos(client: AsyncClient) -> list[str]:
    r = await client.get("https://api.github.com/orgs/idn-au/repos?per_page=100")
    r.raise_for_status()
    repos = [repo["name"] for repo in r.json() if repo["name"] != ".github"]
    return repos


async def list_labels(client: AsyncClient, repo: str) -> list[dict]:
    r = await client.get(
        f"https://api.github.com/repos/idn-au/{repo}/labels?per_page=100"
    )
    r.raise_for_status()
    labels = [
        {
            "name": label["name"],
            "description": label["description"],
            "color": label["color"],
        }
        for label in r.json()
    ]
    return labels


async def create_label(client: AsyncClient, repo: str, label: dict):
    r = await client.post(
        f"https://api.github.com/repos/idn-au/{repo}/labels", data=json.dumps(label)
    )
    r.raise_for_status()


async def update_label(client: AsyncClient, repo: str, name: str, label: dict):
    r = await client.patch(
        f"https://api.github.com/repos/idn-au/{repo}/labels/{name}",
        data=json.dumps(
            {
                "new_name": label["name"],
                "description": label["description"],
                "color": label["color"],
            }
        ),
    )
    r.raise_for_status()


async def delete_label(client: AsyncClient, repo: str, name: str):
    r = await client.delete(f"https://api.github.com/repos/idn-au/{repo}/labels/{name}")
    r.raise_for_status()


async def sync_labels(client: AsyncClient, repo: str, new_labels: list[dict]):
    remaining_new_labels = [label for label in new_labels]
    labels = await list_labels(client, repo)
    async with asyncio.TaskGroup() as tg:
        for label in [label for label in labels]:
            matched_label = next((l for l in new_labels if label == l), None)
            if matched_label:
                remaining_new_labels.remove(matched_label)
            else:
                # if name matches, update
                same_name_label = next(
                    (l for l in new_labels if label["name"] == l["name"]), None
                )
                if same_name_label:
                    tg.create_task(update_label(client, repo, label["name"], same_name_label))
                    remaining_new_labels.remove(same_name_label)
                else:
                    # if label not in new labels, delete
                    tg.create_task(delete_label(client, repo, label["name"]))
    async with asyncio.TaskGroup() as tg:
        # if new_label not in labels, create
        [tg.create_task(create_label(client, repo, label)) for label in remaining_new_labels]


async def main():
    token = await get_token() if LOCAL else os.environ.get("GH_TOKEN", "")

    api_client = AsyncClient(
        headers={
            "Accept": "application/vnd.github+json",
            "Authorization": f"Bearer {token}",
            "X-GitHub-Api-Version": "2022-11-28",
        },
        timeout=TIMEOUT,
    )
    
    async with asyncio.TaskGroup() as tg:
        repos = tg.create_task(list_repos(api_client))
        new_labels = tg.create_task(list_labels(api_client, ".github"))
    
    async with asyncio.TaskGroup() as tg:
        [tg.create_task(sync_labels(api_client, repo, new_labels.result())) for repo in repos.result()]

    await api_client.aclose()


if __name__ == "__main__":
    asyncio.run(main())
