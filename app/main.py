from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from passlib.hash import bcrypt
from jose import jwt
import os

# Configuración básica
DATABASE_URL = os.getenv("DATABASE_URL")
JWT_SECRET = os.getenv("JWT_SECRET", "supersecreto")

# Configurar conexión SQLAlchemy
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

app = FastAPI(title="TECHO API", version="0.2.0")

# Modelo Pydantic para login
class LoginData(BaseModel):
    correo: str
    contrasena: str

@app.get("/")
def root():
    return {"ok": True, "service": "TECHO API", "routes": ["/", "/health", "/auth/login"]}

@app.get("/health")
def health():
    return {"ok": True}

@app.post("/auth/login")
def login(data: LoginData):
    """Verifica usuario y contraseña"""
    db = SessionLocal()
    try:
        # Busca usuario por correo
        q = text("SELECT id_usuario, correo, contrasena_hash, nombre, apellido FROM usuario WHERE correo = :correo")
        result = db.execute(q, {"correo": data.correo}).fetchone()
        if not result:
            raise HTTPException(status_code=401, detail="Usuario no encontrado")

        # Compara contraseñas
        contrasena_hash = result.contrasena_hash
        if not bcrypt.verify(data.contrasena, contrasena_hash):
            raise HTTPException(status_code=401, detail="Contraseña incorrecta")

        # Genera token JWT
        token = jwt.encode({"sub": result.correo}, JWT_SECRET, algorithm="HS256")

        return {
            "ok": True,
            "token": token,
            "usuario": {
                "id": result.id_usuario,
                "nombre": result.nombre,
                "apellido": result.apellido,
                "correo": result.correo
            }
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()
