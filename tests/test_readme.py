"""Run README.md's Python examples so they cannot silently rot.

Every ```python block in the README is executed against the in-process server
with the WeatherFlow API mocked. A block that calls ``asyncio.run`` is a
complete script and runs as-is; any other block is a snippet, run inside the
setup the README describes for it (a connected ``client`` and a ``station_id``
from ``tempest_get_stations``).
"""

import os
import re
import textwrap
from pathlib import Path
from unittest.mock import AsyncMock, patch

import pytest

import mcp_server_tempest.server as server_module

from .test_server import (
    SAMPLE_FORECAST_DATA,
    SAMPLE_OBSERVATION_DATA,
    SAMPLE_SINGLE_STATION_DATA,
    SAMPLE_STATION_DATA,
)

README = Path(__file__).parent.parent / "README.md"
BLOCKS = re.findall(r"```python\n(.*?)```", README.read_text(), re.S)

SNIPPET_SETUP = """\
import asyncio

from fastmcp import Client

from mcp_server_tempest.server import mcp


async def _main():
    async with Client(mcp) as client:
        result = await client.call_tool("tempest_get_stations")
        station_id = result.structured_content["stations"][0]["station_id"]
{body}

asyncio.run(_main())
"""


def _as_script(block: str) -> str:
    if "asyncio.run(" in block:
        return block
    return SNIPPET_SETUP.format(body=textwrap.indent(block, " " * 8))


def test_readme_has_examples():
    # Guard the negative result: a regex that matched nothing would make the
    # parametrized test below vacuously pass.
    assert len(BLOCKS) >= 4


@pytest.mark.parametrize("block", BLOCKS, ids=[f"block{i}" for i in range(len(BLOCKS))])
def test_readme_example_runs(block, capsys):
    server_module.cache.clear()
    server_module._fetch_times.clear()
    with (
        patch.dict(os.environ, {"WEATHERFLOW_API_TOKEN": "test-token"}),
        patch.object(server_module, "_get_disk_cache", return_value=None),
        patch.object(
            server_module, "api_get_stations", new=AsyncMock(return_value=SAMPLE_STATION_DATA)
        ),
        patch.object(
            server_module,
            "api_get_station_id",
            new=AsyncMock(return_value=SAMPLE_SINGLE_STATION_DATA),
        ),
        patch.object(
            server_module, "api_get_forecast", new=AsyncMock(return_value=SAMPLE_FORECAST_DATA)
        ),
        patch.object(
            server_module,
            "api_get_observation",
            new=AsyncMock(return_value=SAMPLE_OBSERVATION_DATA),
        ),
    ):
        exec(compile(_as_script(block), "README.md", "exec"), {"__name__": "__readme__"})
    server_module.cache.clear()
    server_module._fetch_times.clear()
    out = capsys.readouterr().out
    assert out.strip(), "example printed nothing"
    if '"repair"' in block:
        # The error-recovery example must actually take the repair path.
        assert "Retried with" in out, out
