from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from django.urls import reverse

@override_settings(UI_DEMO=True)
class StudioPreviewTests(TestCase):
    def test_all_screens_render(self):
        for url in ['/', '/videos/1/', '/videos/1/capitulos/', '/perfil/', '/componentes/', '/conta/entrar/']:
            with self.subTest(url=url):
                response = self.client.get(url)
                self.assertEqual(response.status_code, 200)
                self.assertContains(response, 'lang="pt-BR"')

    def test_combined_catalog_filters(self):
        response = self.client.get('/', {'q': 'entrevista', 'tag': 'UX', 'person': 'Beatriz Santos'})
        self.assertEqual([v['id'] for v in response.context['videos']], [3])

    def test_empty_catalog(self):
        response = self.client.get('/', {'q': 'termo-inexistente'})
        self.assertContains(response, 'Nenhum arquivo encontrado')
        self.assertEqual(response.context['videos'], [])

    def test_htmx_returns_only_catalog_partial(self):
        response = self.client.get('/', {'category': 'Cortes & Shorts'}, HTTP_HX_REQUEST='true')
        self.assertEqual([v['id'] for v in response.context['videos']], [2, 7])
        self.assertContains(response, 'id="library-results"')
        self.assertNotContains(response, '<html')

    def test_each_demo_asset_has_an_editor(self):
        for video_id in range(1, 9):
            with self.subTest(video_id=video_id):
                self.assertEqual(self.client.get(f'/videos/{video_id}/').status_code, 200)

    def test_unknown_video_is_not_found(self):
        self.assertEqual(self.client.get('/videos/999/').status_code, 404)

    def test_preview_does_not_accept_mutations(self):
        self.assertEqual(self.client.post('/videos/1/', {'title': 'changed'}).status_code, 405)

    @override_settings(UI_DEMO=False)
    def test_real_access_requires_authentication(self):
        self.assertRedirects(self.client.get('/'), '/conta/entrar/?next=/', fetch_redirect_response=False)
        user = get_user_model().objects.create_user('editor@example.com', 'temporary-test-password')
        self.client.force_login(user)
        self.assertEqual(self.client.get('/').status_code, 200)

    @override_settings(UI_DEMO=False)
    def test_email_login_and_post_logout(self):
        get_user_model().objects.create_user('editor@example.com', 'temporary-test-password')
        response = self.client.post(reverse('accounts:login'), {'username': 'editor@example.com', 'password': 'temporary-test-password'})
        self.assertRedirects(response, '/')
        self.assertEqual(self.client.get(reverse('accounts:logout')).status_code, 405)
        self.assertRedirects(self.client.post(reverse('accounts:logout')), reverse('accounts:login'))
