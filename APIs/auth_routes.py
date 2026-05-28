from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from fastapi.security import OAuth2PasswordRequestForm
from auth import bcrypt_context
from dependencias import pegar_sessao, verificar_token
from main import ACCESS_TOKEN_EXPIRE_MINUTES, SECRET_KEY, ALGORITHM
from models import Usuario
from schemas import UsuarioSchema, LoginSchema
from jose import jwt, JWTError
from datetime import datetime, timedelta, timezone


auth_router = APIRouter(prefix="/auth", tags=["auth"])

def criar_token(id_usuario, duracao_token=ACCESS_TOKEN_EXPIRE_MINUTES):
    data_expiracao = datetime.now(timezone.utc) + timedelta(minutes=int(duracao_token))
    dic_informacao={"sub": str(id_usuario), "exp": data_expiracao}
    jwt_codificado = jwt.encode(dic_informacao, SECRET_KEY,ALGORITHM)
    return jwt_codificado

def autenticar_usuario(email, senha, session):
    usuario = session.query(Usuario).filter(Usuario.email == email).first()
    
    if not usuario:
        return False
    elif not bcrypt_context.verify(senha, usuario.senha): 
        return False
    
    return usuario

@auth_router.get("/")
async def home():
    """
    Essa é a rota de autenticação
    """
    return {"mensagem": "Esta é a rota de autenticação", "autenticado": False}


@auth_router.post("/criar_conta")
async def criar_conta(
    usuario_schema: UsuarioSchema,
    session: Session = Depends(pegar_sessao)
):
    # Verifica se o email já existe
    utilizador = (
        session.query(Usuario)
        .filter(Usuario.email == usuario_schema.email)
        .first()
    )

    if utilizador:
        raise HTTPException(
            status_code=400,
            detail="Já existe utilizador com este email"
        )

    # Bcrypt limita senhas a 72 bytes — truncamos para evitar crash
    senha_truncada = usuario_schema.senha[:72]
    senha_criptografada = bcrypt_context.hash(senha_truncada)

    novo_utilizador = Usuario(
        nome=usuario_schema.nome,
        email=usuario_schema.email,
        senha=senha_criptografada,
        ativo=usuario_schema.ativo,
        admin=usuario_schema.admin
    )

    session.add(novo_utilizador)

    try:
        session.commit()
        session.refresh(novo_utilizador)
    except Exception:
        session.rollback()
        raise HTTPException(
            status_code=500,
            detail="Erro ao gravar no banco de dados"
        )

    return {
        "mensagem": "Conta criada com sucesso",
        "email": novo_utilizador.email,
        "id": novo_utilizador.id
    }
    
#login -> verificar email e senha, retornar token ou mensagem de erro
@auth_router.post("/login")
async def login(login_schema: LoginSchema, session: Session = Depends(pegar_sessao)):
    usuario = autenticar_usuario (login_schema.email, login_schema.senha, session)
    if not usuario:
        raise HTTPException(status_code=400, detail= "Email ou senha incorretos ou usuário não existe")
    else:
        access_token = criar_token(usuario.id)
        refresh_token = criar_token(usuario.id, duracao_token=timedelta(days=7).total_seconds() / 60)  # Token de refresh com duração de 7 dias
        return {"access_token": access_token, 
                "refresh_token": refresh_token,
                "token_type": "bearer"  }
        
@auth_router.post("/login-form")
async def login_form(dados_formulario: OAuth2PasswordRequestForm = Depends(), session: Session = Depends(pegar_sessao)):
    usuario = autenticar_usuario (dados_formulario.username, dados_formulario.password, session)
    if not usuario:
        raise HTTPException(status_code=400, detail= "Email ou senha incorretos ou usuário não existe")
    else:
        access_token = criar_token(usuario.id)
        refresh_token = criar_token(usuario.id, duracao_token=timedelta(days=7).total_seconds() / 60)  # Token de refresh com duração de 7 dias
        return {"access_token": access_token, 
                "token_type": "bearer"  }
        
@auth_router.get("/refresh")
async def use_refresh_token(usuario: Usuario = Depends(verificar_token)):
    access_token = criar_token(usuario.id)
    
    return {"access_token": access_token, 
            "token_type": "Bearer"}