"""
Common
~~~~~~
"""

from rich.console import Console
from rich.progress import (
    BarColumn,
    DownloadColumn,
    Progress,
    TextColumn,
    TransferSpeedColumn
)
from rich.table import Column


progress = Progress(
    TextColumn('[progress.description]{task.description}', table_column=Column(ratio=1)),
    BarColumn(bar_width=60, table_column=Column(ratio=2)),
    TextColumn('[progress.percentage]{task.percentage:>3.0f}%', table_column=Column(ratio=1)),
    DownloadColumn(),
    TransferSpeedColumn(),
    console=Console(),
    transient=False,
)
