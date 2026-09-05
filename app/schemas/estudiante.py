# 2. La Capa de Validación (El Schema)
# Esta capa es el escudo de seguridad. Utiliza Pydantic para asegurar 
# que la información que viaja por la API REST tenga el formato exacto 
# que se necesita antes de tocar la base de datos.


from pydantic import BaseModel


# 1. Propiedades comunes que siempre necesitaremos
class EstudianteBase(BaseModel):
    nombre: str
    matricula: str

# 2. Lo que exigimos cuando hacen el POST (Crear)
class EstudianteCreate(EstudianteBase):
    pass

# 3. Lo que devolvemos como respuesta HTTP (Response)
class EstudianteResponse(EstudianteBase):
    id: int
    uid_rfid: str | None = None

    class Config:
        # Permite que Pydantic lea directamente del modelo de SQLAlchemy
        from_attributes = True