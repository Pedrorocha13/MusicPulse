# MusicPulse
Sharing some insights and metrics.
## Modules
### 1 - Heatmap Brazil

O que é viável de verdade
- Spotify Charts tem charts por cidade e “local pulse” (e outros recortes), mas não é uma “API oficial simples”; é um produto web que exige login pra acessar tudo.
- Você usa a Spotify Web API pra enriquecer as faixas (artista, álbum, popularidade, mercados) e (opcional) áudio-features.

Como fica o insight (bem LinkedIn)
- Coleta diária/semanal do chart por capitais (SP, RJ, BH, SSA, REC…)
- Mapeia capital → estado → região
- Enriquecimento: gênero do artista / popularidade / atributos
- Saída: “Mapa do Brasil do som” (top gêneros/estilos por região + evolução no tempo)

Métrica legal: “Índice de diversidade musical” por estado (Shannon/Simpson) + “dominância” (quanto o top1 gênero domina o top200).

### 2 - Shows por Estado
“O que leva artista internacional a escolher estados pra show?”

Dá pra fazer… sem virar tese de doutorado, mas você precisa definir bem a proxy.

Fontes viáveis

- Ticketmaster Discovery API (eventos/venues e, às vezes, informações de preço/“price ranges” dependendo do mercado/listagem).
- Bandsintown tem endpoints de eventos de artistas (bom pra tour dates) e integrações com plataformas; documentação existe, mas cobertura varia.
- IBGE / dados.gov pra população e PIB per capita (pra você calcular “capacidade de consumo per capita”/mercado potencial).

Como transformar sua ideia em análise sólida
Você quer algo tipo “capitalização por pessoa alcançada”. Como preço real e público “por estado” nem sempre vem completo, sugiro 2 caminhos:

Caminho A (prático e defensável):

- “Escolha de estado” ~ função de população + PIB per capita + concentração urbana + histórico de eventos
- Proxy de “pessoa alcançada”: capacidade do venue (quando disponível) ou tamanho do evento (quando não, usa categoria + venue como proxy)
- Proxy de “capitalização”: estimativa_receita = capacidade * preço_médio_estimado (ou usa a faixa se vier do Ticketmaster; se não vier, assume faixas fixas por tipo de evento e deixa isso explícito no README)
- 
Caminho B (mais musical, menos econômico):

- Traz do Spotify (catálogo) popularidade e seguidores do artista e mede “atratividade” do estado via:
  - presença do artista nos charts locais
  - crescimento de plays do artista na região (via charts locais)
  - e correlaciona com decisão de passar por lá.

### 3 - "Eu estou no Mainstream/Hype?"
Esse é o seu módulo mais original e 100% executável com Spotify.

Dados do seu usuário (Spotify Web API)
- Recently Played pra histórico real de reprodução.
- Top Artists/Tracks por janelas (4 semanas / 6 meses / anos).
- Scopes: user-read-recently-played e user-top-read.

Como medir “seguir o hype”

Você compara o que você ouviu vs o que está “quente” no lugar:
- Overlap score (Jaccard): quantas músicas do chart local também aparecem no seu histórico
- Rank correlation: seu ranking vs ranking do chart (Spearman)
- Hype lag: quantos dias depois de a faixa entrar no chart você passa a ouvir (isso é MUITO postável: “sou early adopter ou chego atrasado?”)


<br>
<img width="435" height="452" alt="Logic" src="https://github.com/user-attachments/assets/f8420a5c-89d0-4c58-8e7b-f85dc7325570" />
<br/>
