import unittest
from unittest.mock import patch, MagicMock
from pipeline import PipelineMetrics, process_single_job

class TestPipeline(unittest.TestCase):

    @patch("pipeline.jobs_collection")
    @patch("pipeline.send_telegram_notification")
    def test_pipeline_qualified_and_saved(self, mock_notify, mock_db):
        mock_result = MagicMock()
        mock_result.upserted_id = "test_mongo_id"
        mock_db.update_one.return_value = mock_result

        metrics = PipelineMetrics("TestScraper")
        raw = {
            "company": "TestCo",
            "title": "Software Engineer",
            "location": "Bangalore, India",
            "link": "https://testco.com/job/1",
            "min_exp": 0,
            "max_exp": 1
        }

        saved = process_single_job(raw, metrics)
        self.assertIsNotNone(saved)
        self.assertEqual(metrics.fetched, 1)
        self.assertEqual(metrics.qualified, 1)
        self.assertEqual(metrics.saved, 1)
        self.assertEqual(metrics.new_jobs, 1)
        mock_notify.assert_called_once()

    @patch("pipeline.jobs_collection")
    def test_pipeline_rejected_senior(self, mock_db):
        metrics = PipelineMetrics("TestScraper")
        raw = {
            "company": "TestCo",
            "title": "Senior Software Engineer",
            "location": "Bangalore, India",
            "link": "https://testco.com/job/2",
            "min_exp": 0,
            "max_exp": 1
        }

        saved = process_single_job(raw, metrics)
        self.assertIsNone(saved)
        self.assertEqual(metrics.fetched, 1)
        self.assertEqual(metrics.qualified, 0)
        self.assertEqual(metrics.rejection_reasons.get("senior_role"), 1)

if __name__ == "__main__":
    unittest.main()
