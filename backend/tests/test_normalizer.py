import unittest
from normalizer import parse_experience_string, normalize_job_dict

class TestNormalizer(unittest.TestCase):

    def test_experience_parsing(self):
        self.assertEqual(parse_experience_string("0-1 Years"), (0.0, 1.0))
        self.assertEqual(parse_experience_string("0 to 1 Yrs"), (0.0, 1.0))
        self.assertEqual(parse_experience_string("1-2 years"), (1.0, 2.0))
        self.assertEqual(parse_experience_string("2+ years"), (2.0, None))
        self.assertEqual(parse_experience_string("Freshers welcome"), (0.0, 0.0))
        self.assertEqual(parse_experience_string("1 year"), (1.0, 1.0))
        self.assertEqual(parse_experience_string(""), (None, None))
        self.assertEqual(parse_experience_string(None), (None, None))

    def test_job_normalization(self):
        raw = {
            "company": " Flipkart ",
            "title": " Software Development Engineer 1 ",
            "location": "Bengaluru, Karnataka",
            "link": "https://flipkart.com/jobs/123",
            "experience_text": "0-1 years",
        }
        normalized = normalize_job_dict(raw)
        self.assertEqual(normalized["company"], "Flipkart")
        self.assertEqual(normalized["title"], "Software Development Engineer 1")
        self.assertEqual(normalized["min_exp"], 0.0)
        self.assertEqual(normalized["max_exp"], 1.0)
        self.assertEqual(normalized["country"], "India")
        self.assertEqual(normalized["apply_link"], "https://flipkart.com/jobs/123")

if __name__ == "__main__":
    unittest.main()
