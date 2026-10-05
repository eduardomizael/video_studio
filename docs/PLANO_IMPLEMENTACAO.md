# Plano de implementação — Video Studio

**Versão:** 0.1  
**Status:** pronto para execução  
**Origem:** [Requisitos](REQUISITOS.md), versão 0.2.

## 1. Objetivo e limite deste plano

Implementar o MVP para catalogar vídeos locais e editar seus metadados, marcações, pessoas, tags e legendas SRT. O sistema gerencia referências a arquivos já existentes: não faz upload, conversão, exclusão, varredura automática nem integrações em nuvem.

O plano não institui papéis detalhados, colaboração, visualização mobile, APIs públicas, auditoria histórica completa nem exclusão de registros de vídeo.

## 2. Arquitetura definida

| Camada | Decisão |
| --- | --- |
| Backend | Django, projeto e dependências Python gerenciados por UV. |
| Banco inicial | SQLite, com migrações Django desde o primeiro incremento. |
| Interface | Templates Django orientados a páginas, com HTMX para interações parciais. |
| Estilo | Tailwind CSS compilado por build Node e publicado como arquivo estático. |
| Autenticação | Modelo customizado de usuário desde a primeira migração; telas protegidas por login. |
| Administração | Django Admin para usuários e locais de mídia. |
| Arquivos | Caminhos locais sob raízes de mídia configuradas e acessíveis ao processo Django. |
| Metadados técnicos | Extração por ferramenta local de mídia, com preenchimento manual como contingência. |

### Convenções técnicas propostas

- Usar `npm` para o build Node, com scripts para desenvolvimento e produção do Tailwind.
- Organizar código por apps Django: `accounts`, `catalog` e `annotations` (ou nomenclatura equivalente, sem misturar responsabilidades).
- Representar todos os tempos persistidos como inteiros em milissegundos. A interface converte para `hh:mm:ss.mmm`; assim marcações e SRT preservam precisão sem erros de ponto flutuante.
- Usar `Path.resolve()` para resolver o caminho final e validar que ele permanece sob a raiz ativa do `LocalMidia`; não aceitar caminhos absolutos fornecidos pelo usuário.
- Expor mídia por uma view autenticada que resolve a referência do vídeo. Nunca tornar toda a árvore de arquivos local um diretório estático público.
- Implementar o player para os formatos que o navegador efetivamente suporta. Um arquivo não reproduzível continua catalogável e recebe estado claro de indisponibilidade de reprodução.

## 3. Modelo de dados e regras de integridade

| Modelo | Campos e regras principais |
| --- | --- |
| `Usuario` | Substitui o usuário padrão do Django antes da primeira migração. E-mail único, nome de exibição e campos de estado de acesso. |
| `LocalMidia` | Nome único, raiz absoluta validada no servidor, flag `ativo`. Administrado somente no Django Admin. |
| `Video` | `titulo` obrigatório, descrição opcional, `local_midia`, `caminho_relativo`, duração e miniatura opcionais, estado do arquivo, criador/atualizador e datas. A combinação local + caminho relativo é única. |
| `Tag` | Nome normalizado e único de forma case-insensitive; cor opcional. |
| `Pessoa` | Nome de exibição obrigatório e observação opcional. |
| `MarcacaoTemporal` | Vídeo, título, início obrigatório, fim opcional, criador/atualizador e datas. Permite sobreposição. |
| `VersaoLegenda` | Vídeo, nome obrigatório, idioma opcional, origem (`importada`/`manual`), `ativa` e datas. Há no máximo uma ativa por vídeo. |
| `EntradaLegenda` | Versão, início, fim, texto e ordem. |

As relações muitos-para-muitos de tags e pessoas devem existir tanto no vídeo quanto na marcação. Validações de modelo/formulário devem bloquear tempo negativo, intervalo invertido e tempo além da duração conhecida. A seleção de versão ativa e a importação SRT devem ser transacionais.

## 4. Fases de execução

### Fase 1 — Fundação do projeto

1. Criar o projeto Django com UV, arquivos de ambiente documentados e configurações separadas para desenvolvimento.
2. Criar o modelo customizado `Usuario`, configurar `AUTH_USER_MODEL` antes de qualquer migração e habilitar login/logout.
3. Configurar SQLite, timezone, idioma `pt-br`, arquivos estáticos e diretórios de templates.
4. Inicializar Node, Tailwind e scripts de build/watch; integrar o CSS compilado aos templates-base.
5. Criar layout-base autenticado: navegação lateral, barra superior e área de conteúdo, inspirado no modo escuro dos protótipos Stitch.

**Validação:** criar superusuário, aplicar migrações, autenticar-se e confirmar que CSS Tailwind é servido no layout protegido.

### Fase 2 — Domínio e administração

1. Implementar os modelos e migrações da seção 3.
2. Registrar `Usuario` e `LocalMidia` no Django Admin; restringir a administração a superusuários/staff.
3. Registrar os demais modelos no Admin como ferramenta de diagnóstico, sem substituir as telas de trabalho.
4. Implementar normalização de tags, restrições de unicidade e validações de caminhos/tempos.
5. Criar serviços de domínio para resolver arquivo, verificar existência e atualizar o estado do vídeo.

**Validação:** testes de migração, unicidade de tag/caminho, bloqueio de traversal, marcações inválidas e regra de uma legenda ativa.

### Fase 3 — Registro de vídeo e metadados técnicos

1. Criar formulário de vídeo que aceite título, descrição, local de mídia e caminho relativo.
2. Implementar serviço de inspeção do arquivo: verificar existência, obter duração e gerar ou localizar miniatura quando a ferramenta local estiver disponível.
3. Permitir correção manual de duração e miniatura caso a inspeção falhe; mostrar a origem/estado da informação.
4. Criar endpoint autenticado de mídia com autorização, resolução segura do caminho e suporte à reprodução/seek compatível com o servidor de implantação.
5. Exibir estado `arquivo não encontrado` sem perder as associações e metadados já cadastrados.

**Validação:** registrar vídeo válido, vídeo ausente e arquivo com extração falha; conferir que nenhum caminho fora de um local configurado é servido.

### Fase 4 — Biblioteca de mídia

1. Criar a página de catálogo paginado, com miniatura/indicador, título, duração, tags e data de atualização.
2. Implementar busca por título/descrição e filtros combináveis de tags e pessoas.
3. Usar HTMX para atualizar resultados e filtros sem recarregar toda a página, mantendo URL e estado de filtros quando aplicável.
4. Criar estados vazios, carregamento e mensagens de validação em português.

**Validação:** usar conjunto de dados de teste com vários vídeos/tags/pessoas e confirmar paginação, busca, filtros combinados e acesso somente autenticado.

### Fase 5 — Editor do vídeo e anotações

1. Criar tela de detalhe com player/indicador de mídia, formulário de metadados, tags, pessoas e painel de marcações.
2. Implementar componentes HTMX para busca, seleção múltipla, criação de tag/pessoa e remoção somente da associação.
3. Criar formulário de marcação pontual ou por intervalo, com título obrigatório e associação opcional de tags/pessoas.
4. Integrar posição atual do player para iniciar uma marcação; listar marcações cronologicamente e permitir edição/exclusão.
5. Desenhar pontos/intervalos na linha do tempo e posicionar o player ao selecionar uma marcação.

**Validação:** validar todo o fluxo dos critérios 1 a 5 de aceite, incluindo marcações sobrepostas e estados sem player.

### Fase 6 — Legendas SRT

1. Implementar parser SRT tolerante a numeração, quebras de linha e codificação UTF-8; retornar erros com linha/contexto compreensível.
2. Criar fluxo de importação como versão de legenda, com nome obrigatório e idioma opcional.
3. Criar tela de edição de versão e entradas: texto, início, fim e ordenação cronológica.
4. Implementar seleção transacional da versão ativa por vídeo.
5. Sincronizar a faixa ativa com o player e apresentar o texto no instante correspondente.

**Validação:** importar SRT válido, rejeitar tempo inválido, editar entrada, alternar entre versões e confirmar que apenas a versão ativa aparece no player.

### Fase 7 — Qualidade e entrega do MVP

1. Consolidar testes unitários de modelos, serviços de caminho, parser SRT e formulários.
2. Criar testes de integração para login, catálogo, filtros, HTMX, edição de vídeo, marcações e legendas.
3. Fazer revisão de autorização, mensagens de erro e prevenção de exposição de caminhos locais.
4. Verificar acessibilidade por teclado, rótulos de formulário, foco e contraste do tema escuro.
5. Executar validação manual em navegador desktop com vídeos reais e registrar limitações de codec/extração observadas.

**Validação final:** todos os critérios da seção 9 de `REQUISITOS.md` aprovados, suíte automatizada verde e lista explícita de validações dependentes do ambiente.

## 5. Dependências e riscos conhecidos

| Item | Risco | Mitigação no MVP |
| --- | --- | --- |
| FFmpeg/FFprobe | Pode não estar instalado ou não ler determinado codec. | Detectar disponibilidade; não bloquear cadastro; permitir valores manuais. |
| Codec do navegador | Nem todo arquivo local é reproduzível no browser. | Catalogar mesmo sem player e informar o estado. |
| Acesso a arquivo local | O processo Django pode não ter permissão de leitura. | Validar na criação e atualizar para `arquivo não encontrado` quando indisponível. |
| SQLite | Menos adequado a alta concorrência. | Adequado ao MVP; manter modelos/migrações portáveis para futura migração. |
| Caminhos locais | Podem expor arquivos fora do catálogo. | Aceitar somente caminhos relativos sob raízes ativas e servir por endpoint autenticado. |

## 6. Fora do plano atual

- Definição de grupos e papéis detalhados.
- Conectores de nuvem, URLs externas e descoberta automática.
- Upload, exclusão, conversão e edição de mídia.
- APIs externas, exportação de SRT e histórico completo de alterações.
- Layout e comportamento mobile.

## 7. Ordem recomendada de execução

Executar as fases 1 a 3 antes de qualquer tela de catálogo. Depois, concluir fases 4 e 5 para entregar o primeiro fluxo utilizável de gestão de vídeo. A fase 6 complementa esse fluxo com legendas. A fase 7 é obrigatória antes de considerar o MVP validado.
