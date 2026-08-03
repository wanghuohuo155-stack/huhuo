import tempfile
import unittest
from pathlib import Path

import _paths  # noqa: F401

from rushi.store import Store
from fixtures import CLAIMS


class StoreTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.store = Store(Path(self.tmp.name) / "state.db")

    def tearDown(self):
        self.store.close()
        self.tmp.cleanup()

    def test_claim_upsert_and_stats(self):
        for c in CLAIMS:
            self.store.upsert_claim(c)
        self.assertEqual(len(self.store.claims()), 5)
        self.assertEqual(self.store.claim_stats()["pending"], 5)

    def test_claim_upsert_overwrite(self):
        c = dict(CLAIMS[0])
        self.store.upsert_claim(c)
        c["status"] = "verified"
        self.store.upsert_claim(c)
        rows = self.store.claims()
        self.assertEqual(rows[0]["status"], "verified")

    def test_telemetry(self):
        self.store.add_telemetry("slow-gardener", "invocations")
        self.store.add_telemetry("slow-gardener", "mis_trigger")
        rows = self.store.telemetry("slow-gardener")
        self.assertEqual(len(rows), 2)
        self.assertEqual(rows[1]["event"], "mis_trigger")

    def test_export_import_jsonl(self):
        for c in CLAIMS:
            self.store.upsert_claim(c)
        path = Path(self.tmp.name) / "claims.jsonl"
        self.store.export_claims_jsonl(path)
        self.store2 = Store(Path(self.tmp.name) / "state2.db")
        n = self.store2.import_claims_jsonl(path)
        self.assertEqual(n, 5)
        self.store2.close()


if __name__ == "__main__":
    unittest.main()

