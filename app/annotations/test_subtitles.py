from unittest.mock import patch

from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile
from django.db import IntegrityError, transaction
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from .models import SubtitleEntry, SubtitleVersion
from .srt import MAX_BYTES, parse_srt
from .subtitle_forms import ImportForm
from .subtitle_services import import_version
from . import tests as marking_tests

SRT = b'8\r\n00:00:00,500 --> 00:00:01,125\r\nPrimeira linha\r\nSegunda linha\r\n\r\n3\r\n00:00:01,000 --> 00:00:02,750\r\nOutro trecho\r\n'


@override_settings(UI_DEMO=False)
class SubtitleTests(TestCase):
    setUp = marking_tests.MarkingTests.setUp
    def upload(self, name='Português', content=SRT):
        form = ImportForm({'name': name, 'language': 'pt-BR'}, {'srt_file': SimpleUploadedFile('teste.srt', content)}, video=self.video)
        self.assertTrue(form.is_valid(), form.errors)
        return import_version(form, self.user)

    def test_parser_bom_missing_numbers_overlap_and_multiline(self):
        entries = parse_srt(b'\xef\xbb\xbf' + SRT)
        self.assertEqual(entries[0]['end_ms'], 1125)
        self.assertEqual(entries[0]['text'], 'Primeira linha\nSegunda linha')
        self.assertEqual(parse_srt(b'00:00:00,000 --> 00:00:01,000\nSem numero')[0]['start_ms'], 0)

    def test_parser_rejects_malformed_empty_encoding_times_and_limits(self):
        for content in [b'', b'1\ninvalid\ntext', b'\xff', b'00:00:00,000 --> 00:00:00,000\ntext', b'00:60:00,000 --> 00:61:00,000\ntext', b'00:00:00,000 --> 00:00:01,000\n', b'x' * (MAX_BYTES + 1), b'00:00:00,000 --> 00:00:01,000\n' + b'a' * 10001]:
            with self.subTest(content=content[:40]), self.assertRaises(ValidationError):
                parse_srt(content)
        with self.assertRaisesMessage(ValidationError, 'Linha 2'):
            parse_srt(SRT, duration_ms=1000)

    def test_import_atomic_first_active_and_subsequent_inactive(self):
        first, second = self.upload(), self.upload('Outra')
        self.assertTrue(first.active)
        self.assertFalse(second.active)
        self.assertEqual(first.entries.count(), 2)
        self.assertEqual(first.created_by, self.user)
        form = ImportForm({'name': 'Falha'}, {'srt_file': SimpleUploadedFile('a.srt', SRT)}, video=self.video)
        self.assertTrue(form.is_valid())
        with patch('app.annotations.subtitle_services.SubtitleEntry.objects.bulk_create', side_effect=IntegrityError), self.assertRaises(IntegrityError):
            import_version(form, self.user)
        self.assertEqual(SubtitleVersion.objects.count(), 2)

    def test_import_endpoint_error_preserves_input_no_partial_records(self):
        response = self.client.post(reverse('studio:import_srt', args=[self.video.pk]), {'name': 'Nome digitado', 'srt_file': SimpleUploadedFile('a.srt', b'1\ninvalid')})
        self.assertContains(response, 'Nome digitado', status_code=400)
        self.assertContains(response, 'Linha 2', status_code=400)
        self.assertFalse(SubtitleVersion.objects.exists())

    def test_activate_one_version_and_database_constraint(self):
        first, second = self.upload(), self.upload('Outra')
        self.assertEqual(self.client.post(reverse('studio:activate_subtitles', args=[self.video.pk, second.pk])).status_code, 302)
        self.assertEqual(list(self.video.subtitle_versions.filter(active=True)), [second])
        with self.assertRaises(IntegrityError), transaction.atomic():
            SubtitleVersion.objects.filter(pk=first.pk).update(active=True)

    def test_create_edit_remove_entry_preserves_video_and_version(self):
        version = self.upload()
        data = {'start_ms': '00:00.125', 'end_ms': '00:00.750', 'text': 'Nova\nlinha'}
        self.assertEqual(self.client.post(reverse('studio:create_subtitle_entry', args=[self.video.pk, version.pk]), data).status_code, 302)
        entry = version.entries.get(text=data['text'])
        data['text'] = 'Revisada'
        self.assertEqual(self.client.post(reverse('studio:save_subtitle_entry', args=[self.video.pk, version.pk, entry.pk]), data).status_code, 302)
        entry.refresh_from_db()
        self.assertEqual(entry.text, 'Revisada')
        self.assertContains(self.client.get(reverse('studio:confirm_remove_subtitle_entry', args=[self.video.pk, version.pk, entry.pk])), 'Confirmar remoção')
        self.assertTrue(SubtitleEntry.objects.filter(pk=entry.pk).exists())
        self.assertEqual(self.client.post(reverse('studio:remove_subtitle_entry', args=[self.video.pk, version.pk, entry.pk])).status_code, 302)
        self.assertEqual(version.entries.count(), 2)
        self.assertTrue(self.video.subtitle_versions.exists())

    def test_invalid_edit_and_duration_reduction_keep_data(self):
        version = self.upload()
        entry = version.entries.first()
        response = self.client.post(reverse('studio:save_subtitle_entry', args=[self.video.pk, version.pk, entry.pk]), {'start_ms': '00:03', 'end_ms': '00:02', 'text': 'Digitado'})
        self.assertContains(response, 'Digitado', status_code=400)
        entry.refresh_from_db()
        self.assertEqual(entry.start_ms, 500)
        self.video.duration_ms = 1000
        with self.assertRaises(ValidationError):
            self.video.save()

    def test_import_rechecks_current_duration(self):
        form = ImportForm({'name': 'Teste'}, {'srt_file': SimpleUploadedFile('a.srt', SRT)}, video=self.video)
        self.assertTrue(form.is_valid())
        type(self.video).objects.filter(pk=self.video.pk).update(duration_ms=1000)
        with self.assertRaises(ValidationError):
            import_version(form, self.user)
        self.assertFalse(SubtitleVersion.objects.exists())

    def test_nested_parent_authorization_post_and_csrf(self):
        version = self.upload()
        entry = version.entries.first()
        for name, args in [('subtitle_version', [999, version.pk]), ('edit_subtitle_entry', [self.video.pk, 999, entry.pk])]:
            self.assertEqual(self.client.get(reverse('studio:' + name, args=args)).status_code, 404)
        url = reverse('studio:activate_subtitles', args=[self.video.pk, version.pk])
        self.assertEqual(self.client.get(url).status_code, 405)
        csrf = Client(enforce_csrf_checks=True)
        csrf.force_login(self.user)
        self.assertEqual(csrf.post(url).status_code, 403)
        self.client.logout()
        self.assertEqual(self.client.get(reverse('studio:subtitles', args=[self.video.pk])).status_code, 302)

    def test_active_only_safe_player_payload_and_version_edit(self):
        first = self.upload()
        second = self.upload('Inativa', b'1\n00:00:00,000 --> 00:00:01,000\nINATIVA_UNICA')
        first.entries.filter(pk=first.entries.first().pk).update(text='<script>alert(1)</script>')
        response = self.client.get(reverse('studio:editor', args=[self.video.pk]))
        self.assertContains(response, '\\u003Cscript\\u003E')
        self.assertNotContains(response, 'INATIVA_UNICA')
        response = self.client.post(reverse('studio:save_subtitle_version', args=[self.video.pk, second.pk]), {'name': 'Renomeada', 'language': 'en'})
        self.assertEqual(response.status_code, 302)
        second.refresh_from_db()
        self.assertEqual(second.name, 'Renomeada')
        self.assertFalse(second.active)

    @override_settings(UI_DEMO=True)
    def test_demo_blocks_subtitle_mutations(self):
        self.assertEqual(self.client.post(reverse('studio:import_srt', args=[self.video.pk])).status_code, 403)
