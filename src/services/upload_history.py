"""记录已上传原始文件路径，便于列表展示与再次入库。"""

from __future__ import annotations

import json
import re
import uuid
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def _safe_filename(name: str) -> str:
    base = Path(name).name
    base = re.sub(r'[<>:"/\\|?*\x00-\x1f]', "_", base)
    base = re.sub(r"\s+", " ", base).strip() or "file"
    return base[:180]


@dataclass
class UploadRecord:
    id: str
    original_name: str
    stored_filename: str
    size: int
    suffix: str
    uploaded_at: str

    def to_json(self) -> dict[str, Any]:
        return asdict(self)


class UploadHistory:
    def __init__(self, persist_dir: Path) -> None:
        self.persist_dir = Path(persist_dir)
        self.raw_dir = self.persist_dir / "raw_uploads"
        self.manifest_path = self.persist_dir / "upload_history.json"
        self.raw_dir.mkdir(parents=True, exist_ok=True)

    def _load(self) -> list[dict[str, Any]]:
        if not self.manifest_path.is_file():
            return []
        try:
            data = json.loads(self.manifest_path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            return []
        if isinstance(data, list):
            return [x for x in data if isinstance(x, dict)]
        return []

    def _save(self, rows: list[dict[str, Any]]) -> None:
        self.manifest_path.write_text(
            json.dumps(rows, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )

    def list_records(self) -> list[UploadRecord]:
        rows = self._load()
        out: list[UploadRecord] = []
        for r in rows:
            try:
                out.append(
                    UploadRecord(
                        id=str(r["id"]),
                        original_name=str(r["original_name"]),
                        stored_filename=str(r["stored_filename"]),
                        size=int(r["size"]),
                        suffix=str(r.get("suffix", "")),
                        uploaded_at=str(r["uploaded_at"]),
                    )
                )
            except (KeyError, TypeError, ValueError):
                continue
        out.sort(key=lambda x: x.uploaded_at, reverse=True)
        return out

    def get_record(self, upload_id: str) -> UploadRecord | None:
        for r in self.list_records():
            if r.id == upload_id:
                return r
        return None

    def path_for(self, rec: UploadRecord) -> Path:
        return (self.raw_dir / rec.stored_filename).resolve()

    def save_original(self, original_name: str, data: bytes) -> UploadRecord:
        uid = str(uuid.uuid4())
        safe = _safe_filename(original_name)
        stored_filename = f"{uid}_{safe}"
        path = self.raw_dir / stored_filename
        path.write_bytes(data)
        suf = Path(original_name).suffix.lower()
        rec = UploadRecord(
            id=uid,
            original_name=Path(original_name).name,
            stored_filename=stored_filename,
            size=len(data),
            suffix=suf,
            uploaded_at=datetime.now(timezone.utc).isoformat(),
        )
        rows = self._load()
        rows.append(rec.to_json())
        self._save(rows)
        return rec
