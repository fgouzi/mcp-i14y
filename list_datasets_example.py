#!/usr/bin/env python3
"""Example: List datasets from Swiss I14Y platform via the MCP server."""

import asyncio
import json
from helpers.i14y_api_client import I14YApiClient


async def main():
    """List datasets from I14Y."""
    print("📊 Fetching datasets from Swiss I14Y platform...\n")
    
    async with I14YApiClient() as client:
        # List datasets with default pagination (page 1, 25 results)
        response = await client.get(
            "/datasets",
            page=1,
            pageSize=10,  # Fetch just 10 for demo
            publicationLevel="Public"  # Only public datasets
        )
    
    data = json.loads(response)
    
    # Display results
    if "error" in data:
        print(f"❌ Error: {data['error']}")
        return
    
    datasets = data.get("data", [])
    pagination = data.get("metadataFull", {})
    
    print(f"✅ Found {len(datasets)} datasets (showing page preview):")
    print(f"📄 Total available: {pagination.get('totalCount', 'unknown')}")
    print(f"📑 Page: {pagination.get('page', 1)} of {pagination.get('totalPages', 'unknown')}\n")
    
    for i, dataset in enumerate(datasets, 1):
        title = dataset.get("title", {})
        dataset_id = dataset.get("identifier")
        status = dataset.get("registrationStatus", "Unknown")
        
        # Handle multilingual titles
        if isinstance(title, dict):
            title_str = title.get("de") or title.get("fr") or str(title)
        else:
            title_str = title
        
        print(f"{i}. {title_str}")
        print(f"   ID: {dataset_id}")
        print(f"   Status: {status}\n")


if __name__ == "__main__":
    asyncio.run(main())
