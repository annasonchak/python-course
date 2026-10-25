from pathlib import Path
from converter import ConversionRequest, execute, available_targets

output_dir = Path("./output")
output_dir.mkdir(exist_ok=True)

print("CSV -> JSON")
csv_file = Path("test.csv")
csv_file.write_text("name,age\nAlice,30\nBob,25", encoding="utf-8")

print("Available targets for CSV:", available_targets(csv_file))
request_csv_json = ConversionRequest(
    source=csv_file,
    target_format=".json",
    output_dir=output_dir
)
result_json = execute(request_csv_json)
print(f"Created: {result_json}")


print("\nJSON -> CSV")
print("Available targets for JSON:", available_targets(result_json))
request_json_csv = ConversionRequest(
    source=result_json,
    target_format=".csv",
    output_dir=output_dir
)
result_back_csv = execute(request_json_csv)
print(f"Created: {result_back_csv}")


print("\nTXT -> DOCX")
txt_file = Path("test.txt")
txt_file.write_text("Line one: Hello world!\nLine two: Python conversion test.", encoding="utf-8")

print("Available targets for TXT:", available_targets(txt_file))
request_txt_docx = ConversionRequest(
    source=txt_file,
    target_format=".docx",
    output_dir=output_dir
)
result_docx = execute(request_txt_docx)
print(f"Created: {result_docx}")


print("\nDOCX -> PDF")
print("Available targets for DOCX:", available_targets(result_docx))
try:
    request_docx_pdf = ConversionRequest(
        source=result_docx,
        target_format=".pdf",
        output_dir=output_dir
    )
    result_pdf = execute(request_docx_pdf)
    print(f"Created: {result_pdf}")
except Exception as e:
    print(f"PDF conversion failed or LibreOffice is missing: {e}")

print("\nInvalid JSON Error Handling")
bad_json_file = Path("bad_test.json")
bad_json_file.write_text("{ invalid json syntax ...", encoding="utf-8")

try:
    request_bad_json = ConversionRequest(
        source=bad_json_file,
        target_format=".csv",
        output_dir=output_dir
    )
    execute(request_bad_json)
except Exception as e:
    print(f"Error: {e}")