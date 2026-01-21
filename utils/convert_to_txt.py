from pathlib import Path
from datetime import datetime

def save_text_to_txt(
    content: str,
    storage_dir: Path = Path("Storage"),
    filename: str | None = None
) -> Path:
    """
    Save a string as a .txt file inside the Storage folder.

    Args:
        content (str): Text content to save
        storage_dir (Path): Directory where file will be stored
        filename (str | None): Optional filename without extension

    Returns:
        Path: Path to the saved .txt file
    """

    # Ensure storage directory exists
    storage_dir.mkdir(parents=True, exist_ok=True)

    # Generate filename if not provided
    if not filename:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"text_{timestamp}"

    txt_path = storage_dir / f"{filename}"

    # Write content
    txt_path.write_text(content, encoding="utf-8")

    return txt_path