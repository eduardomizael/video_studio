"""Presentation data only. Replace this boundary with catalog queries later."""
VIDEOS = [
    {'id': 1, 'title': 'MASTER_PODCAST_FINAL_4K.mp4', 'description': 'O futuro do design com IA em 2025 | Masterclass completa', 'duration': '42:15', 'duration_seconds': 2535, 'kind': 'video', 'category': 'Vídeos Master', 'status': 'Pronto', 'tone': 'green', 'resolution': '4K HDR', 'size': '18,4 GB', 'codec': 'H.265', 'tags': ['Inteligência Artificial', 'Podcast', 'Design'], 'people': ['Lucas Mendes', 'Beatriz Santos'], 'thumb': 'podcast', 'updated': 'Hoje às 14:20'},
    {'id': 2, 'title': 'CORTE_01_IA_MERCADO.mp4', 'description': 'Como a inteligência artificial está mudando o mercado criativo', 'duration': '00:58', 'duration_seconds': 58, 'kind': 'video', 'category': 'Cortes & Shorts', 'status': 'Pronto', 'tone': 'green', 'resolution': '1080p', 'size': '148 MB', 'codec': 'H.264', 'tags': ['Shorts', 'IA', 'Podcast'], 'people': ['Lucas Mendes'], 'thumb': 'short', 'updated': 'Hoje às 13:58'},
    {'id': 3, 'title': 'ENTREVISTA_BEATRIZ.mov', 'description': 'Entrevista sobre experiência do usuário e ferramentas de design', 'duration': '01:14:30', 'duration_seconds': 4470, 'kind': 'video', 'category': 'Vídeos Master', 'status': 'Arquivo bruto', 'tone': 'muted', 'resolution': '4K', 'size': '54,2 GB', 'codec': 'ProRes', 'tags': ['Entrevista', 'UX', 'Design'], 'people': ['Beatriz Santos'], 'thumb': 'interview', 'updated': 'Ontem às 18:10'},
    {'id': 4, 'title': 'AUDIO_PODCAST_EP08.wav', 'description': 'Faixa de áudio principal do episódio oito', 'duration': '42:15', 'duration_seconds': 2535, 'kind': 'audio', 'category': 'Faixas de Áudio & Pods', 'status': 'Pronto', 'tone': 'green', 'resolution': 'WAV 24-bit', 'size': '820 MB', 'codec': 'PCM', 'tags': ['Podcast', 'Áudio'], 'people': ['Lucas Mendes'], 'thumb': 'audio', 'updated': 'Ontem às 16:35'},
    {'id': 5, 'title': 'THUMBNAIL_TESTE_IA.png', 'description': 'Capa do episódio: o futuro é agora', 'duration': 'Imagem', 'duration_seconds': 0, 'kind': 'image', 'category': 'Miniaturas & Imagens', 'status': 'Pronto', 'tone': 'green', 'resolution': '3840 × 2160', 'size': '8,2 MB', 'codec': 'PNG', 'tags': ['Design', 'Capa'], 'people': [], 'thumb': 'thumbnail', 'updated': 'Ontem às 15:12'},
    {'id': 6, 'title': 'BROLL_TECLADO_MECANICO.mp4', 'description': 'Detalhes de teclado e estação de edição', 'duration': '03:15', 'duration_seconds': 195, 'kind': 'video', 'category': 'B-roll', 'status': 'Biblioteca', 'tone': 'muted', 'resolution': '4K 120fps', 'size': '1,2 GB', 'codec': 'H.264', 'tags': ['B-roll', 'Tecnologia'], 'people': [], 'thumb': 'keyboard', 'updated': '02 out. às 11:20'},
    {'id': 7, 'title': 'CORTE_02_AGENTES_IA.mp4', 'description': 'Agentes de IA e o trabalho criativo', 'duration': '00:45', 'duration_seconds': 45, 'kind': 'video', 'category': 'Cortes & Shorts', 'status': 'Arquivo não encontrado', 'tone': 'red', 'resolution': '1080p', 'size': '115 MB', 'codec': 'H.264', 'tags': ['IA', 'Shorts'], 'people': ['Lucas Mendes'], 'thumb': 'agents', 'updated': '01 out. às 09:42'},
    {'id': 8, 'title': 'VINHETA_STUDIO_INTRO.mov', 'description': 'Animação de abertura do Studio', 'duration': '00:10', 'duration_seconds': 10, 'kind': 'video', 'category': 'B-roll', 'status': 'Biblioteca', 'tone': 'muted', 'resolution': '1080p Alpha', 'size': '85 MB', 'codec': 'ProRes', 'tags': ['Vinheta', 'Motion'], 'people': [], 'thumb': 'intro', 'updated': '30 set. às 17:25'},
]
CHAPTERS = [
    {'time': '00:00', 'seconds': 0, 'title': 'Introdução & Abertura', 'length': '02:30'},
    {'time': '02:30', 'seconds': 150, 'title': 'O que são Agentes Autônomos', 'length': '06:15'},
    {'time': '08:45', 'seconds': 525, 'title': 'Modelos de Raciocínio & Ferramentas', 'length': '05:43'},
    {'time': '14:28', 'seconds': 868, 'title': 'Arquitetura de Pipelines e UX', 'length': '07:42'},
    {'time': '22:10', 'seconds': 1330, 'title': 'O Futuro dos Desenvolvedores em 2025', 'length': '12:15'},
    {'time': '34:25', 'seconds': 2065, 'title': 'Perguntas da Comunidade & Encerramento', 'length': '07:50'},
]
SUBTITLES = [
    {'start': '00:00:12.000', 'end': '00:00:18.000', 'text': 'Sejam muito bem-vindos ao Studio Podcast, hoje com uma conversa sobre design e inteligência artificial.', 'speaker': 'Lucas Mendes'},
    {'start': '00:00:18.000', 'end': '00:00:22.800', 'text': 'Obrigada pelo convite! Vamos falar sobre como a IA está transformando a experiência das pessoas.', 'speaker': 'Beatriz Santos'},
    {'start': '00:14:25.180', 'end': '00:14:32.450', 'text': 'O impacto direto dos agentes autônomos no desenvolvimento de software moderno.', 'speaker': 'Lucas Mendes'},
    {'start': '00:14:33.000', 'end': '00:14:38.640', 'text': 'Exatamente. Quando olhamos para a autonomia e a experiência de uso, o contexto faz toda a diferença.', 'speaker': 'Beatriz Santos'},
]
NOTIFICATIONS = [
    {'title': 'Metadados revisados', 'text': 'O episódio MASTER_PODCAST_FINAL_4K está pronto para sua revisão.', 'time': 'Há 5 min', 'icon': 'check_circle', 'tone': 'green', 'group': 'videos'},
    {'title': 'Marcação de pessoa', 'text': 'Beatriz Santos foi associada ao trecho “Arquitetura de Pipelines e UX”.', 'time': 'Há 12 min', 'icon': 'person', 'tone': 'purple', 'group': 'people'},
    {'title': 'Legenda de demonstração disponível', 'text': 'A versão Português (Brasil) pode ser visualizada no editor de legendas.', 'time': 'Há 1 h', 'icon': 'subtitles', 'tone': 'purple', 'group': 'system'},
    {'title': 'Arquivo não encontrado', 'text': 'Confira a referência local de CORTE_02_AGENTES_IA.mp4.', 'time': 'Há 2 h', 'icon': 'warning', 'tone': 'red', 'group': 'videos'},
]
