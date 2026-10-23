from django.test import TestCase
from django.urls import reverse


class ResearchQuestionnaireTests(TestCase):
    def test_questionnaire_is_reachable_from_the_home_page(self):
        home_response = self.client.get(reverse("home_page"))
        questionnaire_response = self.client.get(reverse("research_questionnaire"))

        self.assertContains(home_response, reverse("research_questionnaire"))
        self.assertEqual(questionnaire_response.status_code, 200)
        self.assertContains(questionnaire_response, "Questions 1–2 of 10")
        self.assertContains(questionnaire_response, "Academic researcher")
        self.assertContains(questionnaire_response, "Define a custom AI role.")
        self.assertContains(questionnaire_response, 'name="role_other"')
        self.assertContains(questionnaire_response, 'id="submit-button" type="submit" hidden>Next</button>')
        self.assertContains(questionnaire_response, 'value="fundamental_background" checked')
        self.assertContains(questionnaire_response, 'value="detailed" checked')
        self.assertContains(questionnaire_response, 'value="standard_presentation" checked')

    def test_valid_answers_are_saved_as_a_reusable_dictionary(self):
        response = self.client.post(
            reverse("research_questionnaire"),
            {
                "topic": "AI in healthcare",
                "role": "academic_researcher",
                "objective": "Compare diagnostic methods",
                "scope": [
                    "fundamental_background",
                    "current_developments",
                    "case_studies",
                    "future_trends",
                ],
                "audience": "researchers_experts",
                "evidence": ["peer_reviewed_papers", "government_reports"],
                "critical_analysis": "balanced_analysis",
                "outputs": [
                    "research_report",
                    "presentation_slides",
                    "executive_summary",
                    "reference_list",
                ],
                "report_word_count": "detailed",
                "slide_count": "standard_presentation",
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Your research brief is saved")
        self.assertEqual(
            self.client.session["research_requirements"],
            {
                "topic": "AI in healthcare",
                "role": "Academic researcher: conduct evidence-based research and synthesize credible sources.",
                "objective": "Compare diagnostic methods",
                "scope": [
                    "fundamental_background",
                    "current_developments",
                    "case_studies",
                    "future_trends",
                ],
                "scope_other": "",
                "audience": "researchers_experts",
                "audience_other": "",
                "evidence": ["peer_reviewed_papers", "government_reports"],
                "evidence_other": "",
                "critical_analysis": "balanced_analysis",
                "outputs": [
                    "research_report",
                    "presentation_slides",
                    "executive_summary",
                    "reference_list",
                ],
                "report_word_count": 1500,
                "slide_count": 8,
            },
        )

    def test_custom_answers_and_other_details_are_normalized(self):
        response = self.client.post(
            reverse("research_questionnaire"),
            {
                "topic": "AI in healthcare",
                "role": "other",
                "role_other": "Healthcare technology researcher",
                "objective": "Compare diagnostic methods",
                "scope": ["other"],
                "scope_other": "Patient privacy",
                "audience": "other",
                "audience_other": "Hospital administrators",
                "evidence": ["other"],
                "evidence_other": "Clinical trial registries",
                "critical_analysis": "deep_critical_evaluation",
                "outputs": ["research_report"],
                "report_word_count": "custom",
                "report_word_count_custom": "2200",
                "slide_count": "custom",
                "slide_count_custom": "10",
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            self.client.session["research_requirements"]["role"],
            "Healthcare technology researcher",
        )
        self.assertEqual(self.client.session["research_requirements"]["scope_other"], "Patient privacy")
        self.assertEqual(self.client.session["research_requirements"]["audience_other"], "Hospital administrators")
        self.assertEqual(self.client.session["research_requirements"]["evidence_other"], "Clinical trial registries")
        self.assertEqual(self.client.session["research_requirements"]["report_word_count"], 2200)
        self.assertEqual(self.client.session["research_requirements"]["slide_count"], 10)

    def test_invalid_answers_are_rejected(self):
        response = self.client.post(
            reverse("research_questionnaire"),
            {
                "topic": "",
                "role": "academic_researcher",
                "objective": "Compare diagnostic methods",
                "audience": "researchers_experts",
                "critical_analysis": "balanced_analysis",
                "report_word_count": "detailed",
                "slide_count": "standard_presentation",
            },
        )

        self.assertEqual(response.status_code, 400)
        self.assertContains(response, "Topic and objective are required.", status_code=400)
        self.assertNotIn("research_requirements", self.client.session)

    def test_invalid_role_and_empty_custom_role_are_rejected(self):
        questionnaire_url = reverse("research_questionnaire")
        answers = {
            "topic": "AI in healthcare",
            "objective": "Compare diagnostic methods",
            "scope": ["fundamental_background"],
            "audience": "researchers_experts",
            "evidence": ["peer_reviewed_papers"],
            "critical_analysis": "balanced_analysis",
            "outputs": ["research_report"],
            "report_word_count": "detailed",
            "slide_count": "standard_presentation",
        }

        invalid_role_response = self.client.post(
            questionnaire_url,
            {**answers, "role": "made_up_role"},
        )
        self.assertEqual(invalid_role_response.status_code, 400)
        self.assertContains(invalid_role_response, "Choose a valid AI role.", status_code=400)

        empty_custom_role_response = self.client.post(
            questionnaire_url,
            {**answers, "role": "other", "role_other": "   "},
        )
        self.assertEqual(empty_custom_role_response.status_code, 400)
        self.assertContains(empty_custom_role_response, "Define your custom AI role.", status_code=400)

        long_custom_role_response = self.client.post(
            questionnaire_url,
            {**answers, "role": "other", "role_other": "x" * 201},
        )
        self.assertEqual(long_custom_role_response.status_code, 400)
        self.assertContains(
            long_custom_role_response,
            "Keep your custom AI role to 200 characters or fewer.",
            status_code=400,
        )
