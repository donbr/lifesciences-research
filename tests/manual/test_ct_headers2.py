"""Test ClinicalTrials.gov API headers - matching curl exactly."""
import asyncio
import httpx


async def test_minimal_headers():
    """Test with minimal headers like curl."""
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(
                "https://clinicaltrials.gov/api/v2/studies",
                params={"query.term": "cancer", "pageSize": 1, "format": "json"},
                headers={
                    "Host": "clinicaltrials.gov",
                    "User-Agent": "curl/7.81.0",
                    "Accept": "*/*",
                },
            )
            print(f"With curl headers: {response.status_code}")
            if response.status_code == 200:
                print("SUCCESS! curl headers work")
                data = response.json()
                print(f"Studies returned: {len(data.get('studies', []))}")
        except Exception as e:
            print(f"Error with curl headers: {e}")


async def test_httpx_default():
    """Test with httpx default headers."""
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(
                "https://clinicaltrials.gov/api/v2/studies",
                params={"query.term": "cancer", "pageSize": 1, "format": "json"},
            )
            print(f"\nWith httpx defaults: {response.status_code}")
            if response.status_code != 200:
                print(f"Response: {response.text[:200]}")
        except Exception as e:
            print(f"Error with httpx defaults: {e}")


async def main():
    """Run tests."""
    print("Testing ClinicalTrials.gov API with different headers...\n")
    await test_minimal_headers()
    await test_httpx_default()


if __name__ == "__main__":
    asyncio.run(main())
