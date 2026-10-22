# 🎮 Pokédex do Treinador

Aplicação web desenvolvida em **Django** que funciona como uma Pokédex pessoal, permitindo ao usuário **buscar Pokémon reais na PokeAPI** e **salvar, editar, favoritar e remover** os que capturar em sua própria coleção.

---

## 📌 Sobre o Projeto

O sistema resolve um problema simples e didático: como consumir dados de uma API externa (a [PokeAPI](https://pokeapi.co/)) e transformá-los em registros persistentes, controlados pelo próprio usuário, em um banco de dados local.

Diferente de uma Pokédex tradicional (que só exibe informações fixas de todos os Pokémon), aqui o usuário decide **quais Pokémon fazem parte da sua coleção**, podendo:

- Buscar qualquer Pokémon pelo nome ou número na PokeAPI
- Adicionar esse Pokémon à sua coleção pessoal (salvo no banco local)
- Editar informações do Pokémon (nível, observações, status)
- Marcar como capturado e/ou favorito
- Remover um Pokémon da coleção
- Acompanhar um resumo da coleção na tela inicial (total, favoritos, tipos descobertos)

---

## 🎯 Objetivos

- Praticar o consumo de uma API REST externa (PokeAPI) a partir do backend
- Implementar um CRUD completo (Create, Read, Update, Delete) em Django
- Reaproveitar templates HTML com herança (`extends`) e componentes (`include`)
- Persistir dados em banco relacional (SQLite) através do ORM do Django

---

## 🚀 Funcionalidades

- 🏠 **Início** — resumo da coleção (quantidade de Pokémon, favoritos e tipos descobertos) e destaque dos favoritos
- 🔍 **Buscar Pokémon** — pesquisa por nome ou número diretamente na PokeAPI, exibindo imagem, tipos, atributos base (HP, Ataque, Defesa, Velocidade), altura, peso e habilidades
- ➕ **Adicionar à coleção** — salva o Pokémon pesquisado no banco de dados local
- 📖 **Minha Coleção** — lista todos os Pokémon salvos, com indicação de favorito e status de captura
- ✏️ **Editar Pokémon** — permite atualizar qualquer campo do registro salvo
- 🗑️ **Remover Pokémon** — exclui um Pokémon da coleção, com tela de confirmação
- 🔎 **Detalhes do Pokémon** — tela que reúne os dados do registro, a **ficha de captura** (1:1) e as **habilidades** (N:N) com a indicação de oculta e o slot
- ⚡ **Habilidades** — CRUD completo do catálogo (listar com busca, cadastrar, ver detalhes com os Pokémon que a possuem, editar e remover com confirmação)

---

## 🧠 Regras de Negócio

- Os dados "de espécie" (sprite, altura, peso, habilidades, atributos base) vêm sempre da PokeAPI no momento da busca
- Só entram na coleção os Pokémon que o usuário adicionar manualmente pela tela de busca
- Um Pokémon só é considerado "Capturado" ou "Favorito" se o usuário marcar essas opções explicitamente
- A data de adição à coleção é registrada automaticamente pelo sistema

---

## 🏗️ Tecnologias Utilizadas

- **Backend:** Python + Django 6.1
- **Front-end:** HTML, CSS (templates renderizados pelo Django — sem framework JS)
- **Banco de dados:** SQLite
- **API externa:** [PokeAPI](https://pokeapi.co/) (consumida via biblioteca `requests`)

## 🔧 Ferramentas Utilizadas

- **Ambiente de desenvolvimento (IDE):** VSCode / PyCharm
- **Controle de versão:** Git e GitHub

---

## 🗃️ Modelo de Dados (`Pokemon`)

| Campo | Tipo | Descrição |
|---|---|---|
| `nome` | `CharField` (máx. 100) | Nome do Pokémon |
| `id_pokemon` | `IntegerField` | Número da Pokédex (ex: 25 para Pikachu) |
| `tipos` | `JSONField` | Lista com o(s) tipo(s) do Pokémon (ex: `["electric"]`) |
| `altura` | `CharField` (máx. 20) | Altura do Pokémon, conforme retornado pela PokeAPI |
| `peso` | `CharField` (máx. 20) | Peso do Pokémon, conforme retornado pela PokeAPI |
| `habilidades` | `ManyToManyField` (`through=PokemonHabilidade`) | Habilidades do Pokémon (N:N com o catálogo `Habilidade`) |
| `hp` | `IntegerField` | Atributo base de HP |
| `ataque` | `IntegerField` | Atributo base de Ataque |
| `defesa` | `IntegerField` | Atributo base de Defesa |
| `velocidade` | `IntegerField` | Atributo base de Velocidade |
| `sprite_url` | `CharField` | URL da imagem (sprite) do Pokémon |
| `observacoes` | `TextField` | Anotações livres do treinador sobre o Pokémon |
| `favorito` | `BooleanField` (padrão `False`) | Indica se o Pokémon está marcado como favorito |
| `capturado` | `BooleanField` (padrão `False`) | Indica se o Pokémon já foi capturado |
| `data_captura` | `DateField` (preenchido automaticamente) | Data em que o Pokémon foi adicionado à coleção |

### Novos models (Semana 1)

| Model | Campos principais | Relacionamento |
|---|---|---|
| `Regiao` | `nome` (único), `numero_inicial`, `numero_final` | 1:N com `Pokemon` (`Regiao.pokemons`) |
| `Treinador` | `nome`, `cidade_natal`, `data_cadastro` | 1:N com `Pokemon` (`Treinador.pokemons`) |
| `Habilidade` | `nome` (único), `descricao` | Catálogo de habilidades, usado no N:N com `through` (Semana 2) |

O model `Pokemon` ganhou duas `ForeignKey` opcionais: `treinador` e `regiao`. A região é definida automaticamente a partir do número da Pokédex (Kanto 1–151, Johto 152–251, e assim por diante). As 9 regiões são criadas pela própria migração `0005`.

### Novos models (Semana 2)

| Model | Campos principais | Relacionamento |
|---|---|---|
| `Captura` | `apelido`, `nivel` (1–100), `pokebola` (choices), `local`, `data_encontro` | **1:1** com `Pokemon` (`pokemon.captura`, `OneToOneField`, `CASCADE`) |
| `PokemonHabilidade` | `pokemon`, `habilidade`, `oculta`, `ordem` (slot) | **Tabela intermediária (`through`)** do **N:N** `Pokemon.habilidades` ↔ `Habilidade.pokemons` |

**1:1 — ficha de captura.** Cada Pokémon pode ter no máximo uma ficha (`OneToOneField`). Ela é preenchida na própria tela de adicionar/editar o Pokémon; se todos os campos ficarem vazios, nenhuma ficha é criada (e a existente é removida). A tela **Detalhes do Pokémon** (`/<id>/detalhes_pokemon/`) exibe os dados do Pokémon junto com a ficha.

**N:N com `through`.** `Pokemon.habilidades` é um `ManyToManyField(Habilidade, through='PokemonHabilidade')`. A tabela intermediária guarda dados do próprio vínculo: se a habilidade é **oculta** (`is_hidden` da PokeAPI) e a **ordem/slot**. Há uma `UniqueConstraint` em (`pokemon`, `habilidade`), impedindo repetir a mesma habilidade no mesmo Pokémon. Habilidades digitadas no formulário que ainda não existem entram automaticamente no catálogo (sem duplicar por maiúsculas/minúsculas). Excluir um Pokémon remove seus vínculos; excluir uma `Habilidade` desfaz os vínculos, mas **nunca** apaga os Pokémon.

**CRUD 2 — Habilidade** (segunda entidade do N:N):

| Operação | Rota | View |
|---|---|---|
| Listar (com busca `?q=`) | `/listar_habilidades/` | `listar_habilidades` |
| Criar | `/criar_habilidade/` | `criar_habilidade` |
| Detalhes (Pokémon que a possuem) | `/<id>/detalhes_habilidade/` | `detalhes_habilidade` |
| Editar | `/<id>/editar_habilidade/` | `editar_habilidade` |
| Remover (GET confirma, POST exclui) | `/<id>/remover_habilidade/` | `remover_habilidade` |

> **Migração dos dados antigos:** as migrações `0006` → `0008` criam as novas tabelas, **copiam** as habilidades que estavam no campo JSON `Pokemon.habilidades` para a tabela intermediária (preservando a ordem) e só então removem o campo antigo. A `0007` é reversível.

### Dashboard

A tela inicial (`/`) exibe indicadores calculados direto do banco: total na coleção, capturados, favoritos, tipos descobertos, treinadores, habilidades catalogadas, Pokémon por região, Pokémon por treinador, média dos atributos, Pokémon mais forte e últimos adicionados.

### Testes

```bash
python manage.py test
```

---

## 📂 Estrutura do Projeto

```
pokedex-monolitico/
├── core/                    # Configurações do projeto Django (settings, urls raiz)
├── pokemon_api/             # App principal
│   ├── migrations/          # Migrações do banco de dados
│   ├── static/              # CSS e imagens do projeto
│   ├── templates/           # Templates HTML (base.html + páginas + includes/)
│   │                        #   detalhes_pokemon, listar/form/detalhes/confirmar_remocao_habilidade
│   ├── templatetags/        # Filtro customizado (cor por tipo de Pokémon)
│   ├── models.py            # Pokemon, Regiao, Treinador, Habilidade, PokemonHabilidade, Captura
│   ├── forms.py             # HabilidadeForm e CapturaForm (validação em português)
│   ├── views.py             # Views (home, buscar, CRUD de Pokémon, detalhes, CRUD de Habilidade)
│   ├── services.py          # Integração com a PokeAPI
│   └── urls.py               # Rotas do app
├── manage.py
├── requirements.txt
└── db.sqlite3                # Banco de dados (gerado após as migrações)
```

---

## ⚙️ Instruções de Execução

Pré-requisito: **Python 3.10+** instalado.

```bash
# 1. Clone o repositório
git clone https://github.com/LU1DY/django-podekex.git
cd django-podekex

# 2. Crie e ative um ambiente virtual
python -m venv venv

# Windows
venv\Scripts\activate

# Linux/Mac
source venv/bin/activate

# 3. Instale as dependências
pip install -r requirements.txt

# 4. Aplique as migrações do banco de dados (inclui a migração das habilidades antigas)
python manage.py migrate

# 5. Rode o servidor de desenvolvimento
python manage.py runserver
```

Acesse **http://127.0.0.1:8000/** no navegador para abrir a página inicial da Pokédex.

> Opcional: crie um usuário administrador para acessar `/admin/` com `python manage.py createsuperuser`.

---

## 💡 Diferenciais

- Reaproveitamento de HTML com `{% extends %}` e `{% include %}`, evitando repetição de código entre as páginas
- Filtro customizado (`templatetags`) para colorir dinamicamente as badges de tipo de cada Pokémon
- Dados sempre atualizados na busca, por virem diretamente da PokeAPI

---

## 📈 Possíveis Melhorias Futuras

- Autenticação de usuários (permitindo múltiplos treinadores com coleções próprias)
- Paginação e busca/filtro por tipo na tela "Minha Coleção"
- Upload de imagem própria do Pokémon, além da sprite da PokeAPI
- Versão da API em REST Framework para consumo por um front-end separado (React, mobile, etc.)

---

## 👨‍💻 Autores

**Luidy Michael da Silva**
📚 Sistema de Informação - FEPI

**Gustavo Faria Melo Silva**
📚 Sistema de Informação - FEPI

<!-- Adicione aqui os demais integrantes do grupo, no mesmo formato -->
