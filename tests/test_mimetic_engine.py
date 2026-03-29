import unittest

from app.core.mimetic_engine import MimeticEngine
from app.repository.in_memory import InMemoryRepository


class MimeticEngineTests(unittest.TestCase):
    def test_creates_entities_and_updates_stock(self) -> None:
        repo = InMemoryRepository()
        engine = MimeticEngine(repo)

        engine.ingest(
            "tenant-a",
            {"type": "purchase", "item": "tomate", "quantity": 10, "unit": "kg", "note": "compra"},
        )
        engine.ingest(
            "tenant-a",
            {"type": "consumption", "item": "tomate", "quantity": 3, "unit": "kg", "note": "consumo"},
        )

        snapshot = engine.build_snapshot("tenant-a")
        self.assertEqual(snapshot.stock["tomate"], 7)
        self.assertEqual(snapshot.consumption_trend["tomate"], 3)

        entities = repo.list_entities("tenant-a")
        self.assertEqual(len(entities), 1)
        self.assertEqual(entities[0].id, "inventory_item:tomate")

    def test_audit_trace_contains_events(self) -> None:
        repo = InMemoryRepository()
        engine = MimeticEngine(repo)

        engine.ingest("tenant-b", {"note": "se dañaron 2kg de carne", "quantity": 2, "item": "carne"})
        trace = engine.audit_trace("tenant-b")

        self.assertEqual(trace["tenant_id"], "tenant-b")
        self.assertEqual(len(trace["events"]), 1)
        self.assertEqual(len(trace["entities"]), 1)


if __name__ == "__main__":
    unittest.main()
