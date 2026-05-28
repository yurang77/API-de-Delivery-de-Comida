from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from dependencias import pegar_sessao, verificar_token
from schemas import PedidoSchema, ItemPedidoSchema, ResponsePedidoSchema
from models import Pedido, Usuario, Item
from typing import List

order_router = APIRouter(prefix="/pedidos", tags=["pedidos"], dependencies = [Depends(verificar_token)])

@order_router.get("/")
async def pedidos():
    return {"mensagem": "Voce acedeu a lista de pedidos"}

@order_router.post("/pedido")
async def criar_pedido(pedido_schema: PedidoSchema, session: Session = Depends(pegar_sessao)):
    novo_pedido = Pedido(
        usuario_id=pedido_schema.id_usuario,  # ← modelo espera usuario_id, não id_usuario
    )
    
    session.add(novo_pedido)
    session.commit()
    session.refresh(novo_pedido)
    
    return {"mensagem": "Pedido criado com sucesso", "pedido": novo_pedido.id}

@order_router.post("/pedido/cancelar/{id_pedido}")
async def cancelar_pedido(id_pedido: int, session: Session = Depends(pegar_sessao), usuario: Usuario = Depends(verificar_token)):
    #usuario.admin = True
    #usuario.id = pedido.usuario
    
    pedido = session.query(Pedido).filter(Pedido.id == id_pedido).first()
    if not pedido:
        raise HTTPException(status_code=404, detail= "Pedido nao encontrado")
    if not usuario.admin and usuario.id!= pedido.usuario_id:
        raise HTTPException(status_code=402, detail = "Voce nao tem permissao para cancelar este pedido")
    else:
        pedido.status = "CANCELADO"
        session.commit()
        return {"mensagem": "Pedido cancelado com sucesso",
               "pedido": pedido.id
           }
        
@order_router.get("/listar")
async def listar_pedidos(session: Session = Depends(pegar_sessao), usuario: Usuario = Depends(verificar_token)):
    if not usuario.admin:
        raise HTTPException(status_code = 403 , detail = "Voce nao tem permissao para acessar esta lista")
    else:
        pedidos = session.query(Pedido).all()
        return {"pedidos": pedidos}
    
    
@order_router.post("/pedido/adicionar-item/{id_pedido}")
async def adicionar_item_pedido(id_pedido: int,
                                item_pedido_schema: ItemPedidoSchema,
                                session: Session = Depends(pegar_sessao),
                                usuario : Usuario = Depends(verificar_token)):
     
    pedido = session.query(Pedido).filter(Pedido.id == id_pedido).first()
    if not pedido:
        raise HTTPException(status_code=400, detail = "Pedido nao encontrado")
    if not usuario.admin and usuario.id != pedido.usuario_id:
        raise HTTPException(status_code = 403, detail = "Nao tem acesso autorizado")
    item_pedido = Item(item_pedido_schema.quantidade, item_pedido_schema.sabor,
                       item_pedido_schema.tamanho,
                       item_pedido_schema.preco_unitario,
                       id_pedido)
    session.add(item_pedido)
    pedido.calcular_preco()
    session.commit()
    return {
        "mensagem": "Item adicionado ao pedido com sucesso",
        "preco_pedido": pedido.preco,
        "item": item_pedido.id
    }
    
@order_router.post("/pedido/remover-item/{id_item}")    
async def remover_item_pedido(
    id_item: int,
    session: Session = Depends(pegar_sessao),
    usuario: Usuario = Depends(verificar_token)
):
    # 1. Busca o item PRIMEIRO
    item = session.query(Item).filter(Item.id == id_item).first()
    
    if not item:
        raise HTTPException(status_code=404, detail="Item não encontrado")

    pedido = session.query(Pedido).filter(Pedido.id == item.pedido_id).first()
    if not pedido:
        raise HTTPException(status_code=404, detail="Pedido não encontrado")

    if not usuario.admin and usuario.id != pedido.usuario_id:
        raise HTTPException(status_code=403, detail="Não tem acesso autorizado")
    
    item_id_removido = item.id
    
    session.delete(item)
    session.flush()             
    session.refresh(pedido)      
    pedido.calcular_preco()      
    session.commit()
    
    return {
        "mensagem": "Item removido do pedido com sucesso",
        "preco_pedido": pedido.preco,
        "item_id": item_id_removido
    }

    
@order_router.post("/pedido/finalizar/{id_pedido}")
async def finalizar_pedido(
    id_pedido: int,
    session: Session = Depends(pegar_sessao),
    usuario: Usuario = Depends(verificar_token)
):
    pedido = session.query(Pedido).filter(Pedido.id == id_pedido).first()
    if not pedido:
        raise HTTPException(status_code=404, detail="Pedido nao encontrado")
    if pedido.status in ("FINALIZADO", "CANCELADO"):
        raise HTTPException(status_code=400, detail=f"Pedido ja {pedido.status.lower()}")
    if not usuario.admin and usuario.id != pedido.usuario_id:
        raise HTTPException(status_code=403, detail="Voce nao tem permissao para finalizar este pedido")
    
    pedido.status = "FINALIZADO"
    session.commit()
    return {"mensagem": "Pedido finalizado com sucesso", "pedido": pedido.id}
        
@order_router.get("/visualizar/{id_pedido}")
async def visualizar_opedido(id_pedido: int, session: Session = Depends(pegar_sessao), usuario: Usuario = Depends(verificar_token)):
    pedido = session.query(Pedido).filter(Pedido.id == id_pedido).first()
    if not pedido:
        raise HTTPException(status_code = 404, detail ="Pedido nao encontrado")
    if not usuario.admin and usuario.id != pedido.usuario_id:
        raise HTTPException(status_code = 403, detail = "Acesso negado")
    else:
        return {"quantidade_itens_pedido": len(pedido.item),
                "preco_total_pedido": pedido.preco,
                "status_pedido": pedido.status,
                "itens": pedido.item}

@order_router.get("/listar/pedidos-usuario", response_model = List[ResponsePedidoSchema])
async def listar_pedidos(session: Session = Depends(pegar_sessao), usuario: Usuario = Depends(verificar_token)):
    pedidos = session.query(Pedido).filter(Pedido.usuario_id == usuario.id).all()
    return pedidos
        