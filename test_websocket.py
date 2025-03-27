#!/usr/bin/env python
"""
Test script for WebSocket streaming with the MCP server.
"""

import asyncio
import json
import websockets

async def test_websocket():
    headers = {'X-API-Key': 'test-key'}
    uri = 'ws://localhost:8000/api/functions/stream'
    
    print(f"Connecting to {uri}...")
    async with websockets.connect(uri, extra_headers=headers) as websocket:
        # Send the request
        request = {
            'name': 'calculator',
            'parameters': {'operation': 'add', 'a': 10, 'b': 20}
        }
        print(f"Sending request: {json.dumps(request)}")
        await websocket.send(json.dumps(request))
        
        # Receive and print all responses until complete
        while True:
            response = await websocket.recv()
            data = json.loads(response)
            print(f"Received: {json.dumps(data, indent=2)}")
            
            # Check if this is the final chunk
            if data.get('status') == 'success' or data.get('status') == 'error':
                print("Stream complete.")
                break

if __name__ == "__main__":
    asyncio.run(test_websocket()) 