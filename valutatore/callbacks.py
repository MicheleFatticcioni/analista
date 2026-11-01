"""Crew callbacks."""

from pathlib import Path
from typing import Any

from crewai_files import PDFFile


def load_pitch(inputs: dict[str, Any]) -> dict[str, Any]:
    """Attach the PDF at ``pitch_path`` to the crew as the file ``pitch``.

    crewai moves file objects found in the inputs into the crew's files and
    sends them to the model natively, so the agent reads the whole document.
    """
    raw_path = inputs.get("pitch_path", "")
    path = Path(raw_path).expanduser()
    if not raw_path or not path.is_file():
        raise FileNotFoundError(f"pitch_path does not point to a file: '{raw_path}'")
    if path.suffix.lower() != ".pdf":
        raise ValueError(f"pitch_path must be a PDF: '{raw_path}'")

    return {**inputs, "pitch": PDFFile(source=str(path))}
