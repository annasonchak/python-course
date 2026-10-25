from dataclasses import dataclass
from pathlib import Path
from collections.abc import Callable
import csv
import json
import subprocess
from docx import Document

Converter = Callable[[Path, Path], Path]
REGISTRY: dict[tuple[str, str], Converter] = {}

def converter(source: str, target: str):
    def register(func: Converter) -> Converter:
        REGISTRY[(source.lower(), target.lower())] = func
        return func
    return register

@dataclass(frozen=True)
class ConversionRequest:
    source: Path
    target_format: str
    output_dir: Path

    def validate(self) -> None:
        if not self.source.is_file():
            raise FileNotFoundError("Input file not found")
        if not self.output_dir.is_dir():
            raise NotADirectoryError("Target directory not found")
        key = (self.source.suffix.lower(), self.target_format.lower())
        if key not in REGISTRY:
            raise ValueError(f"Unsupported conversion: {key}")

def available_targets(source: Path) -> list[str]:
    return sorted(target for (src, target) in REGISTRY if src == source.suffix.lower())

def execute(request: ConversionRequest) -> Path:
    request.validate()
    key = (request.source.suffix.lower(), request.target_format.lower())
    return REGISTRY[key](request.source, request.output_dir)

@converter(".csv", ".json")
def csv_to_json(source: Path, output_dir: Path) -> Path:
    target = output_dir / f"{source.stem}.json"
    data = []
    with open(source, mode="r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            data.append(row)
    with open(target, mode="w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)
    return target

@converter(".json", ".csv")
def json_to_csv(source: Path, output_dir: Path) -> Path:
    target = output_dir / f"{source.stem}.csv"
    with open(source, mode="r", encoding="utf-8") as f:
        data = json.load(f)
    if not isinstance(data, list) or not data:
        raise ValueError("JSON file must contain a non-empty list of objects")
    fieldnames = list(data[0].keys())
    with open(target, mode="w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(data)
    return target

def _libreoffice_convert(source: Path, output_dir: Path, target_ext: str) -> Path:
    command = [
        "libreoffice",
        "--headless",
        "--convert-to",
        target_ext,
        "--outdir",
        str(output_dir),
        str(source)
    ]
    try:
        result = subprocess.run(command, capture_output=True, text=True, timeout=60)
    except FileNotFoundError:
        raise RuntimeError("LibreOffice executable not found")
    
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip() or "Conversion failed")
        
    target = output_dir / f"{source.stem}.{target_ext}"
    if not target.exists():
        raise RuntimeError("Output file was not created")
    return target

@converter(".txt", ".docx")
def txt_to_docx(source: Path, output_dir: Path) -> Path:
    target = output_dir / f"{source.stem}.docx"
    doc = Document()
    with open(source, mode="r", encoding="utf-8") as f:
        for line in f:
            doc.add_paragraph(line.strip())
    doc.save(target)
    return target

@converter(".docx", ".txt")
def docx_to_txt(source: Path, output_dir: Path) -> Path:
    target = output_dir / f"{source.stem}.txt"
    doc = Document(source)
    text = "\n".join([p.text for p in doc.paragraphs])
    target.write_text(text, encoding="utf-8")
    return target

@converter(".txt", ".odt")
def txt_to_odt(source: Path, output_dir: Path) -> Path:
    return _libreoffice_convert(source, output_dir, "odt")

@converter(".odt", ".txt")
def odt_to_txt(source: Path, output_dir: Path) -> Path:
    return _libreoffice_convert(source, output_dir, "txt")

@converter(".txt", ".pdf")
def txt_to_pdf(source: Path, output_dir: Path) -> Path:
    return _libreoffice_convert(source, output_dir, "pdf")

@converter(".docx", ".pdf")
def docx_to_pdf(source: Path, output_dir: Path) -> Path:
    return _libreoffice_convert(source, output_dir, "pdf")

@converter(".docx", ".odt")
def docx_to_odt(source: Path, output_dir: Path) -> Path:
    return _libreoffice_convert(source, output_dir, "odt")

@converter(".odt", ".docx")
def odt_to_docx(source: Path, output_dir: Path) -> Path:
    return _libreoffice_convert(source, output_dir, "docx")

@converter(".odt", ".pdf")
def odt_to_pdf(source: Path, output_dir: Path) -> Path:
    return _libreoffice_convert(source, output_dir, "pdf")