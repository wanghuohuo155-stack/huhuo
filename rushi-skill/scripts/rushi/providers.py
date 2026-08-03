"""LLM Provider 抽象：mock（确定性）与 OpenAI 兼容接口（stdlib HTTP）。"""

from __future__ import annotations

import json
import http.client
import os
import urllib.error
import urllib.request
from typing import Protocol


class ProviderError(RuntimeError):
    pass


class Provider(Protocol):
    name: str

    def complete(self, prompt: str, system: str = "") -> str: ...


class OpenAICompatibleProvider:
    """OpenAI 兼容 Chat Completions 客户端（无第三方依赖）。"""

    name = "openai"

    def __init__(
        self,
        model: str,
        api_key: str,
        base_url: str = "https://api.openai.com/v1",
        json_mode: bool = False,
        max_tokens: int = 8192,
    ):
        self.model = model
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.json_mode = json_mode
        self.max_tokens = max_tokens

    def complete(self, prompt: str, system: str = "", json_mode: bool | None = None) -> str:
        url = f"{self.base_url}/chat/completions"
        use_json = self.json_mode if json_mode is None else json_mode
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system or "你是一个严谨的方法论蒸馏执行器。"},
                {"role": "user", "content": prompt},
            ],
            "temperature": 0.2,
        }
        if use_json:
            payload["response_format"] = {"type": "json_object"}
        payload["max_tokens"] = self.max_tokens
        req = urllib.request.Request(
            url,
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.api_key}",
            },
            method="POST",
        )
        data = None
        for attempt in (1, 2):
            try:
                with urllib.request.urlopen(req, timeout=180) as resp:
                    data = json.loads(resp.read().decode("utf-8"))
                break
            except urllib.error.HTTPError as exc:
                body = exc.read().decode("utf-8", errors="replace")[:300]
                raise ProviderError(f"HTTP {exc.code}: {body}") from exc
            except urllib.error.URLError as exc:
                # 传输层错误（超时/连接中断）重试一次；HTTP 错误已在上面抛出
                if attempt == 1 and isinstance(
                    exc.reason, (ConnectionError, TimeoutError, http.client.HTTPException)
                ):
                    continue
                raise ProviderError(f"网络错误: {exc.reason}") from exc
            except (http.client.HTTPException, ConnectionError, TimeoutError) as exc:
                if attempt == 1:
                    continue
                raise ProviderError(f"响应读取失败: {exc}") from exc
            except (UnicodeDecodeError, ValueError) as exc:
                raise ProviderError(f"响应解析失败: {exc}") from exc
        if data is None:
            raise ProviderError("响应读取失败（重试后仍失败）")
        try:
            return data["choices"][0]["message"]["content"]
        except (KeyError, IndexError) as exc:
            raise ProviderError(f"响应格式异常: {str(data)[:300]}") from exc


def get_provider(cfg):
    if cfg.provider == "mock":
        raise ProviderError(
            "provider=mock 不产出真实内容；请配置 openai provider 或使用 --mode mock 的确定性评测"
        )
    if cfg.provider == "openai":
        key = os.environ.get(cfg.api_key_env, "")
        if not key:
            raise ProviderError(
                f"未找到 API Key：请设置环境变量 {cfg.api_key_env}（或改用 --mode mock）"
            )
        model = cfg.model or "gpt-4.1-mini"
        return OpenAICompatibleProvider(
            model=model,
            api_key=key,
            base_url=cfg.base_url,
            json_mode=cfg.json_mode,
            max_tokens=cfg.max_output_tokens,
        )
    raise ProviderError(f"未知 provider: {cfg.provider}")
