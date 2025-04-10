from fastapi import FastAPI, HTTPException, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import requests
import logging
from typing import Optional, Dict, List, Union
from contextlib import contextmanager
from fuzzywuzzy import fuzz
from db_config import get_db_connection
import os
from data.sinonimos import CARRERAS_SINONIMOS
from data.variaciones import CARRERAS_VARIACIONES
from data.carreras import LISTA_COMPLETA_CARRERAS
from data.horario import HORARIO_CARRERA
from datetime import datetime
from fastapi import APIRouter
import uuid
import base64

app = FastAPI()
router = APIRouter()

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://192.168.0.93:3000", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# API GEMINI
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "tu_api_key_de_gemini")
GEMINI_API_URL = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={GEMINI_API_KEY}"

class DocumentoCarrera(BaseModel):
    id: int
    nombre: str
    contenido: str  
    fecha_upload: datetime

class Message(BaseModel):
    message: str
    session_id: Optional[str] = None

class ChatMessage(BaseModel):
    role: str 
    content: str
    carrera_referencia: Optional[str] = None
    documentos: Optional[List[DocumentoCarrera]] = None

class ChatSession(BaseModel):
    session_id: str

class PreUsuarioCreate(BaseModel):
    nombre: str
    cedula: str
    correo: str
    celular: str
    carrera: str

@contextmanager
def get_db_cursor():
    """Manejador de contexto para cursores de base de datos"""
    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        yield cursor
        conn.commit()
    except Exception as e:
        if conn:
            conn.rollback()
        logger.error(f"Error de base de datos: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Error al acceder a la base de datos"
        )
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

def obtener_documentos_carrera(cursor, nombre_carrera: str) -> List[DocumentoCarrera]:
    """Obtiene todos los documentos asociados a una carrera por nombre"""
    try:
        # Primero obtenemos el ID de la carrera
        cursor.execute("""
            SELECT id_carrera FROM carrera 
            WHERE LOWER(nombre) LIKE LOWER(%s)
            LIMIT 1
        """, (f"%{nombre_carrera}%",))
        carrera_result = cursor.fetchone()
        
        if not carrera_result:
            return []

        id_carrera = carrera_result['id_carrera']

        # Luego obtenemos los documentos asociados
        cursor.execute("""
            SELECT id, nombre, contenido, fecha_upload
            FROM documentos
            WHERE id = %s
            ORDER BY fecha_upload DESC
        """, (id_carrera,))
        
        documentos = []
        for row in cursor.fetchall():
            # Asegurarnos de que el contenido existe antes de convertirlo
            contenido_base64 = base64.b64encode(row['contenido']).decode('utf-8') if row['contenido'] else None
            documentos.append(
                DocumentoCarrera(
                    id=row['id'],
                    nombre=row['nombre'],
                    contenido=contenido_base64,
                    fecha_upload=row['fecha_upload']
                )
            )
        return documentos
        
    except Exception as e:
        logger.error(f"Error al obtener documentos: {str(e)}")
        return []

def query_carrera(nombre_carrera: str) -> Optional[dict]:
    """Consulta información de carrera en la base de datos incluyendo documentos y horarios"""
    with get_db_cursor() as cursor:
        try:
            # Consulta información básica de la carrera
            cursor.execute("""
                SELECT c.*, p.descripcion
                FROM carrera c
                LEFT JOIN perfil_profesional p ON c.id_carrera = p.id_carrera
                WHERE LOWER(c.Nombre) LIKE LOWER(%s)
                LIMIT 1
            """, (f"%{nombre_carrera}%",))
            
            results = cursor.fetchall()
            if not results:
                return None
                
            carrera_data = results[0]
            
            # Obtiene documentos asociados
            documentos = obtener_documentos_carrera(cursor, nombre_carrera)
            
            # Obtiene horarios de la carrera
            horarios = HORARIO_CARRERA.get(carrera_data['nombre'].upper(), {})
            
            return {
                **carrera_data,
                "documentos": documentos,
                "horarios": horarios
            }
            
        except Exception as e:
            logger.error(f"Error en consulta de carrera: {str(e)}")
            return None

def detectar_carrera_solicitada(texto: str) -> Optional[str]:
    """Detecta carreras con variaciones y sinónimos"""
    texto = texto.lower()
    
    if any(palabra in texto for palabra in ["carreras", "disponibles", "ofrecen", "tienen", "qué estudiar", "qué carreras"]):
        return "LISTA_CARRERAS"
    
    for sinonimo, carrera in CARRERAS_SINONIMOS.items():
        if sinonimo in texto:
            return carrera
    
    for carrera, variaciones in CARRERAS_VARIACIONES.items():
        if carrera in texto:
            return carrera
        for variacion in variaciones:
            if variacion in texto:
                return carrera
    
    best_match = None
    highest_score = 0
    
    for carrera in CARRERAS_VARIACIONES.keys():
        score = fuzz.token_set_ratio(texto, carrera)
        if score > highest_score and score > 60:
            highest_score = score
            best_match = carrera
    
    return best_match

def generar_sugerencia(texto: str) -> str:
    texto = texto.lower()
    sugerencias = []
    
    if any(palabra in texto for palabra in ["sist", "comp", "info", "compu"]):
        sugerencias.append("¿Quizás te refieres a 'Ingeniería en Sistemas Inteligentes'?")
    if any(palabra in texto for palabra in ["dere", "abog", "ley"]):
        sugerencias.append("¿Quisiste decir 'Derecho'?")
    if any(palabra in texto for palabra in ["dent", "odon"]):
        sugerencias.append("¿Te refieres a 'Odontología'?")
    if any(palabra in texto for palabra in ["cont", "fina"]):
        sugerencias.append("¿Buscas información sobre 'Contabilidad y Finanzas'?")
    if any(palabra in texto for palabra in ["enferm", "cuidados"]):
        sugerencias.append("¿Te interesa la carrera de 'Enfermería'?")
    
    return " " + " ".join(sugerencias) if sugerencias else ""

def save_chat_message(session_id: str, message: ChatMessage):
    """Guarda un mensaje en el historial de chat"""
    with get_db_cursor() as cursor:
        cursor.execute(
            """
            INSERT INTO chat_history 
                (session_id, role, content, carrera_referencia)
            VALUES (%s, %s, %s, %s)
            """,
            (session_id, message.role, message.content, message.carrera_referencia)
        )

def get_chat_history(session_id: str, limit: int = 5) -> List[ChatMessage]:
    """Obtiene el historial de chat para una sesión"""
    with get_db_cursor() as cursor:
        cursor.execute(
            """
            SELECT role, content, carrera_referencia
            FROM chat_history
            WHERE session_id = %s
            ORDER BY timestamp DESC
            LIMIT %s
            """,
            (session_id, limit)
        )
        return [
            ChatMessage(
                role=row['role'],
                content=row['content'],
                carrera_referencia=row['carrera_referencia']
            )
            for row in cursor.fetchall()
        ]

def generate_prompt(user_message: str, db_data: Optional[dict], chat_history: List[ChatMessage] = None) -> str:
    """Genera el prompt contextualizado para Gemini con historial de chat"""
    base_context = """
Eres Sara, la asesora virtual de la Universidad Bolivariana del Ecuador. Tu estilo es profesional, cálido y detallado, brindando respuestas claras, precisas y acogedoras para que los usuarios se sientan escuchados y bien atendidos.

Tu misión:

Guiarlos con información relevante sobre carreras, beneficios y procesos de la universidad.

Destacar las ventajas de estudiar en la UBE:

Excelencia académica con profesores especializados.

Infraestructura moderna y ambientes de aprendizaje óptimos.

Oportunidades de prácticas y vinculación laboral.

Formación integral con valores sociales y compromiso comunitario.

Cuando pregunten por carreras:

Proporciona un listado organizado (por áreas o facultades).

Pregunta amablemente: "¿Te gustaría más detalles sobre alguna carrera en particular? Estoy aquí para ayudarte".

Recuerda:

Usa emojis para dar calidez y dinamismo (pero sin exceso).

Evita presentarte a menos que sea necesario (ya conocen tu nombre y rol).

Siempre agradece y motiva a seguir explorando la UBE.
Recuerda siempre basate en información de Ecuador.
Y finalle comentas los veneficios de la UBE.
"""
    
    history_context = ""
    if chat_history:
        history_context = "\n\nHistorial reciente de la conversación:\n"
        for msg in reversed(chat_history):  
            role = "Usuario" if msg.role == "user" else "Sara"
            history_context += f"{role}: {msg.content}\n"
    
    if db_data is None:
        return f"""{base_context}{history_context}
        
Usuario: {user_message}
Sara:"""
    
    # Sección para horarios
    horarios_info = ""
    if db_data.get('horarios'):
        horarios_info = "\n\nHorarios disponibles:\n"
        for nivel, info_horario in db_data['horarios'].items():
            horarios_info += f"- {nivel}: {info_horario.get('dias', '')} de {info_horario.get('horario', '')}\n"
    
    documentos_info = ""
    if db_data.get('documentos'):
        doc_names = [doc.nombre for doc in db_data['documentos']]
        documentos_info = f"\n\nDocumentos disponibles: {', '.join(doc_names)}. Puedes hacer clic para descargarlos."
    
    carrera_info = f"""
Información de la carrera {db_data.get('nombre', '')}:
- Modalidad: {db_data.get('modalidad', '')}
- Duración: {db_data.get('semestre', '')} semestres
- Costos:
  * Inscripción: ${db_data.get('inscripción', '')}
  * PRE: ${db_data.get('pre', '')}
  * Matrícula: ${db_data.get('matrícula', '')}
  * Cuotas mensuales: ${db_data.get('cuotas_mensuales', '')}
- Perfil profesional: {db_data.get('descripcion', '')}
{horarios_info}
{documentos_info}
"""
    
    return f"{base_context}{history_context}\n\n{carrera_info}\n\nUsuario: {user_message}\nSara:"

@app.post("/chat")
async def chat(message: Message):
    """Endpoint principal del chatbot con memoria"""
    try:
        logger.info(f"Mensaje recibido: {message.message}")
        
        session_id = message.session_id if message.session_id else str(uuid.uuid4())
        
        carrera_detectada = detectar_carrera_solicitada(message.message)
        user_msg = ChatMessage(
            role="user",
            content=message.message,
            carrera_referencia=carrera_detectada if carrera_detectada != "LISTA_CARRERAS" else None
        )
        save_chat_message(session_id, user_msg)
        
        chat_history = get_chat_history(session_id)
        
        if carrera_detectada == "LISTA_CARRERAS":
            carreras_formateadas = "\n- ".join(LISTA_COMPLETA_CARRERAS)
            response = {
                "response": f"¡Estas son las carreras que ofrecemos:\n\n- {carreras_formateadas}\n\n¿Te gustaría que te brinde más información sobre alguna en particular?",
                "session_id": session_id,
                "documentos": None
            }

            assistant_msg = ChatMessage(
                role="assistant",
                content=response["response"],
                carrera_referencia=None,
                documentos=None
            )
            save_chat_message(session_id, assistant_msg)
            return response
        
        if not carrera_detectada:
            sugerencia = generar_sugerencia(message.message)
            carreras_lista = "\n- ".join(LISTA_COMPLETA_CARRERAS)
            response = {
                "response": f"Lo siento, no entendí completamente tu consulta.{sugerencia}\n\n"
                          f"Estas son las carreras sobre las que puedo brindarte información:\n- {carreras_lista}\n\n"
                          f"¿Sobre cuál te gustaría conocer más?",
                "session_id": session_id,
                "documentos": None
            }
       
            assistant_msg = ChatMessage(
                role="assistant",
                content=response["response"],
                carrera_referencia=None,
                documentos=None
            )
            save_chat_message(session_id, assistant_msg)
            return response
        
        db_data = query_carrera(carrera_detectada)
        
        prompt = generate_prompt(message.message, db_data, chat_history)
        logger.info(f"Prompt generado: {prompt}")
        
        payload = {
            "contents": [{
                "parts": [{"text": prompt}]
            }],
            "generationConfig": {
                "temperature": 0.7,
                "topP": 0.9,
                "maxOutputTokens": 1024
            }
        }
        
        response = requests.post(
            GEMINI_API_URL,
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=30
        )
        response.raise_for_status()
      
        data = response.json()
        bot_response = data["candidates"][0]["content"]["parts"][0]["text"]
        
        response_data = {
            "response": bot_response,
            "session_id": session_id,
            "documentos": [
                {
                    "id": doc.id,
                    "nombre": doc.nombre,
                    "fecha_upload": doc.fecha_upload.isoformat()
                }
                for doc in db_data.get('documentos', [])
            ] if db_data else None,
            "horarios": db_data.get('horarios') if db_data else None
        }

        assistant_msg = ChatMessage(
            role="assistant",
            content=bot_response,
            carrera_referencia=carrera_detectada if carrera_detectada != "LISTA_CARRERAS" else None,
            documentos=db_data.get('documentos') if db_data else None
        )
        save_chat_message(session_id, assistant_msg)
        
        return response_data
        
    except requests.exceptions.RequestException as e:
        logger.error(f"Error en Gemini API: {str(e)}")
        raise HTTPException(
            status_code=502,
            detail="Error al comunicarse con el servicio de IA"
        )
    except Exception as e:
        logger.error(f"Error inesperado: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="Ocurrió un error al procesar tu mensaje"
        )

@app.get("/documentos/{id_documento}")
async def obtener_documento(id_documento: int):
    """Devuelve el documento directamente desde la base de datos"""
    with get_db_cursor() as cursor:
        try:
            cursor.execute("""
                SELECT nombre, contenido
                FROM documentos
                WHERE id = %s
                LIMIT 1
            """, (id_documento,))
            
            doc = cursor.fetchone()
            if not doc or not doc['contenido']:
                raise HTTPException(status_code=404, detail="Documento no encontrado o vacío")

            return Response(
                content=doc['contenido'],
                media_type="application/pdf",
                headers={
                    "Content-Disposition": f"inline; filename={doc['nombre'] or 'documento'}.pdf"
                }
            )
        except Exception as e:
            logger.error(f"Error al obtener documento: {str(e)}")
            raise HTTPException(
                status_code=500, 
                detail="Error al procesar documento"
            )

@router.post("/pre-registro")
async def crear_pre_registro(
    usuario: PreUsuarioCreate,
    request: Request
):
    try:
        registro_data = {
            **usuario.model_dump(),  
            "fecha_registro": datetime.now(),
            "origen": request.headers.get("origin", "desconocido"),
            "procesado": False
        }

        with get_db_cursor() as cursor:
            try:
                cursor.execute(
                    """
                    INSERT INTO pre_usuario (
                        nombre, cedula, correo, celular, carrera,
                        fecha_registro, origen, procesado
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                    RETURNING id, fecha_registro, carrera
                    """,
                    (
                        usuario.nombre,
                        usuario.cedula,
                        usuario.correo,
                        usuario.celular,
                        usuario.carrera,
                        registro_data["fecha_registro"],
                        registro_data["origen"],
                        registro_data["procesado"]
                    )
                )
                result = cursor.fetchone()

            except Exception as db_error:
                logger.error(f"Error al insertar registro: {str(db_error)}")
                if "duplicada" in str(db_error).lower():
                    cursor.execute(
                        "SELECT id, fecha_registro, carrera FROM pre_usuario WHERE cedula = %s LIMIT 1",
                        (usuario.cedula,)
                    )
                    result = cursor.fetchone()
                    if result:
                        return {
                            "mensaje": "Ya existe un registro con esta cédula",
                            "registro": {
                                "id": result["id"],
                                "fecha": result["fecha_registro"].isoformat(),
                                "carrera": result["carrera"]
                            },
                            "warning": "Se encontró un registro previo con esta cédula"
                        }
                raise HTTPException(
                    status_code=400,
                    detail="Error al procesar el registro. Por favor intente nuevamente."
                )

            perfil = None
            cursor.execute(
                """
                SELECT p.descripcion
                FROM carrera c
                JOIN perfil_profesional p ON c.id_carrera = p.id_carrera
                WHERE LOWER(c.nombre) = LOWER(%s)
                LIMIT 1
                """,
                (usuario.carrera,)
            )
            perfil = cursor.fetchone()

        return {
            "mensaje": "Pre-registro exitoso",
            "registro": {
                "id": result["id"],
                "fecha": result["fecha_registro"].isoformat(),
                "carrera": result["carrera"],
                "perfil_profesional": perfil["descripcion"] if perfil else "No disponible"
            },
            "next_steps": "Un asesor se pondrá en contacto contigo pronto"
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error inesperado: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="Error interno al procesar el registro"
        )

app.include_router(router)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        app, 
        host="0.0.0.0", 
        port=5000,
        log_level="info"
    )
