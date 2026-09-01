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
| `habilidades` | `JSONField` | Lista com as habilidades do Pokémon |
| `hp` | `IntegerField` | Atributo base de HP |
| `ataque` | `IntegerField` | Atributo base de Ataque |
| `defesa` | `IntegerField` | Atributo base de Defesa |
| `velocidade` | `IntegerField` | Atributo base de Velocidade |
| `sprite_url` | `CharField` | URL da imagem (sprite) do Pokémon |
| `observacoes` | `TextField` | Anotações livres do treinador sobre o Pokémon |
| `favorito` | `BooleanField` (padrão `False`) | Indica se o Pokémon está marcado como favorito |
| `capturado` | `BooleanField` (padrão `False`) | Indica se o Pokémon já foi capturado |
| `data_captura` | `DateField` (preenchido automaticamente) | Data em que o Pokémon foi adicionado à coleção |

---

## 📂 Estrutura do Projeto

```
pokedex-monolitico/
├── core/                    # Configurações do projeto Django (settings, urls raiz)
├── pokemon_api/             # App principal
│   ├── migrations/          # Migrações do banco de dados
│   ├── static/              # CSS e imagens do projeto
│   ├── templates/           # Templates HTML (base.html + páginas + includes/)
│   ├── templatetags/        # Filtro customizado (cor por tipo de Pokémon)
│   ├── models.py            # Model Pokemon
│   ├── views.py             # Views (home, buscar, salvar, listar, editar, remover)
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

# 4. Aplique as migrações do banco de dados
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

**Luidy Michael**
📚 [Curso/Instituição a confirmar]

<!-- Adicione aqui os demais integrantes do grupo, no mesmo formato -->

---

## 📌 Status do Projeto

🚧 Em desenvolvimento