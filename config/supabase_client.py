import os
from supabase import create_client, Client

# Conexão centralizada do Supabase
# As credenciais vêm SEMPRE do ambiente (.env local ou variáveis do Render).
# Nunca deixe uma chave "escrita" aqui como valor reserva.
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    raise RuntimeError(
        "SUPABASE_URL e SUPABASE_KEY precisam estar definidas no .env (local) "
        "ou nas variáveis de ambiente do Render (produção)."
    )

def criar_cliente_supabase() -> Client:
    """
    Cria um cliente NOVO do Supabase.

    Cada sessão de usuário (cada aba/navegador conectado ao app) deve ter o
    seu próprio cliente. Um cliente guarda o token de quem fez login nele: se
    vários usuários compartilhassem o mesmo cliente, o último login
    sobrescreveria o token de todos os outros.
    """
    return create_client(SUPABASE_URL, SUPABASE_KEY)

# Categorias padrão utilizadas nos formulários e filtros
CATEGORIAS = [
    "Alimentação",
    "Moradia",
    "Transporte",
    "Saúde & Bem-Estar",
    "Educação",
    "Lazer & Viagens",
    "Assinaturas & Serviços",
    "Compras & Vestuário",
    "Dívidas & Empréstimos",
    "Investimentos & Reserva",
    "Rendimento & Salário",
    "Outros"
]