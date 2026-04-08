"""共享的 HTTP 代理规范化（供 LLM 与 Embedding 等复用）。"""


def normalize_http_proxy_url(url: str) -> str:
    u = url.strip()
    if u.startswith("https://127.0.0.1") or u.startswith("https://localhost"):
        return "http://" + u[len("https://") :]
    return u
