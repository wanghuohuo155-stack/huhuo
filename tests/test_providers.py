import http.client
import json
import os
import tempfile
import unittest
import urllib.error
from pathlib import Path
from unittest import mock

import _paths  # noqa: F401

from rushi.config import Config
from rushi.providers import OpenAICompatibleProvider, ProviderError, get_provider


class Resp:
    def __init__(self, data: str):
        self._data = data.encode("utf-8")

    def read(self) -> bytes:
        return self._data

    def close(self) -> None:
        pass

    def __enter__(self) -> "Resp":
        return self

    def __exit__(self, *args: object) -> None:
        pass


class ProvidersTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.provider = OpenAICompatibleProvider("test-model", "test-key", "https://x.test", json_mode=False)

    def tearDown(self):
        self.tmp.cleanup()

    def test_success_with_json_mode_payload(self):
        captured = {}

        def fake_urlopen(req, timeout=180):
            captured["payload"] = json.loads(req.data)
            captured["headers"] = req.headers
            return Resp('{"choices":[{"message":{"content":"ok"}}]}')

        with mock.patch("rushi.providers.urllib.request.urlopen", side_effect=fake_urlopen):
            out = self.provider.complete("hi", json_mode=True)
        self.assertEqual(out, "ok")
        self.assertEqual(captured["payload"]["response_format"], {"type": "json_object"})
        self.assertEqual(captured["payload"]["model"], "test-model")
        self.assertEqual(captured["headers"]["Authorization"], "Bearer test-key")

    def test_http_error_raises_provider_error(self):
        def boom(req, timeout=180):
            raise urllib.error.HTTPError("http://x", 429, "quota", {}, Resp('{"error":"no quota"}'))

        with mock.patch("rushi.providers.urllib.request.urlopen", side_effect=boom):
            with self.assertRaises(ProviderError) as cm:
                self.provider.complete("hi")
        self.assertIn("HTTP 429", str(cm.exception))

    def test_url_error_retries_once_then_fails(self):
        calls = []

        def flaky(req, timeout=180):
            calls.append(1)
            raise urllib.error.URLError(TimeoutError("timeout"))

        with mock.patch("rushi.providers.urllib.request.urlopen", side_effect=flaky):
            with self.assertRaises(ProviderError) as cm:
                self.provider.complete("hi")
        self.assertEqual(len(calls), 2)
        self.assertIn("网络错误", str(cm.exception))

    def test_http_exception_retry_then_success(self):
        calls = []

        def flaky(req, timeout=180):
            calls.append(1)
            if len(calls) == 1:
                raise http.client.IncompleteRead(b"")
            return Resp('{"choices":[{"message":{"content":"recovered"}}]}')

        with mock.patch("rushi.providers.urllib.request.urlopen", side_effect=flaky):
            out = self.provider.complete("hi")
        self.assertEqual(out, "recovered")
        self.assertEqual(len(calls), 2)

    def test_bad_json_raises(self):
        with mock.patch(
            "rushi.providers.urllib.request.urlopen", return_value=Resp("not-json")
        ):
            with self.assertRaises(ProviderError):
                self.provider.complete("hi")

    def test_missing_choices_raises(self):
        with mock.patch(
            "rushi.providers.urllib.request.urlopen", return_value=Resp('{"choices":[]}')
        ):
            with self.assertRaises(ProviderError):
                self.provider.complete("hi")

    def test_get_provider_mock_raises(self):
        cfg = Config(project_dir=Path(self.tmp.name), provider="mock")
        with self.assertRaises(ProviderError):
            get_provider(cfg)

    def test_get_provider_openai_missing_key(self):
        cfg = Config(
            project_dir=Path(self.tmp.name), provider="openai", api_key_env="RUSHI_NO_SUCH_KEY_XYZ"
        )
        with self.assertRaises(ProviderError):
            get_provider(cfg)

    def test_get_provider_openai_with_env(self):
        cfg = Config(project_dir=Path(self.tmp.name), provider="openai", api_key_env="RUSHI_TEST_KEY")
        with mock.patch.dict(os.environ, {"RUSHI_TEST_KEY": "k"}, clear=False):
            p = get_provider(cfg)
        self.assertEqual(p.model, "gpt-4.1-mini")
        self.assertTrue(p.json_mode)

    def test_get_provider_unknown(self):
        cfg = Config(project_dir=Path(self.tmp.name), provider="nope")
        with self.assertRaises(ProviderError):
            get_provider(cfg)


if __name__ == "__main__":
    unittest.main()
