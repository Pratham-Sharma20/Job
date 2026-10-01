import unittest
from filters import evaluate_job, is_india_location, get_technical_track, is_senior_role

class TestFilters(unittest.TestCase):

    def test_positive_cases(self):
        # 1. Software Engineer with explicit 0-1 years
        res = evaluate_job(
            title="Software Engineer",
            location="Bangalore, Karnataka",
            min_exp=0,
            max_exp=1
        )
        self.assertTrue(res["valid"])
        self.assertEqual(res["reason"], "valid_experience")
        self.assertEqual(res["track"], "Software Engineering")

        # 2. Software Engineer with experience_text
        res = evaluate_job(
            title="Software Engineer",
            location="Bengaluru",
            experience_text="0-1 years"
        )
        self.assertTrue(res["valid"])
        self.assertIn(res["reason"], ["valid_fresher", "valid_experience"])

        # 3. Software Engineer Intern with missing experience
        res = evaluate_job(
            title="Software Engineer Intern",
            location="Hyderabad",
            min_exp=None,
            max_exp=None
        )
        self.assertTrue(res["valid"])
        self.assertEqual(res["reason"], "valid_intern")

        # 4. SDE 1 with missing experience
        res = evaluate_job(
            title="SDE 1",
            location="Pune, India",
            min_exp=None,
            max_exp=None
        )
        self.assertTrue(res["valid"])
        self.assertEqual(res["reason"], "valid_fresher")

        # 5. Graduate Software Engineer with missing experience
        res = evaluate_job(
            title="Graduate Software Engineer",
            location="Gurugram",
            min_exp=None,
            max_exp=None
        )
        self.assertTrue(res["valid"])
        self.assertEqual(res["reason"], "valid_fresher")

        # 6. Machine Learning Engineer (0-1 yrs exp)
        res = evaluate_job(
            title="Machine Learning Engineer",
            location="Noida, Uttar Pradesh",
            min_exp=0,
            max_exp=1
        )
        self.assertTrue(res["valid"])
        self.assertEqual(res["track"], "AI / ML")
        self.assertEqual(res["reason"], "valid_experience")

        # 7. Data Engineer Intern
        res = evaluate_job(
            title="Data Engineer Intern",
            location="India",
            min_exp=None,
            max_exp=None
        )
        self.assertTrue(res["valid"])
        self.assertEqual(res["track"], "Data Engineering")
        self.assertEqual(res["reason"], "valid_intern")

        # 8. SDE Specialist (specialist should NOT be rejected as senior!)
        res = evaluate_job(
            title="Software Engineer Specialist",
            location="Bengaluru",
            min_exp=0,
            max_exp=1
        )
        self.assertTrue(res["valid"])

    def test_negative_cases(self):
        # 1. Software Engineer with 1-2 years
        res = evaluate_job(
            title="Software Engineer",
            location="Bangalore",
            min_exp=1,
            max_exp=2
        )
        self.assertFalse(res["valid"])
        self.assertEqual(res["reason"], "experience_too_high")

        # 2. Software Engineer with 0-2 years
        res = evaluate_job(
            title="Software Engineer",
            location="Bangalore",
            min_exp=0,
            max_exp=2
        )
        self.assertFalse(res["valid"])
        self.assertEqual(res["reason"], "experience_too_high")

        # 3. Software Engineer with min 2+ years
        res = evaluate_job(
            title="Software Engineer",
            location="Bangalore",
            min_exp=2
        )
        self.assertFalse(res["valid"])
        self.assertEqual(res["reason"], "experience_too_high")

        # 4. Plain Software Engineer with missing experience
        res = evaluate_job(
            title="Software Engineer",
            location="Bangalore",
            min_exp=None,
            max_exp=None
        )
        self.assertFalse(res["valid"])
        self.assertEqual(res["reason"], "missing_early_career_signal")

        # 5. Senior Software Engineer
        res = evaluate_job(
            title="Senior Software Engineer",
            location="Bangalore",
            min_exp=0,
            max_exp=1
        )
        self.assertFalse(res["valid"])
        self.assertEqual(res["reason"], "senior_role")

        # 6. Lead SDE
        res = evaluate_job(
            title="Lead SDE",
            location="Bengaluru",
            min_exp=0,
            max_exp=1
        )
        self.assertFalse(res["valid"])
        self.assertEqual(res["reason"], "senior_role")

        # 7. Engineering Manager
        res = evaluate_job(
            title="Software Engineering Manager",
            location="Hyderabad"
        )
        self.assertFalse(res["valid"])
        self.assertEqual(res["reason"], "senior_role")

        # 8. Non-India location
        res = evaluate_job(
            title="Software Engineer Intern",
            location="San Francisco, CA",
            country="United States"
        )
        self.assertFalse(res["valid"])
        self.assertEqual(res["reason"], "non_india")

        # 9. Non-technical role
        res = evaluate_job(
            title="HR Intern",
            location="Bengaluru, India"
        )
        self.assertFalse(res["valid"])
        self.assertEqual(res["reason"], "non_technical")

if __name__ == "__main__":
    unittest.main()
