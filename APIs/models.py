from sqlalchemy import create_engine, Column, Integer, String, Boolean, Float, ForeignKey
from sqlalchemy.orm import declarative_base, relationship

# Criação de conexão de BD
db = create_engine("sqlite:///base.db")

# Criar a base de BD
base = declarative_base()

# Criar as tabelas
class Usuario(base):
    __tablename__ = "usuarios"

    id = Column("id", Integer, nullable=False, primary_key=True, autoincrement=True)
    nome = Column("nome", String)
    email = Column("email", String, nullable=False, unique=True)  
    senha = Column("senha", String)
    ativo = Column("ativo", Boolean, default=True)
    admin = Column("admin", Boolean, default=False)

    def __init__(self, nome, email, senha, ativo=True, admin=False):
        self.nome = nome
        self.email = email
        self.senha = senha
        self.ativo = ativo
        self.admin = admin


class Pedido(base):
    __tablename__ = "pedidos"
    
    STATUS_PEDIDO = (
        ("pendente", "Pendente"),
        ("processando", "Processando"),
        ("cancelado", "Cancelado"),
        ("concluido", "Concluido")
    )
      
    id = Column("id", Integer, nullable=False, primary_key=True, autoincrement=True)
    status = Column("status", String, default="pendente")
    usuario_id = Column("usuario_id", ForeignKey("usuarios.id")) 
    preco = Column("preco", Float, default=0.0)
    item = relationship("Item", cascade = "all, delete")
   
    def __init__(self, usuario_id, status="pendente", preco=0.0):
        self.usuario_id = usuario_id
        self.status = status
        self.preco = preco

    def calcular_preco(self):
        preco_total = 0.0
        for item in self.item:
            preco_item = item.quantidade * item.preco_unitario
            preco_total += preco_item  
        self.preco = preco_total

class Item(base):
    __tablename__ = "itens"
    
    id = Column("id", Integer, nullable=False, primary_key=True, autoincrement=True)
    quantidade = Column("quantidade", Integer, default=1)
    sabor = Column("sabor", String)
    tamanho = Column("tamanho", String)
    preco_unitario = Column("preco_unitario", Float)
    pedido_id = Column("pedido_id", ForeignKey("pedidos.id"))
    
    def __init__(self, quantidade, sabor, tamanho, preco_unitario, pedido_id):
        self.quantidade = quantidade
        self.sabor = sabor
        self.tamanho = tamanho
        self.preco_unitario = preco_unitario
        self.pedido_id = pedido_id  


# Execução de criação dos metadados
base.metadata.create_all(db)