from pathlib import Path


def get_next_filename(
    output_dir: Path | str,
    prefix: str = "video",
    extension: str = ".mp4",
    custom_name: str = "",
) -> str:
    output_dir = Path(output_dir)
    if custom_name:
        candidate = output_dir / f"{custom_name}{extension}"
        if not candidate.exists():
            return str(candidate)
        idx = 1
        while True:
            candidate = output_dir / f"{custom_name}_{idx}{extension}"
            if not candidate.exists():
                return str(candidate)
            idx += 1
    idx = 1
    while True:
        name = output_dir / f"{prefix}_{idx}{extension}"
        if not name.exists():
            return str(name)
        idx += 1
