import unittest

import _paths  # noqa: F401

from rushi.config import Config
from rushi import verifier
from fixtures import SOURCE_TEXT, CLAIMS


class ConfigStub(Config):
    def __init__(self):
        super().__init__(project_dir=__import__("pathlib").Path("."))


class QuoteSpanTest(unittest.TestCase):
    def test_exact_match(self):
        span = verifier.find_quote_span("什么情况下我会彻底失败", SOURCE_TEXT)
        self.assertTrue(span["found"])
        self.assertEqual(span["method"], "exact")
        self.assertIsNotNone(span["start"])

    def test_whitespace_insensitive(self):
        quote = "面对任何重要决定，  先问自己：什么情况下我会彻底失败？"
        self.assertTrue(verifier.find_quote_span(quote, SOURCE_TEXT)["found"])

    def test_punctuation_fuzzy(self):
        quote = "面对任何重要决定，先问自己什么情况下我会彻底失败"
        span = verifier.find_quote_span(quote, SOURCE_TEXT)
        self.assertTrue(span["found"])
        self.assertEqual(span["method"], "fuzzy")

    def test_missing(self):
        span = verifier.find_quote_span("这句话根本不存在于源文本", SOURCE_TEXT)
        self.assertFalse(span["found"])
        self.assertEqual(span["method"], "missing")


class LengthTest(unittest.TestCase):
    def test_chars_limit(self):
        ok, _ = verifier.quote_length_ok("短" * 151, 150, 100)
        self.assertFalse(ok)

    def test_words_limit(self):
        ok, _ = verifier.quote_length_ok("word " * 101, 150, 100)
        self.assertFalse(ok)

    def test_ok(self):
        ok, _ = verifier.quote_length_ok("短引用" * 10, 150, 100)
        self.assertTrue(ok)


class ClaimVerifyTest(unittest.TestCase):
    def setUp(self):
        self.cfg = ConfigStub()

    def test_verified(self):
        result = verifier.verify_claim(CLAIMS[0], SOURCE_TEXT, self.cfg)
        self.assertEqual(result["status"], "verified")
        self.assertTrue(result["source_span"])

    def test_numeric_review_when_no_origin(self):
        claim = dict(CLAIMS[0])
        claim["summary"] = "失败率高达 80%"
        result = verifier.verify_claim(claim, SOURCE_TEXT, self.cfg)
        self.assertEqual(result["status"], "numeric-review")

    def test_source_note_resolves_number(self):
        claim = dict(CLAIMS[0])
        claim["summary"] = "失败率高达 80%"
        claim["source_note"] = "原文上下文：80% 的失败源于准备不足"
        result = verifier.verify_claim(claim, SOURCE_TEXT, self.cfg)
        self.assertEqual(result["status"], "verified-with-notes")

    def test_unverified_quote(self):
        claim = dict(CLAIMS[0])
        claim["source_quote"] = "这段引文在源文本中不存在"
        result = verifier.verify_claim(claim, SOURCE_TEXT, self.cfg)
        self.assertEqual(result["status"], "unverified")

    def test_length_failed(self):
        claim = dict(CLAIMS[0])
        claim["source_quote"] = "长" * 151
        result = verifier.verify_claim(claim, SOURCE_TEXT, self.cfg)
        self.assertEqual(result["status"], "length-failed")

    def test_report_pass_with_fixture(self):
        report = verifier.verify_claims(CLAIMS, SOURCE_TEXT, self.cfg)
        self.assertTrue(report["pass"])
        self.assertEqual(report["verified"], 5)
        self.assertEqual(report["fidelity_rate"], 1.0)


if __name__ == "__main__":
    unittest.main()

