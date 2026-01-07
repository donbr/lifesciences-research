"""Test ClinicalTrials.gov API headers to diagnose 403 errors."""

import asyncio
import httpx


async def test_without_user_agent():
    """Test without User-Agent header."""
    async with httpx.AsyncClient(
        base_url="https://clinicaltrials.gov/api/v2",
        headers={"Accept": "application/json"},
    ) as client:
        try:
            response = await client.get(
                "/studies",
                params={"query.term": "cancer", "pageSize": 1, "format": "json"},
            )
            print(f"Without User-Agent: {response.status_code}")
            if response.status_code != 200:
                print(f"Response: {response.text[:200]}")
        except Exception as e:
            print(f"Error without User-Agent: {e}")


async def test_with_user_agent():
    """Test with User-Agent header."""
    async with httpx.AsyncClient(
        base_url="https://clinicaltrials.gov/api/v2",
        headers={
            "Accept": "application/json",
            "User-Agent": "lifesciences-research/0.1.0 (https://github.com/donbr/lifesciences-research)",
        },
    ) as client:
        try:
            response = await client.get(
                "/studies",
                params={"query.term": "cancer", "pageSize": 1, "format": "json"},
            )
            print(f"With User-Agent: {response.status_code}")
            if response.status_code == 200:
                print("SUCCESS! User-Agent header is required")
        except Exception as e:
            print(f"Error with User-Agent: {e}")


async def main():
    """Run tests."""
    print("Testing ClinicalTrials.gov API headers...")
    await test_without_user_agent()
    await test_with_user_agent()


if __name__ == "__main__":
    asyncio.run(main())
