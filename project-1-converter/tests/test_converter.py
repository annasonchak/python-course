import pytest
from pathlib import Path
from unittest.mock import patch
from converter import ConversionRequest, REGISTRY, execute, available_targets

@pytest.fixture
def sample_dir(tmp_path):
    return tmp_path

def test_group_a_valid_conversion(tmp_path):
    csv_file = tmp_path / "data.csv"
    csv_file.write_text("id,name,role\n1,Jan Kowalski,Developer", encoding="utf-8")
    
    request = ConversionRequest(source=csv_file, target_format=".json", output_dir=tmp_path)
    result = execute(request)
    
    assert result.exists()
    assert result.suffix == ".json"

def test_group_b_valid_conversion(tmp_path):
    txt_file = tmp_path / "document.txt"
    txt_file.write_text("Przykładowy tekst testowy.", encoding="utf-8")
    
    request = ConversionRequest(source=txt_file, target_format=".docx", output_dir=tmp_path)
    result = execute(request)
    
    assert result.exists()
    assert result.suffix == ".docx"

def test_bad_or_corrupted_file_handling(tmp_path):
    bad_json = tmp_path / "sample_bad.json"
    bad_json.write_text("{ invalid json structure", encoding="utf-8")
    
    request = ConversionRequest(source=bad_json, target_format=".csv", output_dir=tmp_path)
    
    with pytest.raises(Exception):
        execute(request)

def test_unsupported_pair_validation(tmp_path):
    pdf_file = tmp_path / "document.pdf"
    pdf_file.write_text("dummy pdf content", encoding="utf-8")
    
    request = ConversionRequest(source=pdf_file, target_format=".csv", output_dir=tmp_path)
    
    with pytest.raises(ValueError, match="Unsupported conversion"):
        request.validate()


def test_missing_libreoffice_handling(tmp_path):
    docx_file = tmp_path / "test.docx"
    docx_file.write_text("dummy", encoding="utf-8")
    
    request = ConversionRequest(source=docx_file, target_format=".pdf", output_dir=tmp_path)
    
    with patch("subprocess.run", side_effect=FileNotFoundError):
        with pytest.raises(RuntimeError, match="LibreOffice executable not found"):
            execute(request)

def test_target_file_already_exists_logic(tmp_path):
    csv_file = tmp_path / "test.csv"
    csv_file.write_text("a,b\n1,2", encoding="utf-8")
    
    existing_target = tmp_path / "test.json"
    existing_target.write_text("old content", encoding="utf-8")
    
    request = ConversionRequest(source=csv_file, target_format=".json", output_dir=tmp_path)
    
    target_path = tmp_path / f"{csv_file.stem}.json"
    assert target_path.exists()
    assert target_path.read_text(encoding="utf-8") == "old content"

def test_polish_chars_and_empty_values(tmp_path):
    csv_file = tmp_path / "polish.csv"
    csv_file.write_text("id,name,description\n1,Zażółć Gęślą Jaźń,\n2,Anna Nowak,Kraków", encoding="utf-8")
    
    request = ConversionRequest(source=csv_file, target_format=".json", output_dir=tmp_path)
    result = execute(request)
    
    assert result.exists()
    content = result.read_text(encoding="utf-8")
    
    assert "Zażółć Gęślą Jaźń" in content
    assert "Kraków" in content