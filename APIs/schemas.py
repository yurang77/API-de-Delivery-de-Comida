from pydantic import BaseModel, field_validator
from typing import Optional, List

class UsuarioSchema(BaseModel):
    nome: str
    email: str
    ativo: Optional[bool] = True
    senha: str
    

    @field_validator("senha")
    @classmethod
    def senha_max_72_bytes(cls, v):
        if len(v.encode("utf-8")) > 72:
            raise ValueError("A senha não pode ter mais de 72 bytes")
        return v
    admin: Optional[bool] = False
    
    class Config:
        from_attributes = True

class PedidoSchema(BaseModel):
    id_usuario: int
    descricao: str
    valor: float
    
    class Config:
        from_attributes = True

class LoginSchema(BaseModel):
    email: str
    senha: str
    
    class Config:
        from_attributes = True

class ItemPedidoSchema(BaseModel):
    quantidade: int
    sabor: str
    tamanho: str
    preco_unitario: float
    
    
    class Config:
        from_attributes = True

class ResponsePedidoSchema(BaseModel):
    id: int
    status: str
    preco: float
    item: List[ItemPedidoSchema]
    
    class Config:
        from_attributes = True