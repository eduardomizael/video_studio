from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from app.catalog.models import LocalMidia, Pessoa, Tag, Video
from app.catalog.forms import VideoForm
from app.catalog.services import save_video
from .forms import MarkingForm
from .models import MarcacaoTemporal
from .services import save_marking
from .timecodes import format_timecode, parse_timecode


@override_settings(UI_DEMO=False)
class MarkingTests(TestCase):
    def setUp(self):
        self.folder = TemporaryDirectory(dir=settings.BASE_DIR)
        self.addCleanup(self.folder.cleanup)
        self.local = LocalMidia.objects.create(name='Acervo de teste', root_path=self.folder.name)
        self.user = get_user_model().objects.create_user('marking@example.com', 'test-password', first_name='Ana')
        self.other_user = get_user_model().objects.create_user('other@example.com', 'test-password')
        self.client.force_login(self.user)
        self.video = Video.objects.create(title='Vídeo', local_midia=self.local, relative_path='missing.mp4', duration_ms=120000, duration_source='manual', created_by=self.user, updated_by=self.user)
        self.tag = Tag.objects.create(name='Cena')
        self.person = Pessoa.objects.create(name='Pessoa de teste')
        self.create_url = reverse('studio:create_marking', args=[self.video.pk])

    def data(self, **changes):
        return {'title': 'Trecho importante', 'start_ms': '00:10.125', 'end_ms': '', 'tags': [self.tag.pk], 'people': [self.person.pk], **changes}

    def create(self, **changes):
        form = MarkingForm(self.data(**changes), video=self.video)
        self.assertTrue(form.is_valid(), form.errors)
        return save_marking(form, self.user)

    def test_point_interval_overlap_and_chronological_order(self):
        self.assertEqual(self.client.post(self.create_url, self.data(start_ms='00:20.500', end_ms='00:40.750', title='Intervalo')).status_code, 302)
        self.assertEqual(self.client.post(self.create_url, self.data(start_ms='00:10.125', title='Ponto')).status_code, 302)
        self.assertEqual(self.client.post(self.create_url, self.data(start_ms='00:30', end_ms='00:50', title='Sobreposto')).status_code, 302)
        markings = list(self.video.markings.all())
        self.assertEqual([m.title for m in markings], ['Ponto', 'Intervalo', 'Sobreposto'])
        self.assertEqual(markings[0].start_ms, 10125)
        self.assertIsNone(markings[0].end_ms)
        self.assertEqual(markings[1].end_ms, 40750)
        self.assertEqual(markings[0].created_by, self.user)
        self.assertEqual(list(markings[0].tags.all()), [self.tag])
        self.assertEqual(list(markings[0].people.all()), [self.person])
        self.assertFalse(self.video.tags.exists())
        self.assertFalse(self.video.people.exists())
        response = self.client.get(reverse('studio:chapters', args=[self.video.pk]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, '00:00:10.125')
        self.assertLess(response.content.index(b'<h3>Ponto</h3>'), response.content.index(b'<h3>Intervalo</h3>'))

    def test_invalid_times_title_and_relations_do_not_create_partial_data(self):
        for changes in [dict(title=' '), dict(start_ms='-00:01'), dict(start_ms='00:60'), dict(start_ms='text'), dict(start_ms='00:10', end_ms='00:09'), dict(start_ms='02:00.001'), dict(end_ms='02:00.001'), dict(tags=[999]), dict(people=[999])]:
            with self.subTest(data=changes):
                response = self.client.post(self.create_url, self.data(**changes))
                self.assertEqual(response.status_code, 400)
                self.assertContains(response, 'Trecho importante' if 'title' not in changes else 'Não foi possível salvar', status_code=400)
        self.assertFalse(MarcacaoTemporal.objects.exists())
        self.assertEqual(Tag.objects.count(), 1)
        self.assertEqual(Pessoa.objects.count(), 1)

    def test_duration_unknown_and_boundary_are_valid(self):
        marking = self.create(start_ms='02:00', end_ms='02:00')
        self.assertEqual(marking.end_ms, self.video.duration_ms)
        self.video.duration_ms = None
        self.video.save()
        marking = self.create(start_ms='100:00:00.123')
        self.assertEqual(marking.start_ms, 360000123)

    def test_edit_preserves_creator_and_removes_only_associations(self):
        marking = self.create()
        self.client.force_login(self.other_user)
        response = self.client.post(reverse('studio:update_marking', args=[self.video.pk, marking.pk]), self.data(title='Título editado', start_ms='00:11.001', tags=[], people=[]))
        self.assertEqual(response.status_code, 302)
        marking.refresh_from_db()
        self.video.refresh_from_db()
        self.assertEqual(marking.created_by, self.user)
        self.assertEqual(marking.updated_by, self.other_user)
        self.assertEqual(self.video.updated_by, self.other_user)
        self.assertEqual(marking.start_ms, 11001)
        self.assertFalse(marking.tags.exists())
        self.assertTrue(Tag.objects.exists())
        self.assertTrue(Pessoa.objects.exists())

    def test_invalid_edit_keeps_persisted_values_and_submitted_input(self):
        marking = self.create()
        response = self.client.post(reverse('studio:update_marking', args=[self.video.pk, marking.pk]), self.data(title='Título digitado', start_ms='03:00'))
        self.assertEqual(response.status_code, 400)
        self.assertContains(response, 'Título digitado', status_code=400)
        marking.refresh_from_db()
        self.assertEqual(marking.title, 'Trecho importante')
        self.assertEqual(marking.start_ms, 10125)

    def test_removal_does_not_delete_video_global_records_or_file(self):
        media = Path(self.folder.name) / 'missing.mp4'
        media.write_bytes(b'fixture')
        marking = self.create()
        url = reverse('studio:confirm_delete_marking', args=[self.video.pk, marking.pk])
        self.assertContains(self.client.get(url), 'Remover marcação')
        self.assertTrue(MarcacaoTemporal.objects.exists())
        response = self.client.post(reverse('studio:remove_marking', args=[self.video.pk, marking.pk]))
        self.assertEqual(response.status_code, 302)
        self.assertFalse(MarcacaoTemporal.objects.exists())
        self.assertTrue(Video.objects.exists())
        self.assertTrue(Tag.objects.exists())
        self.assertTrue(Pessoa.objects.exists())
        self.assertTrue(media.exists())

    def test_parent_video_is_checked_for_all_operations(self):
        marking = self.create()
        other = Video.objects.create(title='Outro', local_midia=self.local, relative_path='other.mp4')
        for name in ['edit_marking', 'confirm_delete_marking']:
            self.assertEqual(self.client.get(reverse(f'studio:{name}', args=[other.pk, marking.pk])).status_code, 404)
        for name in ['update_marking', 'remove_marking']:
            self.assertEqual(self.client.post(reverse(f'studio:{name}', args=[other.pk, marking.pk]), self.data()).status_code, 404)
        self.assertTrue(MarcacaoTemporal.objects.exists())

    def test_anonymous_and_get_mutations_are_blocked(self):
        marking = self.create()
        urls = [self.create_url, reverse('studio:update_marking', args=[self.video.pk, marking.pk]), reverse('studio:remove_marking', args=[self.video.pk, marking.pk])]
        for url in urls:
            self.assertEqual(self.client.get(url).status_code, 405)
        self.client.logout()
        for url in urls:
            self.assertEqual(self.client.post(url, self.data()).status_code, 302)
        self.assertEqual(self.client.get(reverse('studio:chapters', args=[self.video.pk])).status_code, 302)
        self.assertEqual(MarcacaoTemporal.objects.count(), 1)

    def test_post_requires_csrf(self):
        client = Client(enforce_csrf_checks=True)
        client.force_login(self.user)
        self.assertEqual(client.post(self.create_url, self.data()).status_code, 403)
        client.get(reverse('studio:chapters', args=[self.video.pk]))
        response = client.post(self.create_url, self.data(), HTTP_X_CSRFTOKEN=client.cookies['csrftoken'].value)
        self.assertEqual(response.status_code, 302)

    def test_database_blocks_inverted_interval_and_negative_time(self):
        for values in [dict(start_ms=20, end_ms=10), dict(start_ms=-1, end_ms=None)]:
            with self.subTest(values=values), self.assertRaises(IntegrityError), transaction.atomic():
                MarcacaoTemporal.objects.bulk_create([MarcacaoTemporal(video=self.video, title='Inválida', **values)])

    def test_transaction_rolls_back_on_relationship_failure(self):
        form = MarkingForm(self.data(), video=self.video)
        self.assertTrue(form.is_valid(), form.errors)
        with patch.object(form, 'save_m2m', side_effect=IntegrityError('fixture'), create=True):
            # ModelForm.save(commit=False) installs save_m2m; patch _save_m2m instead.
            with patch.object(form, '_save_m2m', side_effect=IntegrityError('fixture')):
                with self.assertRaises(IntegrityError):
                    save_marking(form, self.user)
        self.assertFalse(MarcacaoTemporal.objects.exists())

    def test_service_rechecks_duration_after_form_validation(self):
        form = MarkingForm(self.data(start_ms='01:00'), video=self.video)
        self.assertTrue(form.is_valid(), form.errors)
        Video.objects.filter(pk=self.video.pk).update(duration_ms=10000)
        with self.assertRaises(ValidationError):
            save_marking(form, self.user)
        self.assertFalse(MarcacaoTemporal.objects.exists())

    def test_reducing_duration_rejects_existing_out_of_bounds_marking(self):
        self.create(start_ms='01:00', end_ms='01:30')
        form = VideoForm({'title': self.video.title, 'local_midia': self.local.pk, 'relative_path': self.video.relative_path, 'duration_ms': 20000}, instance=self.video)
        self.assertFalse(form.is_valid())
        self.assertIn('duration_ms', form.errors)
        self.video.refresh_from_db()
        self.assertEqual(self.video.duration_ms, 120000)

    def test_missing_file_and_inactive_local_do_not_block_marking_metadata(self):
        self.local.active = False
        self.local.save()
        self.create()
        response = self.client.get(reverse('studio:chapters', args=[self.video.pk]))
        self.assertContains(response, 'Trecho importante')
        self.assertContains(response, 'Arquivo indisponível')

    def test_inspected_shorter_replacement_does_not_change_video_reference(self):
        self.create(start_ms='01:00')
        form = VideoForm({'title': self.video.title, 'local_midia': self.local.pk, 'relative_path': 'replacement.mp4', 'duration_ms': 120000}, instance=self.video)
        self.assertTrue(form.is_valid(), form.errors)

        def shorter(video, path):
            video.duration_ms = 20000
            video.duration_source = 'extracted'

        with patch('app.catalog.services.inspect_video', side_effect=shorter), self.assertRaises(ValidationError):
            save_video(form, self.user)
        self.video.refresh_from_db()
        self.assertEqual(self.video.relative_path, 'missing.mp4')
        self.assertEqual(self.video.duration_ms, 120000)

    def test_reinspection_preserves_duration_when_markings_would_be_invalid(self):
        self.create(start_ms='01:00')

        def shorter(video, path):
            video.duration_ms = 20000
            video.duration_source = 'extracted'

        with patch('app.catalog.views.inspect_video', side_effect=shorter):
            response = self.client.post(reverse('studio:reinspect', args=[self.video.pk]), follow=True)
        self.assertContains(response, 'Não foi possível aplicar a inspeção')
        self.video.refresh_from_db()
        self.assertEqual(self.video.duration_ms, 120000)

    @override_settings(UI_DEMO=True)
    def test_demo_cannot_mutate_real_markings(self):
        self.assertEqual(self.client.post(self.create_url, self.data()).status_code, 403)
        self.assertFalse(MarcacaoTemporal.objects.exists())

    def test_timecodes_preserve_milliseconds_and_reject_overflow(self):
        for raw, expected in [('00:00', 0), ('01:02.001', 62001), ('01:02:03,12', 3723120), ('100:00:00.999', 360000999)]:
            with self.subTest(raw=raw):
                self.assertEqual(parse_timecode(raw), expected)
                self.assertEqual(parse_timecode(format_timecode(expected)), expected)
        for raw in ['1', '-01:00', '00:61', '01:60:00', '00:00.1234', '9' * 30 + ':00']:
            with self.subTest(raw=raw), self.assertRaises(ValidationError):
                parse_timecode(raw)
