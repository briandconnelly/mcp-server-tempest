from importlib.metadata import version

from .server import mcp

__version__ = version("mcp-server-tempest")


def main():
    mcp.run()


if __name__ == "__main__":
    main()
