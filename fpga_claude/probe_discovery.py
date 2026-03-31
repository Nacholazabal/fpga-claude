"""Auto-discover .ltx probe files from a Vivado project directory."""

import glob
from pathlib import Path


def find_ltx(project_path: str) -> str:
    """Find the .ltx debug probes file for a Vivado project.

    Searches common output directories in order of preference:
      1. <project>.runs/impl_1/*.ltx
      2. <project>.hw/*.ltx
      3. Any impl run directory (picks newest by mtime)

    Args:
        project_path: Path to the .xpr file or the project root directory.

    Returns:
        Absolute path to the .ltx file.

    Raises:
        FileNotFoundError: If no .ltx file is found with a helpful message.
    """
    p = Path(project_path)

    # Accept either the .xpr file or the containing directory
    if p.is_file() and p.suffix == ".xpr":
        project_dir = p.parent
        project_name = p.stem
    elif p.is_dir():
        project_dir = p
        # Try to find the .xpr to get the project name
        xprs = list(p.glob("*.xpr"))
        project_name = xprs[0].stem if xprs else p.name
    else:
        raise FileNotFoundError(f"Project path not found: {project_path}")

    candidates = []

    # 1. Preferred: impl_1 run directory
    impl1_pattern = str(project_dir / f"{project_name}.runs" / "impl_1" / "*.ltx")
    candidates.extend(glob.glob(impl1_pattern))

    # 2. Hardware directory (Vivado 2019+ sometimes puts it here)
    hw_pattern = str(project_dir / f"{project_name}.hw" / "*.ltx")
    candidates.extend(glob.glob(hw_pattern))

    # 3. Any impl_* run directory
    any_impl_pattern = str(project_dir / f"{project_name}.runs" / "impl_*" / "*.ltx")
    candidates.extend(glob.glob(any_impl_pattern))

    # Remove duplicates, keep unique paths
    seen = set()
    unique = []
    for c in candidates:
        if c not in seen:
            seen.add(c)
            unique.append(c)

    if not unique:
        raise FileNotFoundError(
            f"No .ltx probe file found for project '{project_name}'.\n"
            f"Searched in: {project_dir}\n\n"
            "To generate the .ltx file:\n"
            "  1. Open your project in Vivado\n"
            "  2. Run Implementation (or Generate Bitstream)\n"
            "  3. The .ltx file will appear in <project>.runs/impl_1/\n\n"
            "Or specify the path explicitly with --ltx /path/to/debug.ltx"
        )

    # If multiple, pick the newest by modification time
    unique.sort(key=lambda f: Path(f).stat().st_mtime, reverse=True)
    return str(Path(unique[0]).resolve())
