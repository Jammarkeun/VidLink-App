import unittest
from unittest.mock import Mock, patch
from backend.services.pipeline import MediaExtractionPipeline

class TestPipeline(unittest.TestCase):

    def setUp(self):
        self.pipeline = MediaExtractionPipeline()

    def test_url_validation(self):
        self.assertTrue(self.pipeline.validate_url("https://randomwebsite.com/video/123"))
        self.assertTrue(self.pipeline.validate_url("http://custom-domain.net/media"))
        self.assertFalse(self.pipeline.validate_url("ftp://example.com"))
        self.assertFalse(self.pipeline.validate_url("not_a_url"))

    def test_no_whitelist_acceptance(self):
        # Arbitrary non-whitelisted URLs must be accepted for analysis
        url = "https://arbitrary-nonexistent-site-xyz-123.org/watch"
        result = self.pipeline.analyze_url(url)
        self.assertIn("success", result)
        # Should return failure with NO_MEDIA_FOUND or error, never "Unsupported website"
        if not result["success"]:
            self.assertNotEqual(result.get("error"), "Website not supported.")
            self.assertIn(result.get("error_code"), ["NO_MEDIA_FOUND", "AUTHENTICATION_REQUIRED", "EXTRACTION_FAILED"])

    def test_direct_mp4_analysis(self):
        url = "https://sample-videos.com/video321/mp4/720/big_buck_bunny_720p_1mb.mp4"
        result = self.pipeline.analyze_url(url)
        self.assertTrue(result["success"])
        self.assertEqual(result["source_domain"], "sample-videos.com")
        self.assertTrue(result["total_formats_discovered"] > 0)
        self.assertEqual(result["formats"][0]["ext"], "mp4")

    @patch('backend.services.pipeline.requests.head')
    def test_pipeline_aggregates_all_applicable_extractors(self, mock_head):
        mock_head.return_value = Mock(status_code=200)

        first = Mock(name='FirstExtractor')
        first.name = 'FirstExtractor'
        first.can_handle.return_value = True
        first.analyze.return_value = {'title': 'Media', 'formats': [{'url': 'https://cdn.test/video.mp4', 'ext': 'mp4'}]}
        second = Mock(name='SecondExtractor')
        second.name = 'SecondExtractor'
        second.can_handle.return_value = True
        second.analyze.return_value = {'formats': [{'url': 'https://cdn.test/audio.mp3', 'ext': 'mp3', 'has_video': False, 'has_audio': True}]}

        self.pipeline.extractors = [first, second]
        with patch.object(self.pipeline, '_normalize_formats', side_effect=lambda formats: formats):
            result = self.pipeline.analyze_url('https://example.com/watch')

        self.assertTrue(result['success'])
        self.assertEqual(len(result['formats']), 2)

if __name__ == '__main__':
    unittest.main()
