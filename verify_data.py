import asyncio
from toolbox_core.client import ToolboxClient

TOOLBOX_URL = "http://127.0.0.1:5000"

async def verify_data():
    print(f"Connecting to Toolbox at {TOOLBOX_URL}...")
    try:
        async with ToolboxClient(TOOLBOX_URL) as toolbox:
            print("Connected. Loading 'execute_sql' tool...")
            # We can use the 'execute_sql' tool if it's available, or just use the tools we defined.
            # However, 'execute_sql' might not be in the 'tools.yaml' we created?
            # Let's check 'tools.yaml' again.
            # Ah, we defined specific tools like 'search_airports', 'list_flights'.
            # We didn't define a generic 'execute_sql' tool in our tools.yaml.
            # But the toolbox might have it if we load the right toolset?
            # Wait, the previous 'run_database_init.py' used 'execute_sql'.
            # That was when running with '--prebuilt cloud-sql-mysql'.
            # Now we are running with '--tools-file=tools.yaml'.
            # Our 'tools.yaml' does NOT have 'execute_sql'.
            # So we should use one of our defined tools to check data.
            
            print("Loading 'cymbal_air' toolset...")
            tools_list = await toolbox.load_toolset("cymbal_air")
            if tools_list:
                print(f"First tool dict keys: {list(tools_list[0].__dict__.keys())}")
            
            # Convert list to dict for easy access
            tools = {t.__name__: t for t in tools_list}
            print(f"Tools loaded: {list(tools.keys())}")
            
            print("Verifying 'search_airports'...")
            # Search for all airports (empty query should return some)
            # The tools object is a Toolset which behaves like a dict of tools.
            # We need to call the tool.
            search_airports_tool = tools["search_airports"]
            # The tool itself needs to be called.
            # Let's inspect what 'tools["search_airports"]' is.
            print(f"Tool type: {type(search_airports_tool)}")
            
            # Assuming it's a callable tool wrapper
            airports = await search_airports_tool(country="United States")
            print(f"Airports result type: {type(airports)}")
            print(f"Airports result: {airports}")

            if isinstance(airports, list):
                 print(f"Airports found (limit 10): {len(airports)}")
                 if len(airports) > 0:
                     print("Sample Airport:", airports[0])
            else:
                 print("Airports result is not a list.")
            
            print("Verifying 'list_flights'...")
            # We need a valid date. Let's try a broad search or just check if the tool runs.
            # The tool requires date? No, it says "Do NOT guess a date".
            # But the SQL query uses parameters.
            # Let's try to find flights from SFO.
            flights = await tools["list_flights"](departure_airport="SFO", date="2024-01-01") # Just a dummy date to see if it executes
            print(f"Flights found (limit 10): {len(flights)}")
            
            print("Verifying 'search_amenities'...")
            amenities = await tools["search_amenities"](query="food")
            print(f"Amenities found: {len(amenities)}")

            print("\nData verification complete.")
            
    except Exception as e:
        print(f"Verification failed: {e}")

if __name__ == "__main__":
    asyncio.run(verify_data())
