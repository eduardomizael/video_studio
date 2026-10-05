# Requisitos — Video Studio

**Versão:** 0.2  
**Status:** requisitos do MVP consolidados; pronto para planejamento de implementação  
**Base:** descrição inicial do produto e consulta direta ao projeto privado do Google Stitch pelo MCP em 21/09/2026. Os protótipos são referência de intenção visual e de fluxo; não constituem requisitos aprovados automaticamente.

## 1. Visão do produto

O Video Studio é uma aplicação para centralizar e administrar informações descritivas de vídeos. Seu objetivo é permitir que um usuário encontre um vídeo, consulte seu conteúdo e mantenha metadados estruturados — descrição, tags, pessoas e marcações temporais — sem editar o arquivo de mídia.

O produto deve tratar o vídeo como o item central. Os demais dados são associados a ele e devem poder ser criados, alterados e removidos de forma independente.

## 2. Objetivos

- Manter um catálogo pesquisável de vídeos e seus metadados.
- Oferecer uma tela de detalhe/edição focada em um vídeo por vez.
- Registrar pessoas, tags e eventos em pontos ou intervalos da linha do tempo.
- Tornar a localização de vídeos mais rápida por texto, tag, pessoa e tempo marcado.
- Preservar a consistência entre a duração do vídeo e suas marcações temporais.

## 3. Escopo inicial (MVP)

Inclui:

- cadastro, consulta e edição de registros de vídeo;
- reprodução ou pré-visualização do vídeo na tela de detalhe, quando o arquivo estiver disponível;
- edição de título e descrição;
- associação de tags reutilizáveis;
- associação de pessoas reutilizáveis;
- criação e edição de marcações temporais vinculadas ao vídeo;
- importação e edição de versões de legenda em formato SRT;
- listagem, busca e filtros básicos no catálogo;
- persistência dos dados e controle de acesso para usuários autenticados.

Fica fora do MVP, salvo decisão posterior:

- edição, conversão, hospedagem ou transmissão de arquivos de vídeo;
- exclusão de arquivos de vídeo ou de seus registros pela interface;
- reconhecimento automático de pessoas, fala, objetos ou geração automática de tags;
- colaboração simultânea, comentários e aprovação editorial;
- permissões detalhadas por vídeo ou por campo;
- versionamento/auditoria de cada alteração;
- exportação e integração com plataformas externas.

## 4. Perfis de usuário

| Perfil | Responsabilidades no MVP |
| --- | --- |
| Usuário autenticado | Consultar o catálogo e criar ou editar seus metadados. No MVP, todos os usuários autenticados têm as mesmas permissões de trabalho. |
| Administrador | Criar e administrar usuários e configurar locais de mídia pelo Django Admin. |

O projeto deve iniciar com um modelo customizado de usuário do Django. Grupos e papéis detalhados serão incorporados em evolução futura, sem modificar o modelo de usuário já em produção.

## 5. Conceitos e dados do domínio

| Entidade | Finalidade | Campos mínimos propostos |
| --- | --- | --- |
| Local de mídia | Raiz local autorizada para os arquivos de vídeo. | identificador, nome, caminho absoluto no servidor, ativo. |
| Vídeo | Registro principal do catálogo. | identificador, título, descrição opcional, local de mídia, caminho relativo, duração, miniatura opcional, estado do arquivo, data de criação, data de atualização. |
| Tag | Termo reutilizável para classificação. | identificador, nome único, cor opcional. |
| Pessoa | Pessoa identificada ou relacionada ao vídeo. | identificador, nome de exibição, observações opcionais. |
| Marcação temporal | Anotação posicionada na linha do tempo de um vídeo. | identificador, vídeo, instante inicial, instante final opcional, título. |
| Versão de legenda | Faixa de legendas de um vídeo importada ou editada. | identificador, vídeo, nome da versão, idioma opcional, ativa, origem, data de atualização. |
| Entrada de legenda | Trecho sincronizado de uma versão de legenda. | identificador, versão, instante inicial, instante final, texto, ordem. |
| Usuário | Pessoa que acessa o sistema. | identificador, nome, e-mail, perfil, estado de acesso. |

Relações propostas:

- um vídeo pode ter várias tags; uma tag pode pertencer a vários vídeos;
- um vídeo pode ter várias pessoas; uma pessoa pode estar em vários vídeos;
- um vídeo pode ter várias marcações temporais;
- um vídeo pode ter várias versões de legenda, mas somente uma versão pode estar ativa para reprodução por vez;
- uma versão de legenda possui várias entradas sincronizadas;
- uma marcação pode ter suas próprias tags e pessoas. Isso evita atribuir ao vídeo inteiro algo que aparece apenas em uma cena.

## 6. Requisitos funcionais

### 6.1. Catálogo e pesquisa

- **RF-01.** O sistema deve exibir uma lista paginada de vídeos cadastrados.
- **RF-02.** Cada item da lista deve apresentar, no mínimo, miniatura ou indicador visual, título, duração quando conhecida, tags principais e data de atualização.
- **RF-03.** O usuário deve pesquisar vídeos por título e descrição.
- **RF-04.** O usuário deve filtrar a lista por uma ou mais tags.
- **RF-05.** O usuário deve filtrar a lista por uma ou mais pessoas associadas.
- **RF-06.** O usuário deve abrir a tela de detalhe de um vídeo a partir do catálogo.

### 6.2. Vídeo

- **RF-07.** O usuário autorizado deve criar um registro de vídeo informando, no mínimo, título, local de mídia e caminho relativo do arquivo.
- **RF-08.** O usuário autorizado deve editar título e descrição do vídeo.
- **RF-09.** O sistema deve exibir a duração do vídeo quando ela for conhecida.
- **RF-10.** O sistema deve exibir um player ou pré-visualização quando houver mídia acessível.
- **RF-11.** O sistema não deve oferecer exclusão de arquivo de vídeo nem de seu registro pela interface do MVP.
- **RF-12.** O sistema deve informar claramente quando há apenas o registro de metadados e o arquivo de mídia não está disponível para reprodução, identificando o estado como `arquivo não encontrado`.
- **RF-13.** O sistema deve validar que o caminho informado pertence a um local de mídia ativo e configurado no servidor.
- **RF-14.** Ao cadastrar ou atualizar a referência de um vídeo, o sistema deve tentar obter automaticamente duração e miniatura; o usuário deve poder informar ou corrigir esses dados manualmente quando a extração não for possível.

### 6.3. Tags e pessoas

- **RF-15.** O usuário deve associar uma ou mais tags existentes a um vídeo.
- **RF-16.** O usuário autorizado deve criar uma tag ao informar um nome ainda inexistente.
- **RF-17.** O sistema não deve duplicar tags cujo nome seja considerado equivalente pela regra definida para o produto.
- **RF-18.** O usuário deve associar uma ou mais pessoas existentes a um vídeo.
- **RF-19.** O usuário autorizado deve cadastrar uma pessoa durante a associação, quando ela ainda não existir.
- **RF-20.** O usuário deve remover uma associação de tag ou pessoa sem apagar o cadastro global correspondente.

### 6.4. Marcações de tempo

- **RF-21.** O usuário deve criar uma marcação temporal em um instante do vídeo ou em um intervalo entre dois instantes.
- **RF-22.** O usuário deve poder criar uma marcação a partir da posição atual do player, quando houver player disponível.
- **RF-23.** O usuário deve informar e editar o título obrigatório da marcação.
- **RF-24.** O sistema deve listar as marcações em ordem cronológica e permitir sobreposição entre elas.
- **RF-25.** Ao selecionar uma marcação, o sistema deve posicionar o player em seu instante inicial, quando possível.
- **RF-26.** O sistema deve permitir editar e excluir uma marcação.
- **RF-27.** O sistema deve impedir instantes negativos, início posterior ao fim e tempos além da duração conhecida do vídeo.
- **RF-28.** O sistema deve indicar visualmente na linha do tempo os pontos e intervalos marcados, quando houver player disponível.

### 6.5. Legendas

- **RF-29.** O usuário deve importar uma versão de legenda no formato SRT para um vídeo.
- **RF-30.** Cada versão de legenda deve ter nome obrigatório e idioma opcional.
- **RF-31.** O usuário deve criar, editar e remover entradas de legenda, incluindo texto e intervalo de tempo.
- **RF-32.** O sistema deve validar que cada entrada possui início não negativo, fim posterior ao início e tempos compatíveis com a duração conhecida do vídeo.
- **RF-33.** O sistema deve permitir várias versões de legenda por vídeo e selecionar somente uma como ativa por vez.
- **RF-34.** Quando houver player e uma versão ativa, o sistema deve exibir as entradas sincronizadas durante a reprodução.

### 6.6. Acesso e rastreabilidade mínima

- **RF-35.** O sistema deve exigir autenticação para consultar ou alterar o catálogo.
- **RF-36.** No MVP, todo usuário autenticado deve poder criar e editar metadados; administração de usuários e de locais de mídia fica restrita ao Django Admin.
- **RF-37.** O sistema deve registrar data e usuário responsável pela criação e pela última atualização de cada vídeo e marcação.

## 7. Requisitos de interface

- **RI-01.** A tela de catálogo deve privilegiar a descoberta: busca, filtros visíveis e resultados rapidamente escaneáveis.
- **RI-02.** A tela de detalhe deve manter vídeo/player, dados descritivos e marcações temporais em uma mesma experiência, sem exigir múltiplas navegações para uma edição comum.
- **RI-03.** A edição de tags e pessoas deve suportar busca por texto, seleção múltipla e criação controlada de novo item.
- **RI-04.** A linha do tempo deve apresentar tempo em formato compreensível (por exemplo, `mm:ss` ou `hh:mm:ss`) e controles que não exijam precisão manual excessiva.
- **RI-05.** A interface deve informar alterações não salvas, sucesso de salvamento e erros de validação de maneira explícita.
- **RI-06.** A aplicação deve ser utilizável em desktop; interfaces móveis não integram o MVP.

## 8. Requisitos não funcionais

- **RNF-01. Segurança:** senhas nunca devem ser armazenadas em texto aberto; sessão e autorização devem ser protegidas.
- **RNF-02. Integridade:** associações e marcações devem ser transacionais; uma alteração inválida não pode deixar dados parcialmente salvos.
- **RNF-03. Desempenho:** busca e abertura da lista devem manter resposta percebida como imediata para a capacidade do ambiente inicial, sem impor limite funcional de duração, tamanho ou volume de vídeos.
- **RNF-04. Acessibilidade:** campos devem ter rótulos, foco por teclado e contraste adequado; ações não devem depender apenas de cor.
- **RNF-05. Compatibilidade:** definir navegadores suportados antes da implementação.
- **RNF-06. Observabilidade:** erros de aplicação devem ser registrados com contexto técnico, sem expor dados sensíveis ao usuário.
- **RNF-07. Privacidade:** a política de retenção e a classificação de dados de pessoas devem ser definidas antes de armazenar dados pessoais sensíveis.

## 9. Critérios de aceite do MVP

1. Um usuário autorizado cadastra um vídeo, acrescenta título, descrição, duas tags e duas pessoas, salva e reencontra o vídeo pela busca e pelos filtros.
2. Na tela de detalhe, o usuário cria uma marcação pontual e uma por intervalo; ambas aparecem em ordem cronológica, podem se sobrepor e podem ser editadas e removidas.
3. Uma marcação inválida (tempo negativo, intervalo invertido ou além da duração) é bloqueada e recebe mensagem compreensível.
4. Quando a mídia está acessível, selecionar uma marcação desloca a reprodução para o instante correspondente.
5. Quando a mídia não está acessível, os metadados continuam consultáveis e editáveis, e a indisponibilidade é informada.
6. Um usuário autenticado cria e edita metadados; o Django Admin é o único local inicial para administração de usuários e locais de mídia.
7. O usuário importa uma versão SRT, edita suas entradas e a torna ativa; durante a reprodução, as legendas ativas são apresentadas no tempo correspondente.
8. Quando um arquivo referenciado deixa de existir, seu registro continua disponível e mostra o estado `arquivo não encontrado`.

## 10. Decisões consolidadas para o MVP

| ID | Decisão tomada |
| --- | --- |
| D-01 | Os vídeos são cadastrados a partir de caminhos locais acessíveis pelo servidor Django; cada caminho deve pertencer a um local de mídia configurado. |
| D-02 | A descoberta é manual. Não haverá upload, busca automática, nuvem nem URLs externas no MVP. |
| D-03 | A aplicação deve aceitar formatos comuns reproduzíveis no navegador. Não há limite de duração, tamanho ou volume definido para o MVP. |
| D-04 | Tags e pessoas são globais e reutilizáveis. |
| D-05 | Tags e pessoas também podem ser associadas às marcações temporais. |
| D-06 | Marcações podem ser pontuais ou por intervalo, podem se sobrepor e possuem somente título obrigatório. |
| D-07 | Todos os usuários autenticados podem criar e editar metadados no MVP. Papéis e grupos serão definidos futuramente; o modelo customizado de usuário é obrigatório desde o início. |
| D-08 | Registra-se somente autor e data de criação e da última atualização de vídeos e marcações. |
| D-09 | Não haverá comentários, revisão/aprovação nem colaboração simultânea. |
| D-10 | A aplicação será em português e para desktop. |
| D-11 | Legendas têm múltiplas versões por vídeo, são importadas em SRT, podem ser editadas e são sincronizadas por intervalo. Uma versão fica ativa por vez. |
| D-12 | Duração e miniatura devem ser extraídas automaticamente quando possível e podem ser corrigidas manualmente. |
| D-13 | Arquivo ausente não remove o registro: o vídeo é marcado como `arquivo não encontrado`. A interface não permite excluir vídeos nem arquivos. |
| D-14 | Usuários e locais de mídia são administrados inicialmente pelo Django Admin. |
| D-15 | O frontend usa templates Django e HTMX; o CSS Tailwind é compilado por um build Node. O ambiente Python é gerenciado por UV e o banco inicial é SQLite. |

## 11. Referência dos protótipos Stitch

O projeto **Video Metadata Player Interface** foi consultado diretamente por MCP. Ele contém os seguintes protótipos desktop:

| Protótipo | Evidência para os requisitos | Tratamento no documento |
| --- | --- | --- |
| Biblioteca de Mídia | Há uma área dedicada ao catálogo de vídeos. | Confirmado em RF-01 a RF-06. |
| Editor de Metadados & Vídeo | Há uma experiência unificada de player e edição de informações. | Confirmado em RF-08 a RF-10 e RI-02. |
| Capítulos e Legendas | Há intenção de organizar conteúdo por trechos e trabalhar legendas. | Capítulos são cobertos por marcações de intervalo; versões SRT editáveis integram o MVP. |
| Menus Suspensos de Usuário & Notificações | Há elementos de sessão do usuário e notificações. | Autenticação é tratada no MVP; notificações não entram no escopo sem decisão explícita. |
| Perfil do Usuário e Configurações | Há configuração por usuário. | Perfil administrativo e configurações específicas ficam fora do MVP, salvo decisão posterior. |

O sistema visual observado é de uma suíte profissional em modo escuro, com navegação lateral, área central de mídia, inspetor contextual à direita, tipografia Inter para a interface e JetBrains Mono para timecodes. Isso orienta RI-01 a RI-06, mas não fixa uma implementação visual antes da validação do produto.
