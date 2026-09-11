# 💰 Perrut - Controle Financeiro

Aplicativo desktop de controle financeiro pessoal desenvolvido em **Python**, com autenticação de usuários, persistência em banco de dados na nuvem e exportação de relatórios.

O projeto nasceu de uma necessidade real: organizar minhas próprias finanças. A partir daí, virou um estudo prático de arquitetura de software — separação de responsabilidades (views, config, utils), autenticação segura, integração com banco de dados externo e tratamento de erros em operações assíncronas.

---

## 📸 Demonstração

**Tela de Login**
![Tela de login](screenshots/tela_de_login.gif)

**Dashboard principal**
![Dashboard](screenshots/dashboard.gif)

**Exportação de relatório CSV**
![Exportação CSV](screenshots/download_csv.gif)

---

## ✨ Funcionalidades

- 🔐 **Login e autenticação** de usuários via Supabase
- 💾 **Persistência de sessão local** (opção "lembrar login")
- ➕ **Cadastro de receitas e despesas**, com categoria, forma de pagamento e status de pagamento
- 📊 **Totais automáticos** por categoria e por tipo (receita/despesa)
- 📈 **Gráfico visual** dos gastos por categoria
- 🗂️ **Filtros por mês e ano**
- 📄 **Exportação de relatórios em CSV**
- 🧾 **Relatório mensal detalhado**
- 🖥️ Interface construída com **Flet** (Python + Flutter)

---

## 🛠️ Tecnologias utilizadas

- [Python](https://www.python.org/)
- [Flet](https://flet.dev/) — construção da interface gráfica
- [Supabase](https://supabase.com/) — autenticação e banco de dados
- [Matplotlib](https://matplotlib.org/) — geração de gráficos
- [python-dotenv](https://pypi.org/project/python-dotenv/) — variáveis de ambiente

---

## 🧩 Decisões técnicas e desafios

- **Sessão local com auto-login:** o app salva os tokens de sessão localmente e tenta reautenticar automaticamente ao abrir, com fallback seguro para a tela de login caso a sessão esteja expirada ou inválida — sem travar a aplicação.
- **Variáveis de ambiente para credenciais:** `SUPABASE_URL` e `SUPABASE_KEY` nunca ficam hardcoded; o app falha de forma explícita (`RuntimeError`) se as variáveis não estiverem configuradas, em vez de falhar silenciosamente.
- **Exportação de CSV com encoding correto:** ajustei o delimitador (`;`) e a codificação do arquivo exportado para abrir corretamente no Excel em português, evitando o problema comum de acentuação quebrada em CSVs gerados por Python.
- **Operações assíncronas:** chamadas à API do Supabase rodam em thread separada (`asyncio.to_thread`) para não travar a interface enquanto os dados carregam.

---

## 🚀 Como rodar o projeto localmente

### Pré-requisitos
- Python 3.10 ou superior instalado
- Uma conta gratuita no [Supabase](https://supabase.com/) com um projeto criado

### Passo a passo

```bash
# 1. Clone o repositório
git clone https://github.com/seu-usuario/seu-repositorio.git
cd seu-repositorio

# 2. Crie um ambiente virtual (recomendado)
python -m venv venv
venv\Scripts\activate      # Windows
source venv/bin/activate   # Linux/Mac

# 3. Instale as dependências
pip install -r requirements.txt
```

Crie um arquivo `.env` na raiz do projeto com suas próprias credenciais do Supabase:

```env
SUPABASE_URL=sua_url_aqui
SUPABASE_KEY=sua_chave_aqui
```

> ⚠️ O arquivo `.env` nunca deve ser enviado ao GitHub. Ele já está listado no `.gitignore` deste projeto.

Por fim, rode o projeto:

```bash
python main.py
```

---

## 📁 Estrutura do projeto

```
├── main.py                  # Ponto de entrada da aplicação
├── config/
│   └── supabase_client.py   # Conexão com Supabase e categorias padrão
├── views/
│   ├── login_view.py        # Tela de login
│   └── dashboard_view.py    # Tela principal (dashboard)
├── components/
│   └── matrix_bg.py         # Componentes visuais reutilizáveis
├── utils/
│   └── helpers.py           # Funções auxiliares (sessão, exportação CSV, etc.)
├── assets/
│   └── exports/             # Relatórios exportados
└── requirements.txt         # Dependências do projeto
```

---

## 🧠 Sobre o desenvolvimento

Este projeto é resultado de aprendizado autodidata, combinando estudo próprio com apoio de ferramentas de IA (Gemini e Claude) para acelerar pesquisa, revisar código e entender conceitos novos — da mesma forma que qualquer desenvolvedor hoje usa documentação, fóruns e pair programming. As decisões de arquitetura, a modelagem dos dados e a resolução de bugs de produção (autenticação, encoding de arquivos, tratamento de exceções) foram feitas e validadas por mim.

Estou em transição de carreira para desenvolvimento de software e busco oportunidades como estagiário ou desenvolvedor júnior. Feedback técnico é muito bem-vindo — se você é recrutador ou desenvolvedor e tiver sugestões sobre o código, fico feliz em conversar.

---

## 🔜 Próximos passos

- [ ] Testes automatizados (unitários para `helpers.py` e integração para o fluxo de autenticação)
- [ ] Exportação também em PDF, além de CSV
- [ ] Deploy do relatório mensal como serviço web (avaliando Render/Railway)
- [ ] Refatorar `dashboard_view.py` em componentes menores

---

## 📬 Contato

**Desenvolvido por:** Carlos Perrut
**E-mail:** carloshperruts@gmail.com

---

## 📄 Licença

Projeto pessoal para fins de estudo e portfólio.
