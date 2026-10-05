# Levantamento do backend a partir das telas

Data: 04/10/2026. Este documento é um levantamento para implementação, não um registro de funcionalidades concluídas.

Base: as cinco telas reconstruídas do Stitch, seus componentes e comportamentos atuais, `REQUISITOS.md` versão 0.2 e `PLANO_IMPLEMENTACAO.md` versão 0.1. Os requisitos continuam sendo a referência de escopo: um controle presente no protótipo não aprova automaticamente uma nova funcionalidade.

## 1. Estado atual verificado

| Área | Existe hoje | Falta implementar |
| --- | --- | --- |
| Fundação Django | Configurações, SQLite, templates, estáticos, HTMX e build CSS | Configuração e validação do ambiente de execução dos arquivos reais |
| Contas | `User` customizado por e-mail, migração, Admin, login e logout | Usar a identidade autenticada no cabeçalho e telas; aplicar acesso obrigatório ao catálogo real |
| Biblioteca e editor | Views GET, dados em `app/studio/demo.py`, filtros demonstrativos | Modelos do domínio, consultas ao banco, formulários e operações de gravação |
| Player | Imagem e relógio simulados em JavaScript | Referência ao arquivo real, acesso autenticado e reprodução no navegador |
| Marcações e legendas | Manipulação temporária de elementos no navegador | Persistência, validação no servidor, importação SRT e sincronização real |
| Perfil e notificações | Identidade, preferências e notificações de exemplo | Backend específico, se essas extensões forem incluídas |

Desativar `UI_DEMO` exige login, mas não transforma os exemplos em registros reais. As views atuais do Studio aceitam somente GET. Não existe ainda backend de cadastro, salvamento, importação ou exclusão de anotações.

## 2. Biblioteca de mídia

Referências: `templates/studio/library.html`, cards, inspetor e modal de cadastro.

| Elemento/ação | Backend necessário | Entrega |
| --- | --- | --- |
| Cards e lista | Consultar vídeos, duração, miniatura, tags, estado e atualização; paginação com ordenação estável | MVP |
| Busca | Buscar título e descrição; manter parâmetros na URL e paginação | MVP |
| Filtros de tags e pessoas | Aceitar múltiplos IDs, combinar filtros e evitar vídeos duplicados nas relações M2M | MVP |
| Ordenação | Permitir somente critérios conhecidos; tratar duração desconhecida e desempatar por ID | MVP |
| Contadores | Calcular quantidade total e quantidade filtrada usando a mesma consulta da listagem | MVP |
| Selecionar item / inspetor | Carregar o registro escolhido e seus metadados reais, sem serializar o catálogo inteiro na página | MVP |
| Cadastrar vídeo | Validar título, local ativo e caminho relativo; impedir referência duplicada; registrar autor e tentar extrair duração/miniatura | MVP |
| Abrir editor | Consultar o vídeo pelo ID e retornar 404 se o registro não existir | MVP |
| Estado de arquivo ausente | Verificar a referência local e preservar os metadados quando o arquivo desaparecer | MVP |
| Tags em lote | Receber IDs selecionados e operação explícita de adicionar/remover associações; validar todos os itens e gravar em transação | Extensão visível na tela |
| Categorias laterais | Definir classificação editorial/de uso antes de persistir e filtrar | Extensão visível na tela |
| Catálogo de áudio e imagens | Definir se o produto passará a catalogar outros tipos de mídia, além de vídeos | Ampliação do domínio |

Proposta para filtros: valores dentro de cada grupo operam como OR; texto, tags e pessoas combinam entre si por AND. Exemplo: `(tag A ou B) e (pessoa X ou Y) e texto`. A regra deve ser documentada na interface e testada; “conter todas as tags” pode ser uma opção posterior. O MVP exige busca por associações do vídeo; incluir também tags/pessoas de marcações na busca precisa de uma regra explícita para o usuário.

Grade/lista, menus abertos e seleção temporária são estado de interface. Não precisam de um modelo no banco. A persistência de uma visualização preferida pode entrar junto às preferências pessoais.

## 3. Editor de vídeo e metadados

Referências: `templates/studio/editor.html`, `video_toolbar.html`, `player.html`, `tag_editor.html` e modais.

| Elemento/ação | Backend necessário | Entrega |
| --- | --- | --- |
| Título e descrição | Formulário Django, validação e salvamento; título editorial separado do nome do arquivo | MVP |
| Local e caminho | Selecionar `LocalMidia` existente; validar o caminho resolvido e sua unicidade; reinspecionar quando a referência mudar | MVP |
| Tags | Buscar existentes, criar termo normalizado, associar/remover sem apagar a tag global | MVP |
| Pessoas/coautoria | Buscar e cadastrar pessoa; associar/remover sem apagar a pessoa global | MVP |
| Pessoa no frame/trecho | Criar marcação com pessoa associada e instante/intervalo real; não confundir com participação no vídeo inteiro | MVP |
| Dados técnicos | Obter duração e miniatura; permitir correção manual quando necessário | MVP |
| Codec, resolução e tamanho | Extrair do arquivo, guardar valores opcionais e informar quando desconhecidos | Complemento para o inspetor visual |
| Categoria e idioma do áudio | Definir opções, validações e campos opcionais no vídeo | Extensão visível na tela |
| Escolher miniatura entre frames | Gerar candidatos em posições válidas, guardar o escolhido e invalidar imagens ao trocar o arquivo | Extensão além da extração mínima |
| Salvar / descartar | Salvar dados e relações em transação; reabrir valores persistidos ao descartar; devolver erros junto aos campos | MVP |
| Indicador de atualização | Mostrar data e usuário reais da última alteração | MVP |
| “SEO otimizado” / completude | Definir critérios calculáveis; retirar indicadores fictícios até haver regra | Extensão visual sem regra aprovada |

O nome exibido atualmente como arquivo e o título editorial precisam de campos/apresentações separados. O protótipo usa dados demonstrativos em posições que não representam ainda o contrato final do formulário.

“Marcar pessoa” deve enviar o `currentTime` do vídeo real convertido para milissegundos. A posição do navegador não é confiável para validação: o servidor valida o tempo e a relação com o vídeo novamente. A marcação exige título; a interface pode sugerir um título a partir do nome da pessoa.

Para duração informada manualmente, é preciso validar as marcações e legendas existentes antes de reduzir o valor. Proposta: rejeitar a mudança e listar os trechos que ficariam fora da duração, sem truncá-los silenciosamente.

### Acesso ao arquivo e reprodução

- Resolver o arquivo a partir de `Video.local_midia` e `caminho_relativo`; nunca receber um caminho absoluto arbitrário do player.
- Usar caminho canônico e verificar contenção na raiz ativa, incluindo caminhos com `..` e links simbólicos. Não basta comparar prefixos de texto.
- Proteger o endpoint do vídeo e das miniaturas por autenticação. A árvore local autorizada não vira um diretório estático público.
- Suportar leitura parcial HTTP (`Range`) para seek, com respostas apropriadas e entrega compatível com o servidor escolhido. Evitar carregar o arquivo inteiro na memória; o servidor pode assumir a entrega após autorização Django.
- Distinguir arquivo ausente, local desativado, acesso negado pelo sistema operacional, falha de inspeção e formato não reproduzível. Nenhum desses estados deve apagar o registro.
- Usar FFprobe/FFmpeg quando disponíveis, com argumentos estruturados, timeout e tratamento de falha. A falta da ferramenta não deve impedir o cadastro.
- Armazenar miniaturas geradas em área controlada e servi-las por referência ao registro. Valores técnicos desconhecidos ficam nulos, sem dados inventados.

Isso permite a leitura de arquivos locais para pré-visualização, sem introduzir upload de vídeo, conversão, publicação ou serviço de transmissão externo.

Play/pause, velocidade, volume, tela cheia, atalhos e movimentação da agulha são comportamentos do player no frontend. O backend fornece mídia, duração e anotações; não precisa de um endpoint para cada botão.

## 4. Capítulos e marcações temporais

Referências: `templates/studio/chapters.html`, `chapter_row.html`, modal de marcação e timeline.

Implementar criação, consulta, edição e exclusão de `MarcacaoTemporal`, com:

- vínculo obrigatório ao vídeo e título obrigatório;
- início em milissegundos e fim opcional: sem fim representa um ponto; com fim representa um intervalo;
- valores não negativos, fim não anterior ao início e nenhum limite além da duração conhecida;
- duração desconhecida sem bloqueio artificial de todas as marcações;
- sobreposição permitida e ordenação por início, com desempate estável;
- tags e pessoas da marcação independentes das associações do vídeo;
- criador, último editor e datas definidos pelo servidor;
- exclusão somente da marcação, sem apagar vídeo, tag, pessoa ou arquivo.

Capítulos usam essas marcações; não é necessário criar um segundo modelo de capítulos com tempos duplicados. O backend entrega os intervalos e pontos; o frontend calcula suas posições proporcionais na timeline e usa `currentTime` para destacar o trecho e reposicionar o player.

A waveform atual é decorativa. Uma forma de onda real exigiria extração de amostras, cache e invalidação por alteração do arquivo; não é necessária para os critérios do MVP.

## 5. Legendas

Referências: seletor de versão, modal SRT, entradas de legenda e estilo no player.

| Ação | Implementação necessária |
| --- | --- |
| Criar versão manual | Nome obrigatório, idioma opcional e vínculo ao vídeo |
| Importar SRT | Receber arquivo de legenda, interpretar texto e timecodes, validar todas as entradas e gravar versão/entradas de forma atômica |
| Selecionar versão para edição | Carregar as entradas daquela versão; trocar a seleção não deve ativá-la automaticamente |
| Ativar/desativar | Manter no máximo uma versão ativa por vídeo, em transação e com restrição no banco |
| Criar/editar/remover entrada | Validar texto, início, fim e vínculo com a versão/vídeo; reordenar de forma consistente |
| Exibir legenda no player | Entregar faixa ativa como VTT gerado ou dados estruturados autenticados e sincronizar com o tempo real |
| Alterar estilo | Tamanho e fundo no frontend; persistência opcional nas preferências pessoais |

Regras: início não negativo; fim estritamente posterior ao início; texto obrigatório; tempos dentro da duração quando conhecida. Importações devem tratar UTF-8/BOM, linhas CRLF/LF, texto multilinha e numeração SRT, indicando o trecho do erro sem criar uma versão parcialmente importada. Conteúdo de legenda deve ser exibido como texto, sem executar HTML enviado pelo usuário.

Sobreposição de entradas SRT não está definida nos requisitos. Proposta: aceitá-la e usar reprodução que suporte os trechos simultâneos; não reutilizar uma regra implícita de “um texto por instante” do simulador. Validar esse comportamento com arquivo real.

O upload SRT é permitido pelo escopo; isso não autoriza upload de vídeos. Definir limites operacionais de arquivo e quantidade de entradas para proteger o parser, sem inventar um limite de duração do vídeo. A geração interna de VTT para reprodução não inclui uma funcionalidade de exportação SRT.

## 6. Modelos e organização proposta

Manter `app/accounts` e a estrutura visual em `app/studio`. Acrescentar `app/catalog` para catálogo/mídia e `app/annotations` para marcações/legendas, conforme o plano existente. Views do Studio podem consumir esses serviços sem reconstruir o layout.

| Modelo | Campos/relações mínimos | Integridade |
| --- | --- | --- |
| `User` — existente | E-mail, nome, sobrenome, senha e flags Django | Administração de contas pelo Admin; não criar papéis novos a partir do badge “Editor” |
| `LocalMidia` | Nome, raiz absoluta, ativo | Configurado por administrador; raiz validada no servidor |
| `Video` | Título, descrição, local, caminho relativo, duração em ms, referência de miniatura, estado do arquivo, criador/editor e datas | Unicidade local + caminho normalizado; validação segura de referência |
| `Tag` | Nome de exibição, chave normalizada única, cor opcional | Normalização centralizada de espaços e caixa; unicidade também no banco |
| `Pessoa` | Nome de exibição e observações opcionais | Homônimos permitidos; selecionar pelo ID, não apenas pelo nome |
| `MarcacaoTemporal` | Vídeo, título, início/fim em ms, criador/editor e datas | Validação temporal e M2M com tags/pessoas |
| `VersaoLegenda` | Vídeo, nome, idioma, origem, ativa e datas | Restrição condicional de uma ativa por vídeo |
| `EntradaLegenda` | Versão, início/fim em ms, texto e ordem | Fim maior que início; ordenação determinística |

`Video` também tem M2M com tags e pessoas. Os índices devem atender caminho único, ordenação do catálogo e consultas por vídeo/versão e tempo. Campos técnicos adicionais são opcionais, sem bloquear cadastro quando a inspeção falhar.

Separar três conceitos antes de adicionar classificações: tipo técnico (vídeo/áudio/imagem), uso (master/corte/B-roll) e categoria editorial (educação/tecnologia). As opções das telas hoje misturam esses conceitos. Não criar um modelo genérico de mídia sem aprovar a ampliação além de vídeos.

### Serviços necessários

1. Resolução segura e verificação de disponibilidade da mídia local.
2. Inspeção técnica, geração de miniatura e correção manual dos dados.
3. Cadastro/atualização de vídeo e suas associações em transação.
4. Normalização/criação de tags e busca/cadastro de pessoas.
5. Validação/salvamento de marcações e tempos.
6. Parsing e importação atômica SRT.
7. Ativação de versão e montagem da faixa de reprodução.

Começar com serviços síncronos de tempo limitado. Se a extração de imagens tornar a requisição lenta, usar processamento em segundo plano com estado pendente/falhou e reexecução. Fila, scheduler e geração automática não são pré-requisitos de todo o backend.

## 7. Contratos de views propostos

São rotas para implementar, exceto as páginas GET já existentes. Django Forms, sessões e respostas HTML/HTMX atendem o produto; não há necessidade atual de uma API REST pública.

| Método / rota proposta | Responsabilidade |
| --- | --- |
| `GET /` | Catálogo paginado, filtros e fragmentos HTMX |
| `POST /videos/novo/` | Cadastrar referência local |
| `GET /videos/<id>/` | Editor/inspetor com dados reais |
| `POST /videos/<id>/salvar/` | Gravar metadados e associações do formulário |
| `GET /videos/<id>/midia/` | Leitura autenticada do arquivo com seek |
| `GET /videos/<id>/miniatura/` | Miniatura autenticada ou fallback |
| `GET /tags/buscar/` e `GET /pessoas/buscar/` | Busca paginada para seleção |
| `POST /tags/novo/` e `POST /pessoas/novo/` | Criar cadastro reutilizável; associação explícita ao destino |
| `GET /videos/<id>/capitulos/` | Marcações e versão selecionada |
| `POST /videos/<id>/marcacoes/nova/` | Criar ponto/intervalo e associações |
| `POST /videos/<id>/marcacoes/<marcacao_id>/salvar/` | Alterar marcação pertencente ao vídeo |
| `POST /videos/<id>/marcacoes/<marcacao_id>/remover/` | Excluir somente a marcação |
| `POST /videos/<id>/legendas/nova/` | Criar versão vazia ou importar SRT |
| `GET /videos/<id>/legendas/<versao_id>/` | Consultar entradas para edição |
| `POST /videos/<id>/legendas/<versao_id>/ativar/` | Ativar/desativar versão |
| `POST /videos/<id>/legendas/<versao_id>/entradas/salvar/` | Gravar conjunto validado de entradas em transação |
| `POST /videos/<id>/legendas/<versao_id>/entradas/<entrada_id>/remover/` | Excluir entrada da versão correta |
| `GET /videos/<id>/legendas/ativa.vtt` | Faixa autenticada para reprodução, caso se escolha VTT |

Mudanças de nome, idioma e entradas de uma versão podem compor um único formulário transacional. Não há endpoint de exclusão de vídeo/arquivo no MVP. As associações podem ser salvas com o formulário do vídeo ou em ações HTMX menores, mantendo o mesmo serviço de domínio.

Todas as mutações exigem POST e CSRF; GET permanece somente leitura. Validar relações pai/filho na consulta: uma entrada não pode ser alterada através do ID de outra versão ou vídeo. Não confiar em autor, estado técnico ou permissões enviados pelo navegador.

Ao falhar, devolver o formulário com os valores digitados e erros compreensíveis, inclusive em resposta HTMX. Só indicar sucesso após a transação terminar. Ao salvar por componentes, atualizar também os contadores, chips e inspetor afetados. Definir claramente quais alterações são imediatas e quais dependem do botão Salvar, para evitar perda de dados.

## 8. Perfil, menus e notificações: backend adicional

Essa seção cobre o necessário para tornar essas telas reais, mas não altera sua classificação como extensões nos requisitos atuais.

| Recurso visual | Backend necessário | Observação de escopo |
| --- | --- | --- |
| Identidade no menu/cabeçalho | Renderizar `request.user` e seus nomes/e-mail | Integração da autenticação existente ao MVP |
| Edição de nome/e-mail | Formulário de conta própria, unicidade e regra de segurança para mudança de e-mail | Autosserviço não previsto no MVP; contas hoje são administradas pelo Admin |
| Cargo, bio e avatar | Extensão de perfil vinculada ao usuário; validação e armazenamento controlado da imagem | Cargo descritivo não concede privilégios; upload de avatar é uma extensão específica |
| Tema, timezone e opções do editor | `UserPreferences` OneToOne; opções validadas e carregadas em cada sessão | Preferência pessoal; não precisa de “workspace” multiusuário novo |
| Sessões ativas | Associar sessões Django ao usuário, registrar informações disponíveis e permitir revogação das próprias sessões | Não mostrar dispositivo/localização fictícios; recurso adicional |
| Notificações internas | `Notification` com destinatário, tipo, texto, alvo, data e `read_at`; listagem e ações de marcar leitura | Exige definir eventos geradores e destinatários; não introduzir revisão/colaboração por implicação |
| Contador e “marcar todas como lidas” | Consultar somente notificações do usuário e atualizar leitura de forma idempotente | O link deve apontar para o recurso correto e respeitar sua disponibilidade |
| Preferências push/e-mail | Preferências por canal/evento; entrega, provedor, processamento e tratamento de falha | Chaves visuais não equivalem a envio implementado |
| Resumo semanal | Agendamento, seleção de eventos e entrega real | Extensão dependente de notificações e e-mail |
| YouTube, X e Instagram | Autorização OAuth, armazenamento protegido de credenciais, renovação/revogação e contratos dos provedores | Integrações externas estão fora do MVP |

A página `/componentes/` é referência de interface, não um domínio separado. Os menus podem usar os serviços de conta/notificação quando existirem. Até lá, recursos adicionais devem permanecer identificados como demonstração ou indisponíveis.

## 9. Sequência de implementação e aceite

| Etapa | Entrega concreta | Verificação principal |
| --- | --- | --- |
| 1 | Modelos, migrações, Admin de locais, caminhos seguros e autenticação aplicada | Cadastro consistente; raiz externa e local inativo bloqueados; nenhum acesso anônimo aos dados/arquivos |
| 2 | Cadastro/edição de vídeo, tags/pessoas e biblioteca real | Cadastrar, salvar, recarregar e reencontrar por busca, filtros e paginação |
| 3 | Inspeção, miniaturas e player real | Reproduzir/avançar arquivo suportado; manter edição quando faltar arquivo ou ferramenta |
| 4 | Marcações e pessoas por trecho | Criar ponto/intervalo, sobrepor, editar/remover; rejeitar tempos inválidos e posicionar player |
| 5 | Versões e entradas SRT | Importar/editar; falha não deixa dados parciais; uma versão ativa; sincronização real |
| 6 | Integração e entrega do MVP | Percorrer os oito critérios de aceite de `REQUISITOS.md` com registros e arquivos reais |
| 7 | Extensões aprovadas das telas | Perfil/preferências, notificações, lote e classificações em incrementos próprios |

Modelos e segurança vêm antes da conexão das telas; inspeção pode avançar junto ao catálogo após existir a referência segura. Testar integridade no banco, normalização de tags, homônimos, caminhos com traversal/symlink, arquivos ausentes, filtros M2M, transações, tempos em milissegundos, SRT inválido, ativação de versões e autenticação/CSRF/parentesco dos endpoints. Validar leitura parcial e codecs também no ambiente de implantação, não somente no servidor de desenvolvimento.

Os testes atuais da interface demonstrativa não comprovam persistência, reprodução de arquivo ou importação SRT. Não há estimativa de prazo neste levantamento: a infraestrutura de mídia e o escopo das extensões ainda precisam ser definidos para estimar com precisão.

## 10. Decisões que podem alterar o esforço

1. Quais raízes locais estarão disponíveis ao processo Django e onde a aplicação será executada? O caminho é do servidor, não do computador de qualquer usuário remoto.
2. O catálogo continuará exclusivamente de vídeos ou incluirá áudio/imagens? Se incluir, revisar o modelo e os comportamentos por tipo.
3. Quais campos visuais adicionais serão persistidos: categoria, idioma, classificação de uso, miniaturas candidatas e lote?
4. Perfil/preferências e notificações entram na entrega funcional inicial ou depois do MVP?
5. Para notificações, quais eventos reais geram avisos, quem recebe e quais canais serão usados?

Essas decisões não impedem começar pelo domínio aprovado. Integrações externas, upload/conversão de vídeo, exclusão de vídeo, papéis detalhados e auditoria histórica exigem revisão expressa de escopo antes da implementação.
