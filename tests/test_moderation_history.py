import unittest
from datetime import date

import app as website


class ModerationHistoryTests(unittest.TestCase):
    def test_filter_parsing_clamps_pages_and_normalizes_actions(self):
        filters = website._moderation_case_filters({
            "page": "-4",
            "q": "  member-123  ",
            "action": " TIMEOUT ",
            "date_from": "2026-10-01",
            "date_to": "not-a-date",
        })

        self.assertEqual(filters["page"], 1)
        self.assertEqual(filters["q"], "member-123")
        self.assertEqual(filters["action"], "timeout")
        self.assertEqual(filters["date_from"], date(2026, 10, 1))
        self.assertIsNone(filters["date_to"])

    def test_filter_values_are_parameterized(self):
        filters = {
            "q": "' OR 1=1 --",
            "action": "warn",
            "date_from": date(2026, 10, 1),
            "date_to": date(2026, 10, 25),
        }
        where, params = website._moderation_case_where("12345", filters)

        self.assertIn("ILIKE %s", where)
        self.assertNotIn("' OR 1=1 --", where)
        self.assertEqual(params[0], "12345")
        self.assertIn("%' OR 1=1 --%", params)
        self.assertEqual(params[-3:], ["warn", date(2026, 10, 1), date(2026, 10, 25)])

    def test_csv_cells_neutralize_spreadsheet_formulas(self):
        self.assertEqual(website._safe_csv_cell("=HYPERLINK(\"https://example.test\")"), "'=HYPERLINK(\"https://example.test\")")
        self.assertEqual(website._safe_csv_cell("Normal reason"), "Normal reason")


if __name__ == "__main__":
    unittest.main()
