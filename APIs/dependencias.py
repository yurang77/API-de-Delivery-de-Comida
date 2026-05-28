from models import db
from sqlalchemy.orm import sessionmaker, Session
from main import SECRET_KEY, ALGORITHM, oauth2_schema
from fastapi import Depends, HTTPException
from jose import jwt, JWTError
from models import Usuario

def pegar_sessao():
    try:
        Session= sessionmaker(bind=db)
        session=Session()
        yield session
    finally:
        session.close()  

def verificar_token(token: str = Depends(oauth2_schema), session: Session = Depends(pegar_sessao)):
    try:
        dic_info=jwt.decode(token, SECRET_KEY, ALGORITHM)
        usuario_id = int(dic_info.get("sub"))
    except JWTError as erro:
        print(erro)
        raise HTTPException(status_code=401, detail="Token inválido")

    usuario = session.query(Usuario).filter(Usuario.id == usuario_id).first()
    if not usuario:
        raise HTTPException(status_code=401, detail="Usuário não encontrado")
    
    return usuario