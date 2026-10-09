import anyio
from mcp import Client


async def main():
    async with Client(
        "https://mcp-planos.origamidemetalicos.com/mcp"
    ) as client:

        tools = await client.list_tools()

        print(
            [tool.name for tool in tools.tools]
        )


if __name__ == "__main__":
    anyio.run(main)