import sys, io
# Fix Windows terminal encoding (cp1252 -> utf-8)
if sys.stdout.encoding != 'utf-8':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')
"""
openapi_to_csv.py -- Snapshot API List from OpenAPI JSON to CSV
==================================================================
Assignment 5: ข้อ 3e — แปลง openapi.json → CSV สำหรับ Snapshot API List

วิธีใช้งาน:
  1. รัน FastAPI server ก่อน:
       uvicorn backend.main:app --reload --port 8000

  2. รัน script นี้:
       python openapi_to_csv.py
       หรือระบุ URL เอง:
       python openapi_to_csv.py --url http://localhost:8000/openapi.json
       หรือระบุ local file:
       python openapi_to_csv.py --file openapi.json

  3. ผลลัพธ์จะถูกบันทึกเป็น api_snapshot.csv

ไม่ต้องติดตั้ง library เพิ่มเติม — ใช้เฉพาะ Standard Library ของ Python:
  - urllib.request  : ดาวน์โหลด openapi.json จาก /openapi.json endpoint
  - json            : parse JSON
  - csv             : เขียนไฟล์ CSV
  - argparse        : รับ argument จาก command line
  - datetime        : บันทึก snapshot timestamp
"""

import json
import csv
import urllib.request
import argparse
from datetime import datetime
from pathlib import Path


# ─── Configuration ────────────────────────────────────────────────────────────

DEFAULT_OPENAPI_URL = "http://localhost:8000/openapi.json"
DEFAULT_OUTPUT_FILE = "api_snapshot.csv"

CSV_COLUMNS = [
    "no",
    "method",
    "path",
    "tag",
    "summary",
    "description",
    "request_body_required",
    "request_content_type",
    "response_200_description",
    "response_201_description",
    "response_4xx_codes",
    "parameters",
    "operation_id",
    "snapshot_at",
]


# ─── Functions ─────────────────────────────────────────────────────────────────

def load_openapi_from_url(url: str) -> dict:
    """ดาวน์โหลด openapi.json จาก FastAPI server"""
    print(f"[INFO] กำลังดาวน์โหลด OpenAPI schema จาก: {url}")
    try:
        with urllib.request.urlopen(url, timeout=10) as response:
            data = json.loads(response.read().decode("utf-8"))
        print(f"[OK]   ดาวน์โหลดสำเร็จ (API title: {data.get('info', {}).get('title', 'N/A')})")
        return data
    except Exception as e:
        print(f"[ERROR] ไม่สามารถเชื่อมต่อ {url}: {e}")
        print("        กรุณาตรวจสอบว่า FastAPI server กำลังรันอยู่ หรือใช้ --file แทน")
        sys.exit(1)


def load_openapi_from_file(filepath: str) -> dict:
    """โหลด openapi.json จากไฟล์ local"""
    path = Path(filepath)
    if not path.exists():
        print(f"[ERROR] ไม่พบไฟล์: {filepath}")
        sys.exit(1)
    print(f"[INFO] โหลด OpenAPI schema จากไฟล์: {filepath}")
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    print(f"[OK]   โหลดสำเร็จ (API title: {data.get('info', {}).get('title', 'N/A')})")
    return data


def extract_api_rows(openapi: dict) -> list[dict]:
    """
    แปลง openapi.json paths → list ของ dict แต่ละ row
    แต่ละ row = 1 endpoint (method + path)
    """
    rows = []
    paths = openapi.get("paths", {})
    snapshot_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    counter = 1

    for path, path_item in paths.items():
        for method, operation in path_item.items():
            # ข้ามถ้าไม่ใช่ HTTP method จริง
            if method not in ("get", "post", "put", "patch", "delete", "head", "options"):
                continue

            # ─── Tag ──────────────────────────────────────────────────────────
            tags = operation.get("tags", [])
            tag = ", ".join(tags) if tags else "-"

            # ─── Summary & Description ────────────────────────────────────────
            summary = operation.get("summary", "-")
            description = operation.get("description", "-")
            # ลบ newline ออกจาก description เพื่อ CSV ที่อ่านง่าย
            description = description.replace("\n", " ").replace("\r", "").strip()

            # ─── Request Body ─────────────────────────────────────────────────
            request_body = operation.get("requestBody", {})
            req_required = "Yes" if request_body.get("required", False) else ("Yes" if request_body else "No")
            req_content = ", ".join(request_body.get("content", {}).keys()) if request_body else "-"

            # ─── Responses ────────────────────────────────────────────────────
            responses = operation.get("responses", {})
            res_200 = responses.get("200", {}).get("description", "-")
            res_201 = responses.get("201", {}).get("description", "-")

            # รวม 4xx codes
            error_codes = [code for code in responses.keys() if code.startswith("4")]
            res_4xx = ", ".join(sorted(error_codes)) if error_codes else "-"

            # ─── Parameters (query/path) ──────────────────────────────────────
            parameters = operation.get("parameters", [])
            param_summary = "; ".join(
                f"{p.get('name')} ({p.get('in')})"
                for p in parameters
            ) if parameters else "-"

            # ─── Operation ID ─────────────────────────────────────────────────
            operation_id = operation.get("operationId", "-")

            rows.append({
                "no": counter,
                "method": method.upper(),
                "path": path,
                "tag": tag,
                "summary": summary,
                "description": description,
                "request_body_required": req_required,
                "request_content_type": req_content,
                "response_200_description": res_200,
                "response_201_description": res_201,
                "response_4xx_codes": res_4xx,
                "parameters": param_summary,
                "operation_id": operation_id,
                "snapshot_at": snapshot_at,
            })
            counter += 1

    return rows


def write_csv(rows: list[dict], output_path: str) -> None:
    """เขียน rows ออกเป็น CSV file"""
    path = Path(output_path)
    with open(path, "w", newline="", encoding="utf-8-sig") as f:
        # utf-8-sig → Excel เปิดไฟล์ CSV ภาษาไทยได้ถูกต้อง
        writer = csv.DictWriter(f, fieldnames=CSV_COLUMNS)
        writer.writeheader()
        writer.writerows(rows)
    print(f"[OK]   บันทึก CSV สำเร็จ: {path.resolve()}")


def print_summary(openapi: dict, rows: list[dict]) -> None:
    """แสดงสรุปผลใน terminal"""
    info = openapi.get("info", {})
    print()
    print("=" * 60)
    print(f"  📋 API Snapshot Summary")
    print("=" * 60)
    print(f"  Title   : {info.get('title', 'N/A')}")
    print(f"  Version : {info.get('version', 'N/A')}")
    print(f"  Endpoints: {len(rows)} รายการ")
    print()

    # แสดงตารางสรุปใน terminal
    print(f"  {'#':<4} {'METHOD':<8} {'PATH':<40} {'TAG'}")
    print(f"  {'-'*4} {'-'*8} {'-'*40} {'-'*20}")
    for row in rows:
        print(f"  {row['no']:<4} {row['method']:<8} {row['path']:<40} {row['tag']}")
    print("=" * 60)


# ─── Main ──────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="แปลง openapi.json → CSV สำหรับ Snapshot API List ของ AI Ecosystem",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
ตัวอย่างการใช้งาน:
  python openapi_to_csv.py
  python openapi_to_csv.py --url http://localhost:8000/openapi.json
  python openapi_to_csv.py --file openapi.json --output my_api_list.csv
        """
    )
    parser.add_argument(
        "--url",
        default=DEFAULT_OPENAPI_URL,
        help=f"URL ของ OpenAPI JSON endpoint (default: {DEFAULT_OPENAPI_URL})",
    )
    parser.add_argument(
        "--file",
        default=None,
        help="Path ของ openapi.json ที่ดาวน์โหลดมาแล้ว (ใช้แทน --url)",
    )
    parser.add_argument(
        "--output",
        default=DEFAULT_OUTPUT_FILE,
        help=f"ชื่อไฟล์ CSV ที่จะบันทึก (default: {DEFAULT_OUTPUT_FILE})",
    )

    args = parser.parse_args()

    # โหลด OpenAPI schema
    if args.file:
        openapi = load_openapi_from_file(args.file)
    else:
        openapi = load_openapi_from_url(args.url)

    # แปลงเป็น rows
    rows = extract_api_rows(openapi)

    if not rows:
        print("[WARN] ไม่พบ endpoint ใน OpenAPI schema")
        sys.exit(0)

    # แสดงสรุป
    print_summary(openapi, rows)

    # เขียน CSV
    write_csv(rows, args.output)

    print(f"\n  ✅ เสร็จสิ้น! เปิดไฟล์ '{args.output}' ด้วย Excel หรือ Google Sheets ได้เลย")
    print(f"     (เลือก encoding: UTF-8 with BOM หากตัวอักษรไทยไม่แสดงใน Excel)")


if __name__ == "__main__":
    main()
