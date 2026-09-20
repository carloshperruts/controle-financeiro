# 💰 Perrut - Controle Financeiro

Sistema web e desktop de controle financeiro pessoal desenvolvido em **Python**, com autenticação de usuários, persistência em banco de dados na nuvem e exportação de relatórios.

O projeto nasceu de uma necessidade real: organizar minhas próprias finanças. A partir daí, virou um estudo prático de arquitetura de software — separação de responsabilidades (views, config, utils), autenticação segura, integração com banco de dados externo e tratamento de erros em operações assíncronas.

---

## 📸 Demonstração

**Preview geral (versão atual)**
![Preview geral do sistema](screenshots/preview_geral.gif)

**Tela de Login**
![Tela de login](screenshots/tela_de_login.gif)

**Dashboard principal**
![Dashboard](screenshots/dashboard.gif)

**Exportação de relatório CSV**
![Exportação CSV](screenshots/download_csv.gif)

---

## ✨ Funcionalidades

- 🔐 **Login e cadastro** via Supabase, com envio do e-mail de recuperação de senha (a troca da senha pelo link ainda não está implementada)
- 💾 **Persistência de sessão local** (opção "lembrar login")
- ➕ **Cadastro de receitas e despesas**, com categoria, forma de pagamento e status de pagamento
- 💳 **Compras parceladas no cartão de crédito**, com vencimento e divisão exata do valor entre as parcelas
- 📊 **Totais automáticos** por categoria e por tipo (receita/despesa)
- 📈 **Gráfico visual** dos gastos por categoria
- 🗂️ **Filtros por mês e ano**
- 📄 **Exportação de relatórios em CSV e PDF**
- 🧾 **Relatório mensal detalhado**
- 🖥️ Interface construída com **Flet** (Python + Flutter), rodando tanto como **app desktop** quanto como **aplicação web** (`python main.py --web`)

---

## 🛠️ Tecnologias utilizadas

- [Python](https://www.python.org/)
- [Flet](https://flet.dev/) — construção da interface gráfica
- [Supabase](https://supabase.com/) — autenticação e banco de dados
- [ReportLab](https://www.reportlab.com/) — geração dos relatórios em PDF
- [pytest](https://pytest.org/) — testes automatizados
- [python-dotenv](https://pypi.org/project/python-dotenv/) — variáveis de ambiente

---

## 🧩 Desafios e aprendizados

Mais do que decisões de arquitetura pensadas de antemão, o maior desafio deste projeto foi testar o app de ponta a ponta, encontrar os erros que só aparecem em uso real e ajustar o código a partir disso. Alguns exemplos concretos:

- **Falha silenciosa de renderização (tela cinza):** combinar `wrap=True` num `ft.Row` com filhos `expand=True` gerava um crash do lado do Flutter sem nenhum erro no terminal Python. Foi preciso isolar o problema com scripts de teste progressivos (do mínimo até reproduzir a falha) até identificar a incompatibilidade e resolver trocando `expand=True` por larguras fixas.
- **Sessão local com auto-login:** o app salva os tokens de sessão localmente e tenta reautenticar automaticamente ao abrir, com fallback seguro para a tela de login caso a sessão esteja expirada ou inválida — sem travar a aplicação.
- **Exportação assíncrona:** o download de CSV inicialmente travava por um descompasso entre chamada síncrona e assíncrona; resolvido encapsulando a chamada com `asyncio.create_task`, além de tratar caminhos de arquivo de forma diferente para desktop (`file:///`) e web.
- **Exportação de CSV com encoding correto:** ajustei o delimitador (`;`) e a codificação do arquivo exportado para abrir corretamente no Excel em português, evitando o problema comum de acentuação quebrada em CSVs gerados por Python.
- **Variáveis de ambiente para credenciais:** `SUPABASE_URL` e `SUPABASE_KEY` nunca ficam hardcoded; o app falha de forma explícita (`RuntimeError`) se as variáveis não estiverem configuradas, em vez de falhar silenciosamente.
- **Operações assíncronas:** chamadas à API do Supabase rodam em thread separada (`asyncio.to_thread`) para não travar a interface enquanto os dados carregam.

### 🐞 Bugs encontrados e corrigidos

Numa revisão do código feita com apoio do Claude (IA), foram identificados quatro pontos de risco. Eu validei cada correção rodando o app localmente e depois no ar, e cada uma tem testes automatizados escritos para falhar no código antigo e passar com a correção:

- **Centavos perdidos nas parcelas:** dividir e arredondar igual para todas as parcelas fazia R$ 100,00 em 3x somar R$ 99,99. A divisão agora é feita em centavos inteiros e o que sobra é distribuído entre as primeiras parcelas, então a soma sempre bate com o total (33,34 / 33,33 / 33,33).
- **Leitura de valores digitados:** `1234.56` era lido como R$ 123.456,00, `R$ 50,00` virava zero e textos como `nan` ou `inf` passavam como número. A leitura passou a aceitar ponto decimal e o símbolo R$, e a recusar o que não é um valor válido.
- **Um único cliente do Supabase para todos os usuários:** ao ler o código da biblioteca, vi que o cliente guarda um único token e que o último login sobrescreve o anterior. Como o app web atende várias sessões no mesmo processo, passei a criar um cliente por sessão. Com o RLS ativo no banco, o efeito esperado era falha nas consultas do usuário afetado, e não acesso a dados de terceiros.
- **Fuso horário:** datas em UTC vindas do banco agora são convertidas para o horário de Brasília antes de decidir o mês de um lançamento, para que uma compra feita à noite não caia no mês seguinte.

---

## 🚀 Como rodar o projeto localmente

### Pré-requisitos
- Python 3.10 ou superior instalado
- Uma conta gratuita no [Supabase](https://supabase.com/) com um projeto criado

### Passo a passo

```bash
# 1. Clone o repositório
git clone https://github.com/carloshperruts/controle-financeiro.git
cd controle-financeiro

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
python main.py          # abre como app desktop
python main.py --web    # abre no navegador, como aplicação web
```

---

## 🧪 Testes automatizados

O projeto tem 60 testes com [pytest](https://pytest.org/) para a lógica que não depende de tela nem de banco: leitura de valores, cálculo e divisão de parcelas, fuso horário e isolamento do cliente do Supabase por sessão. Eles rodam em poucos segundos e não usam internet nem credenciais reais.

```bash
pip install pytest
python -m pytest
```

> A interface (Flet) e as chamadas reais ao Supabase ainda não têm testes automatizados; esses fluxos são conferidos manualmente.

---

## 📁 Estrutura do projeto

```
├── main.py                  # Ponto de entrada da aplicação
├── config/
│   └── supabase_client.py   # Criação do cliente Supabase (um por sessão) e categorias padrão
├── views/
│   ├── login_view.py        # Tela de login, cadastro e envio do e-mail de recuperação de senha
│   ├── dashboard_view.py    # Lógica e estado do dashboard
│   └── dashboard_ui.py      # Montagem dos componentes visuais do dashboard
├── components/
│   └── matrix_bg.py         # Componentes visuais reutilizáveis
├── utils/
│   └── helpers.py           # Funções auxiliares (sessão, valores, parcelas, fuso, exportação CSV/PDF)
├── assets/
│   └── exports/             # Relatórios exportados
├── tests/                   # Testes automatizados (pytest)
└── requirements.txt         # Dependências do projeto
```

---

## 🧠 Sobre o desenvolvimento

Este projeto é resultado de aprendizado autodidata, combinando estudo próprio com apoio de ferramentas de IA (Gemini e Claude) para acelerar pesquisa, revisar código e entender conceitos novos — da mesma forma que qualquer desenvolvedor hoje usa documentação, fóruns e pair programming. As decisões de arquitetura, a modelagem dos dados e a resolução de bugs de produção (autenticação, encoding de arquivos, tratamento de exceções) foram feitas e validadas por mim.

Estou em transição de carreira para desenvolvimento de software e busco oportunidades como estagiário ou desenvolvedor júnior. Feedback técnico é muito bem-vindo — se você é recrutador ou desenvolvedor e tiver sugestões sobre o código, fico feliz em conversar.

---

## 🔜 Próximos passos

- [ ] Melhorias e correções contínuas conforme bugs forem identificados no uso real
- [x] Testes automatizados da lógica de negócio (valores, parcelas, fuso horário e cliente por sessão)
- [ ] Testes da interface e das chamadas ao Supabase
- [ ] Concluir o fluxo de recuperação de senha (troca da senha pelo link do e-mail)
- [ ] Atualizações incrementais trazendo pequenos ajustes e melhorias ao longo do tempo

---

## 📬 Contato

**Desenvolvido por:** Carlos Perrut
**E-mail:** carloshperruts [at] gmail [dot] com
**LinkedIn:** [linkedin.com/in/carlos-henrique-perrut](https://www.linkedin.com/in/carlos-henrique-perrut)
**GitHub:** [github.com/carloshperruts](https://github.com/carloshperruts)

---

## 📄 Licença

Projeto pessoal para fins de estudo e portfólio.
