import os
from supabase import create_client, Client

# Conexão centralizada do Supabase
SUPABASE_URL = os.environ.get("SUPABASE_URL", "https://vmkkdenzkoqklvlulajo.supabase.co")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY", "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InZta2tkZW56a29xa2x2bHVsYWpvIiwicm9sZSI6ImFub24iLCJpYXQiOjE3ODgzNzg4NDIsImV4cCI6MjEwMzk1NDg0Mn0.vdCNnUnrRCQJuBKme-YYm9FqnyyV_BZ3Wh077uckxYA")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

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