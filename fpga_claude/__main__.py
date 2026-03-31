"""Allow running the package as a module: python -m fpga_claude"""

from .cli import cli

if __name__ == "__main__":
    cli()
