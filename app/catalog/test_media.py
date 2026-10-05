import json
from pathlib import Path
import subprocess
from tempfile import TemporaryDirectory
from types import SimpleNamespace
from unittest.mock import patch

from django.conf import settings
from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from django.urls import reverse

from .forms import VideoForm
from .models import LocalMidia, Video
from .services import save_video


@override_settings(UI_DEMO=False)
class MediaTests(TestCase):
    def setUp(self):
        self.folder = TemporaryDirectory(dir=settings.BASE_DIR)
        self.addCleanup(self.folder.cleanup)
        self.root = Path(self.folder.name)
        self.settings_override = override_settings(PRIVATE_MEDIA_CACHE=self.root / 'cache')
        self.settings_override.enable()
        self.addCleanup(self.settings_override.disable)
        self.path = self.root / 'video.mp4'
        self.path.write_bytes(bytes(range(256)) * 4)
        self.local = LocalMidia.objects.create(name='Acervo', root_path=str(self.root))
        self.user = get_user_model().objects.create_user('media@example.com', 'test-password')
        self.client.force_login(self.user)
        with patch('app.catalog.inspection.subprocess.run', side_effect=FileNotFoundError):
            form = VideoForm(self.data())
            self.assertTrue(form.is_valid(), form.errors)
            self.video = save_video(form, self.user)
        self.url = reverse('studio:media_file', args=[self.video.pk])
        self.thumbnail_url = reverse('studio:thumbnail', args=[self.video.pk])

    def data(self, **changes):
        return {'title': 'Vídeo', 'local_midia': self.local.pk, 'relative_path': 'video.mp4', **changes}

    def body(self, response):
        result = b''.join(response.streaming_content) if response.streaming else response.content
        response.close()
        return result

    def fake_inspection(self, args, **kwargs):
        if '-show_entries' in args:
            return SimpleNamespace(stdout=json.dumps({'format': {'duration': '3.125'}, 'streams': [{'codec_type': 'video', 'codec_name': 'h264', 'width': 320, 'height': 180}]}))
        Path(args[-1]).write_bytes(b'\xff\xd8fixture-jpeg')
        return SimpleNamespace()

    def test_full_response_and_head(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'video/mp4')
        self.assertEqual(response['Content-Length'], '1024')
        self.assertEqual(response['Accept-Ranges'], 'bytes')
        self.assertEqual(response['Cache-Control'], 'private, no-store')
        self.assertEqual(self.body(response), self.path.read_bytes())
        response = self.client.head(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Length'], '1024')
        self.assertEqual(response.content, b'')

    def test_closed_open_suffix_and_clamped_ranges(self):
        raw = self.path.read_bytes()
        for value, start, end in [('bytes=10-19', 10, 19), ('bytes=1000-', 1000, 1023), ('bytes=-5', 1019, 1023), ('bytes=1000-9999', 1000, 1023), ('bytes=-9999', 0, 1023)]:
            with self.subTest(range=value):
                response = self.client.get(self.url, HTTP_RANGE=value)
                self.assertEqual(response.status_code, 206)
                self.assertEqual(response['Content-Range'], f'bytes {start}-{end}/1024')
                self.assertEqual(int(response['Content-Length']), end - start + 1)
                self.assertEqual(self.body(response), raw[start:end + 1])
        response = self.client.head(self.url, HTTP_RANGE='bytes=10-19')
        self.assertEqual(response.status_code, 206)
        self.assertEqual(response['Content-Length'], '10')
        self.assertEqual(response.content, b'')

    def test_invalid_ranges_are_416(self):
        for value in ['bytes=1024-', 'bytes=20-10', 'bytes=-0', 'bytes=-', 'bytes=0-1,4-5', 'garbage', 'bytes=' + '9' * 30 + '-']:
            with self.subTest(range=value):
                response = self.client.get(self.url, HTTP_RANGE=value)
                self.assertEqual(response.status_code, 416)
                self.assertEqual(response['Content-Range'], 'bytes */1024')
        self.path.write_bytes(b'')
        self.assertEqual(self.client.get(self.url, HTTP_RANGE='bytes=0-').status_code, 416)
        response = self.client.get(self.url)
        self.assertEqual(response['Content-Length'], '0')
        self.assertEqual(self.body(response), b'')

    def test_if_range_matches_etag_and_stale_validator_falls_back(self):
        response = self.client.head(self.url)
        ranged = self.client.get(self.url, HTTP_RANGE='bytes=0-9', HTTP_IF_RANGE=response['ETag'])
        self.assertEqual(ranged.status_code, 206)
        self.body(ranged)
        ranged = self.client.get(self.url, HTTP_RANGE='bytes=0-9', HTTP_IF_RANGE=response['Last-Modified'])
        self.assertEqual(ranged.status_code, 206)
        self.body(ranged)
        stale = self.client.get(self.url, HTTP_RANGE='bytes=0-9', HTTP_IF_RANGE='"old"')
        self.assertEqual(stale.status_code, 200)
        self.assertEqual(len(self.body(stale)), 1024)

    def test_missing_media_preserves_editable_record_and_no_player(self):
        self.path.unlink()
        self.assertEqual(self.client.get(self.url).status_code, 404)
        editor = self.client.get(reverse('studio:editor', args=[self.video.pk]))
        self.assertContains(editor, 'Arquivo não encontrado')
        self.assertNotContains(editor, 'data-real-player>')
        self.assertTrue(Video.objects.filter(pk=self.video.pk).exists())

    def test_inactive_root_and_tampered_paths_block_delivery(self):
        self.local.active = False
        self.local.save()
        self.assertEqual(self.client.get(self.url).status_code, 404)
        self.local.active = True
        self.local.save()
        Video.objects.filter(pk=self.video.pk).update(relative_path='../secret.mp4')
        self.assertEqual(self.client.get(self.url).status_code, 404)

    def test_non_video_active_content_is_not_served_inline(self):
        target = self.root / 'page.html'
        target.write_text('<script>bad()</script>', encoding='utf-8')
        Video.objects.filter(pk=self.video.pk).update(relative_path='page.html')
        self.assertEqual(self.client.get(self.url).status_code, 415)

    def test_anonymous_media_thumbnail_and_reinspection_require_authentication(self):
        self.client.logout()
        for url in [self.url, self.thumbnail_url, reverse('studio:reinspect', args=[self.video.pk])]:
            self.assertEqual(self.client.get(url).status_code, 302)
        self.assertEqual(self.client.post(reverse('studio:reinspect', args=[self.video.pk])).status_code, 302)

    def test_inspection_extracts_duration_and_generated_thumbnail(self):
        with patch('app.catalog.inspection.subprocess.run', side_effect=self.fake_inspection):
            response = self.client.post(reverse('studio:reinspect', args=[self.video.pk]))
        self.assertEqual(response.status_code, 302)
        self.video.refresh_from_db()
        self.assertEqual(self.video.duration_ms, 3125)
        self.assertEqual(self.video.duration_source, 'automatic')
        self.assertEqual(self.video.codec, 'h264')
        self.assertEqual((self.video.width, self.video.height), (320, 180))
        self.assertEqual(self.video.size_bytes, 1024)
        self.assertEqual(self.video.inspection_status, 'ready')
        self.assertTrue(self.video.thumbnail_key)
        response = self.client.get(self.thumbnail_url)
        self.assertEqual(response['Content-Type'], 'image/jpeg')
        self.assertTrue(self.body(response).startswith(b'\xff\xd8'))
        self.assertEqual(self.client.head(self.thumbnail_url).status_code, 200)

    def test_tool_missing_and_timeouts_never_block_save_and_manual_duration(self):
        for error in [FileNotFoundError(), subprocess.TimeoutExpired('ffprobe', 10), subprocess.CalledProcessError(1, 'ffprobe'), ValueError('bad-json')]:
            with self.subTest(error=type(error).__name__):
                form = VideoForm(self.data(duration_ms='60000'), instance=self.video)
                self.assertTrue(form.is_valid(), form.errors)
                with patch('app.catalog.inspection.subprocess.run', side_effect=error):
                    self.video.inspection_status = 'pending'
                    video = save_video(form, self.user)
                    from .inspection import inspect_video
                    inspect_video(video, self.path)
                    video.save()
                self.video.refresh_from_db()
                self.assertEqual(self.video.duration_ms, 60000)
                self.assertEqual(self.video.duration_source, 'manual')
                self.assertTrue(self.video.inspection_message)

    def test_reinspection_preserves_manual_override(self):
        form = VideoForm(self.data(duration_ms='90000'), instance=self.video)
        self.assertTrue(form.is_valid(), form.errors)
        save_video(form, self.user)
        with patch('app.catalog.inspection.subprocess.run', side_effect=self.fake_inspection):
            self.client.post(reverse('studio:reinspect', args=[self.video.pk]))
        self.video.refresh_from_db()
        self.assertEqual(self.video.duration_ms, 90000)
        self.assertEqual(self.video.duration_source, 'manual')

    def test_manual_thumbnail_is_validated_and_served_privately(self):
        image = self.root / 'cover.png'
        image.write_bytes(b'\x89PNG\r\n\x1a\nfixture')
        form = VideoForm(self.data(duration_ms='10000', thumbnail_relative_path='cover.png'), instance=self.video)
        self.assertTrue(form.is_valid(), form.errors)
        save_video(form, self.user)
        response = self.client.get(self.thumbnail_url)
        self.assertEqual(response['Content-Type'], 'image/png')
        self.assertEqual(self.body(response), image.read_bytes())
        for path in ['../cover.png', 'page.svg', 'missing.png']:
            form = VideoForm(self.data(thumbnail_relative_path=path), instance=self.video)
            self.assertFalse(form.is_valid())
            self.assertIn('thumbnail_relative_path', form.errors)

    def test_failed_thumbnail_generation_retains_technical_metadata(self):
        def run(args, **kwargs):
            if '-show_entries' in args:
                return self.fake_inspection(args, **kwargs)
            raise FileNotFoundError()
        with patch('app.catalog.inspection.subprocess.run', side_effect=run):
            self.client.post(reverse('studio:reinspect', args=[self.video.pk]))
        self.video.refresh_from_db()
        self.assertEqual(self.video.duration_ms, 3125)
        self.assertEqual(self.video.inspection_status, 'ready')
        self.assertEqual(self.video.thumbnail_key, '')
        self.assertIn('miniatura indisponível', self.video.inspection_message)

    def test_unsupported_probe_result_is_handled(self):
        with patch('app.catalog.inspection.subprocess.run', return_value=SimpleNamespace(stdout='{"streams":[]}')):
            self.client.post(reverse('studio:reinspect', args=[self.video.pk]))
        self.video.refresh_from_db()
        self.assertEqual(self.video.inspection_status, 'failed')

    @override_settings(UI_DEMO=True)
    def test_demo_blocks_real_media_and_reinspection(self):
        self.assertEqual(self.client.get(self.url).status_code, 403)
        self.assertEqual(self.client.get(self.thumbnail_url).status_code, 403)
        self.assertEqual(self.client.post(reverse('studio:reinspect', args=[self.video.pk])).status_code, 403)

    def test_changed_reference_invalidates_duration_and_thumbnail(self):
        with patch('app.catalog.inspection.subprocess.run', side_effect=self.fake_inspection):
            self.client.post(reverse('studio:reinspect', args=[self.video.pk]))
        self.video.refresh_from_db()
        form = VideoForm(self.data(relative_path='missing.mp4', duration_ms=str(self.video.duration_ms)), instance=self.video)
        self.assertTrue(form.is_valid(), form.errors)
        save_video(form, self.user)
        self.video.refresh_from_db()
        self.assertIsNone(self.video.duration_ms)
        self.assertEqual(self.video.thumbnail_key, '')
        self.assertEqual(self.video.inspection_status, 'unavailable')
