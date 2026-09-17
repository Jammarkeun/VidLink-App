import unittest
from unittest.mock import Mock, patch
from backend.extractors import (
    DirectMediaExtractor,
    HLSExtractor,
    DASHExtractor,
    HTMLMediaExtractor,
    MetadataExtractor,
    GenericExtractor
)

class TestExtractors(unittest.TestCase):

    def test_direct_media_can_handle(self):
        extractor = DirectMediaExtractor()
        self.assertTrue(extractor.can_handle("https://example.com/video.mp4"))
        self.assertTrue(extractor.can_handle("https://cdn.test.net/audio/podcast.mp3"))
        self.assertFalse(extractor.can_handle("https://example.com/watch/video"))

    def test_direct_media_analyze(self):
        extractor = DirectMediaExtractor()
        url = "https://cdn.example.org/sample_video.mp4"
        res = extractor.analyze(url)
        self.assertIsNotNone(res)
        self.assertEqual(res['extractor_name'], "DirectMediaExtractor")
        self.assertTrue(len(res['formats']) > 0)
        self.assertEqual(res['formats'][0]['ext'], 'mp4')

    def test_hls_can_handle(self):
        extractor = HLSExtractor()
        self.assertTrue(extractor.can_handle("https://stream.example.com/playlist.m3u8"))
        self.assertTrue(extractor.can_handle("https://cdn.site.com/master.m3u8?token=xyz"))
        self.assertFalse(extractor.can_handle("https://site.com/index.html"))

    def test_dash_can_handle(self):
        extractor = DASHExtractor()
        self.assertTrue(extractor.can_handle("https://stream.example.com/manifest.mpd"))
        self.assertFalse(extractor.can_handle("https://site.com/video.mp4"))

    @patch('backend.extractors.dash_extractor.requests.get')
    def test_dash_resolves_representation_base_url(self, mock_get):
        mock_get.return_value = Mock(
            status_code=200,
            text='<MPD xmlns="urn:mpeg:dash:schema:mpd:2011"><BaseURL>media/</BaseURL>'
                  '<Period><AdaptationSet mimeType="video/mp4"><Representation id="v1" height="720" bandwidth="1000000">'
                  '<BaseURL>video.mp4</BaseURL></Representation></AdaptationSet></Period></MPD>'
        )
        result = DASHExtractor().analyze('https://cdn.example.com/manifest.mpd')
        self.assertEqual(result['formats'][0]['url'], 'https://cdn.example.com/media/video.mp4')

if __name__ == '__main__':
    unittest.main()
