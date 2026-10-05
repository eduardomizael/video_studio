from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from .forms import VideoForm
from .models import LocalMidia, Pessoa, Tag, Video
from .paths import resolve_media_path
from .services import save_video


@override_settings(UI_DEMO=False)
class CatalogTests(TestCase):
    def setUp(self):
        self.folder = TemporaryDirectory(dir=settings.BASE_DIR)
        self.addCleanup(self.folder.cleanup)
        self.root = Path(self.folder.name)
        (self.root / 'episode.mp4').write_bytes(b'fixture: metadata test, not a playable video')
        self.local = LocalMidia.objects.create(name='Acervo de teste', root_path=str(self.root))
        self.user = get_user_model().objects.create_user('editor@example.com', 'test-password', first_name='Ana')
        self.client.force_login(self.user)

    def data(self, **changes):
        return {'title': 'Entrevista local', 'description': 'Tecnologia e design', 'local_midia': self.local.pk, 'relative_path': 'episode.mp4', **changes}

    def create(self, **changes):
        form = VideoForm(self.data(**changes))
        self.assertTrue(form.is_valid(), form.errors)
        return save_video(form, self.user)

    def test_create_edit_reload_search_and_combined_filters(self):
        person = Pessoa.objects.create(name='Participante')
        response = self.client.post(reverse('studio:create_video'), self.data(new_tags=' Design, design , CIÊNCIA ', people=[person.pk], new_person_name='Ana', new_person_notes='Entrevistadora'))
        video = Video.objects.get()
        self.assertRedirects(response, reverse('studio:editor', args=[video.pk]))
        self.assertEqual(video.tags.count(), 2)
        self.assertEqual(video.people.count(), 2)
        self.assertEqual(video.file_status, Video.FileStatus.AVAILABLE)
        self.assertEqual(video.created_by, self.user)
        self.assertEqual(video.updated_by, self.user)
        self.assertIsNone(video.duration_ms)
        design = Tag.objects.get(normalized_name='design')
        other = Tag.objects.create(name='Outra')
        response = self.client.get('/', {'q': 'tecnologia', 'tag': [design.pk, other.pk], 'person': [person.pk]})
        self.assertEqual([item['id'] for item in response.context['videos']], [video.pk])
        editor = self.client.get(reverse('studio:editor', args=[video.pk]))
        self.assertContains(editor, 'Entrevista local')
        self.assertContains(editor, 'Tecnologia e design')
        self.assertContains(editor, 'Ana')
        self.assertNotContains(editor, 'Lucas Mendes')
        response = self.client.post(reverse('studio:update_video', args=[video.pk]), self.data(title='Título atualizado', description='Descrição persistida', tags=[design.pk], people=[person.pk]))
        self.assertEqual(response.status_code, 302)
        video.refresh_from_db()
        self.assertEqual(video.title, 'Título atualizado')
        self.assertEqual(video.description, 'Descrição persistida')
        self.assertEqual(list(video.tags.all()), [design])
        self.assertEqual(list(video.people.all()), [person])
        self.assertEqual(Tag.objects.count(), 3)  # Removed associations preserve global records.
        self.assertEqual(Pessoa.objects.count(), 2)
        self.assertContains(self.client.get(reverse('studio:editor', args=[video.pk])), 'Descrição persistida')

    def test_invalid_edit_preserves_data_and_input(self):
        video = self.create(new_tags='Design')
        response = self.client.post(reverse('studio:update_video', args=[video.pk]), self.data(title='Meu título digitado', relative_path='../outside.mp4', new_tags='Não deve existir'))
        self.assertEqual(response.status_code, 400)
        self.assertContains(response, 'Meu título digitado', status_code=400)
        video.refresh_from_db()
        self.assertEqual(video.title, 'Entrevista local')
        self.assertEqual(Tag.objects.count(), 1)

    def test_duplicate_normalized_path_is_rejected(self):
        self.create()
        response = self.client.post(reverse('studio:create_video'), self.data(relative_path='./episode.mp4'))
        self.assertEqual(response.status_code, 400)
        self.assertEqual(Video.objects.count(), 1)
        self.assertContains(response, 'Já existe um vídeo', status_code=400)

    def test_database_rejects_duplicate_reference(self):
        video = self.create()
        with self.assertRaises(IntegrityError), transaction.atomic():
            Video.objects.bulk_create([Video(title='Outra', local_midia=self.local, relative_path=video.relative_path, path_key=video.path_key)])

    def test_inactive_location_is_rejected(self):
        self.local.active = False
        self.local.save()
        response = self.client.post(reverse('studio:create_video'), self.data())
        self.assertEqual(response.status_code, 400)
        self.assertFalse(Video.objects.exists())

    def test_invalid_tag_selection_does_not_partially_create_records(self):
        response = self.client.post(reverse('studio:create_video'), self.data(tags=[999], new_tags='Nova', new_person_name='Nova pessoa'))
        self.assertEqual(response.status_code, 400)
        self.assertFalse(Video.objects.exists())
        self.assertFalse(Tag.objects.exists())
        self.assertFalse(Pessoa.objects.exists())

    def test_service_rolls_back_video_and_tags_if_person_creation_fails(self):
        form = VideoForm(self.data(new_tags='Nova', new_person_name='Pessoa'))
        self.assertTrue(form.is_valid(), form.errors)
        with patch('app.catalog.services.Pessoa.objects.create', side_effect=IntegrityError('fixture')):
            with self.assertRaises(IntegrityError):
                save_video(form, self.user)
        self.assertFalse(Video.objects.exists())
        self.assertFalse(Tag.objects.exists())

    def test_missing_file_is_catalogable_and_metadata_survives_disappearance(self):
        video = self.create(new_tags='Arquivo')
        (self.root / 'episode.mp4').unlink()
        form = VideoForm(self.data(tags=list(video.tags.values_list('pk', flat=True))), instance=video)
        self.assertTrue(form.is_valid(), form.errors)
        save_video(form, self.user)
        video.refresh_from_db()
        self.assertEqual(video.file_status, Video.FileStatus.MISSING)
        self.assertEqual(video.tags.count(), 1)
        self.assertContains(self.client.get(reverse('studio:editor', args=[video.pk])), 'Arquivo não encontrado')
        self.create(relative_path='missing.mp4')
        self.assertEqual(Video.objects.count(), 2)

    def test_unreadable_file_does_not_block_metadata(self):
        with patch('app.catalog.services.file_status', return_value=Video.FileStatus.UNREADABLE):
            video = self.create()
        self.assertEqual(video.file_status, Video.FileStatus.UNREADABLE)

    def test_path_escape_absolute_drive_and_directory_are_rejected(self):
        for value in ['../outside.mp4', '/outside.mp4', 'C:\\outside.mp4', 'C:outside.mp4', '\\\\server\\share\\video.mp4', '.', 'episode.mp4:stream', '']:
            with self.subTest(path=value), self.assertRaises(ValidationError):
                resolve_media_path(self.local, value)

    def test_symlink_escape_is_rejected(self):
        with TemporaryDirectory(dir=settings.BASE_DIR) as outside:
            target = Path(outside) / 'secret.mp4'
            target.write_bytes(b'private')
            link = self.root / 'link.mp4'
            try:
                link.symlink_to(target)
            except OSError:
                self.skipTest('O ambiente não permite criar links simbólicos.')
            with self.assertRaises(ValidationError):
                resolve_media_path(self.local, 'link.mp4')

    def test_backslash_path_is_normalized(self):
        target, relative, _ = resolve_media_path(self.local, 'interviews\\new.mp4')
        self.assertEqual(relative, 'interviews/new.mp4')
        self.assertTrue(target.is_relative_to(self.root.resolve()))

    def test_tag_normalization_handles_unicode_and_spaces(self):
        self.create(new_tags=' DESIGN , design, ＤＥＳＩＧＮ, Ciência  de Dados, ciência de dados')
        self.assertEqual(Tag.objects.count(), 2)
        self.assertTrue(Tag.objects.filter(normalized_name='ciência de dados').exists())

    def test_homonymous_people_remain_distinct(self):
        original = Pessoa.objects.create(name='Ana')
        video = self.create(people=[original.pk], new_person_name='Ana')
        self.assertEqual(video.people.count(), 2)
        self.assertEqual(Pessoa.objects.count(), 2)

    def test_pagination_and_htmx_keep_filters_and_only_page_data(self):
        tag = Tag.objects.create(name='Design')
        for index in range(14):
            self.create(title=f'Vídeo {index:02}', relative_path=f'video-{index}.mp4', tags=[tag.pk])
        response = self.client.get('/', {'tag': [tag.pk], 'sort': 'title'})
        self.assertEqual(len(response.context['videos']), 12)
        self.assertEqual(len(response.context['all_videos']), 12)
        self.assertEqual(response.context['filtered_total'], 14)
        response = self.client.get('/', {'tag': [tag.pk], 'sort': 'title', 'page': 2}, HTTP_HX_REQUEST='true')
        self.assertEqual(len(response.context['videos']), 2)
        self.assertContains(response, 'id="library-results"')
        self.assertContains(response, 'hx-swap-oob="innerHTML"')
        self.assertNotContains(response, '<html')
        self.assertIn(f'tag={tag.pk}', response.context['page_query'])

    def test_invalid_filter_does_not_return_unfiltered_catalog(self):
        self.create()
        self.assertEqual(self.client.get('/', {'tag': 'invalid'}).context['filtered_total'], 0)
        self.assertEqual(self.client.get('/', {'tag': '9' * 100}).context['filtered_total'], 0)

    def test_anonymous_requests_and_non_post_mutations_are_blocked(self):
        video = self.create()
        self.assertEqual(self.client.get(reverse('studio:create_video')).status_code, 405)
        self.assertEqual(self.client.get(reverse('studio:update_video', args=[video.pk])).status_code, 405)
        self.client.logout()
        for url in ['/', reverse('studio:editor', args=[video.pk]), reverse('studio:create_video'), reverse('studio:update_video', args=[video.pk])]:
            self.assertEqual(self.client.get(url).status_code, 302)
        self.assertEqual(self.client.post(reverse('studio:create_video'), self.data()).status_code, 302)
        self.assertEqual(Video.objects.count(), 1)

    def test_mutations_require_csrf(self):
        client = Client(enforce_csrf_checks=True)
        client.force_login(self.user)
        self.assertEqual(client.post(reverse('studio:create_video'), self.data()).status_code, 403)
        client.get('/')
        token = client.cookies['csrftoken'].value
        response = client.post(reverse('studio:create_video'), self.data(), HTTP_X_CSRFTOKEN=token)
        self.assertEqual(response.status_code, 302)

    @override_settings(UI_DEMO=True)
    def test_demo_never_writes_real_catalog(self):
        self.assertEqual(self.client.post(reverse('studio:create_video'), self.data()).status_code, 403)
        self.assertFalse(Video.objects.exists())

    def test_unimplemented_screens_do_not_display_demo_data(self):
        video = self.create()
        self.assertContains(self.client.get(reverse('studio:chapters', args=[video.pk])), 'Capítulos e marcações')
        self.assertContains(self.client.get(reverse('studio:chapters', args=[video.pk])), 'Nenhuma marcação cadastrada')
        self.assertContains(self.client.get(reverse('studio:profile')), 'editor@example.com')
        self.assertNotContains(self.client.get(reverse('studio:components')), 'Lucas Mendes')

    def test_staff_admin_can_manage_locations_and_regular_user_cannot(self):
        self.assertEqual(self.client.get(reverse('admin:catalog_localmidia_changelist')).status_code, 302)
        self.user.is_staff = True
        self.user.is_superuser = True
        self.user.save()
        self.assertEqual(self.client.get(reverse('admin:catalog_localmidia_changelist')).status_code, 200)
        video = self.create()
        self.assertEqual(self.client.post(reverse('admin:catalog_video_delete', args=[video.pk]), {'post': 'yes'}).status_code, 403)
        self.assertTrue(Video.objects.filter(pk=video.pk).exists())
