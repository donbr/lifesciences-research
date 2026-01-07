"""Diagnostic script to check WikiPathways getXrefList API response format."""
import asyncio

import httpx


async def check_xref_format():
    """Check actual format of getXrefList API response."""
    async with httpx.AsyncClient() as client:
        # Test WP534 (Glycolysis) with code L (Entrez Gene)
        response = await client.get(
            "http://webservice.wikipathways.org/getXrefList",
            params={"pwId": "WP534", "code": "L", "format": "json"},
        )

        print("Status:", response.status_code)
        print("Response JSON:")
        data = response.json()
        print(data)

        if "xrefs" in data:
            print(f"\nFound {len(data['xrefs'])} xrefs")
            print("Type of first xref:", type(data["xrefs"][0]) if data["xrefs"] else "None")
            print("First 3 xrefs:", data["xrefs"][:3] if data["xrefs"] else "None")


if __name__ == "__main__":
    asyncio.run(check_xref_format())
