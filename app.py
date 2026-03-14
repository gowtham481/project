import httpx
from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse

app = FastAPI(title="GitHub Gists API")

GITHUB_API_BASE = "https://api.github.com"


@app.get("/{username}")
async def get_user_gists(username: str):
    """
    Returns a list of public Gists for a given GitHub username.
    """
    url = f"{GITHUB_API_BASE}/users/{username}/gists"
    headers = {
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    }

    async with httpx.AsyncClient() as client:
        response = await client.get(url, headers=headers)

    if response.status_code == 404:
        raise HTTPException(status_code=404, detail=f"GitHub user '{username}' not found")

    if response.status_code != 200:
        raise HTTPException(
            status_code=response.status_code,
            detail="Failed to fetch gists from GitHub API"
        )

    gists = response.json()

    result = [
        {
            "id": gist["id"],
            "description": gist["description"],
            "url": gist["html_url"],
            "files": list(gist["files"].keys()),
            "created_at": gist["created_at"],
            "updated_at": gist["updated_at"],
            "public": gist["public"],
        }
        for gist in gists
    ]

    return JSONResponse(content={"username": username, "gists": result, "count": len(result)})


@app.get("/")
async def root():
    return {"message": "GitHub Gists API. Use /<username> to get a user's public gists."}
