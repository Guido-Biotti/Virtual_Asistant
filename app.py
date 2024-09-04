import vertexai
from langchain_google_vertexai import VertexAI
from google.oauth2 import service_account
from langchain_core.prompts import PromptTemplate
from langchain.chains import LLMChain
import os
import re
import subprocess
import webbrowser
import pyttsx3
import json

path = os.path.expanduser('~')
path = path.replace("\\","/")
path = path+"/OneDrive/Escritorio/"

try:
    with open('vertex.json', 'r') as f:
        vertex = json.load(f)

    PROJECT_ID = vertex['project_id']
    CREDENTIALS = service_account.Credentials.from_service_account_file('vertex.json')

except FileNotFoundError:
    print("File 'vertex.json' not found.")
    CREDENTIALS = None
except json.JSONDecodeError:
    print("Error parsing JSON data in 'vertex.json'.")
    CREDENTIALS = None
except Exception as e:
    print("An unexpected error occurred:", e)
    CREDENTIALS = None

if CREDENTIALS:
    vertexai.init(project=PROJECT_ID, location="us-central1", credentials=CREDENTIALS)
else:
    print("CREDENTIALS not defined. vertexai.init() will not be executed.")

llm = VertexAI(model_name= "text-bison")

def obtener_raices(verbos):
    # Diccionario de terminaciones comunes para cada idioma
    terminaciones = ['ar', 'er', 'ir', 'e', 'ed', 'ing', 's']
    
    # Asegurar que 'verbos' sea una lista
    if isinstance(verbos, str):
        verbos = [verbos]
    
    raices = []
    
    for verbo in verbos:
        raiz = verbo
        for terminacion in terminaciones:
            if verbo.endswith(terminacion):
                raiz = verbo[:-len(terminacion)]
                break
        raices.append(raiz)
    
    return raices

def palabras_clave(task, palabras):
    if any(palabra.endswith(terminacion) for palabra in palabras for terminacion in ['ar', 'er', 'ir', 'e', 'ed', 'ing', 's']):
        raices = obtener_raices(palabras)

    # Convertir la tarea a minúsculas y eliminar caracteres no alfabéticos
    task_normalizada = re.sub(r'[^a-zA-Záéíóúñü]', ' ', task.lower())
    
    # Dividir en palabras individuales
    palabras = task_normalizada.split()
    
    # Verificar si alguna palabra contiene las raíces
    for palabra in palabras:
        for raiz in raices:
            if raiz in palabra:
                return True
    
    return False

def do_task(task):
    prompt = PromptTemplate(
        input_variables=["task"],
        template="""
        You are an advanced virtual assistant capable of managing documents and applications. 
        You should continue speaking in the last language the user used in previous interactions, either English or Spanish.

        Do the next task: {task} 
        Politely ask for the name of the folder or document they are referring to in the same language they were using, if that's the case. 
        Make sure to keep your responses polite and respectful at all times.
        """
    )
    # formateo la entrada del modelo
    formatted_prompt = prompt.format(task=task)
    # obtengo la respuesta del modelo
    response = llm.invoke(formatted_prompt)
    # elimino el salto de línea final
    response = response.strip()
    return response

def get_response(task, name, completion = False):
    prompt = PromptTemplate(
        input_variables=["task", "name", "completion"],
        template="""
        You are an advanced virtual assistant with the ability to answer questions about yourself, manage documents or applications, and add events to the user's calendar. 
        Your primary function is to assist {name} in tasks related to their PC, but your capabilities will expand over time with additional functionalities. 
        You can read and respond in English and Spanish. If addressed in one of these languages, reply in the same language. 
        If you receive a message in a language other than these, such as French, politely indicate that you do not understand.
        Always remain polite and respectful in your interactions.

        Knowing this, please complete the next task: {task}

        Also if they ever want to stop the conversation and they don't know how you explain them how to do it. To do it they should say any of the next words: 'goodbye', 'exit', 'bye', 'quit', 'stop', 'adios', 'chau', 'salir', 'hasta luego' or 'cerrar'.
        It should be exactly one of these words, without any additional words or characters tho they can be in capital or lowercase letters. But don't be to pushy about it, if they want to continue the conversation you should let them do it.

        If they want to do something lke create a folder or document you should ask them for the name of the folder or document they want to create in the same language they were using.
        You should never give them tips to do it for themselves, that's your whole purpose to help them doing their things.

        If {completion} is {True} you have just completed the task. Let {name} know that the task has been successfully completed and ask if they need any further assistance.
        """
    )

    # formateo la entrada del modelo
    formatted_prompt = prompt.format(task=task, name=name, completion=completion)
    # obtengo la respuesta del modelo
    response = llm.invoke(formatted_prompt)
    # elimino el salto de línea final
    response = response.strip()
    return response

def crear_carpeta(nombre):
    name = input(f'{nombre}: ')
    try:
        os.mkdir(path+name)
        return f'Folder {name} created successfully.'
    except FileExistsError:
        return f'Folder {name} already exists.'
    except Exception as e:
        return f'Error creating folder {name}: {e}'
def crear_documento(nombre):
    name = input(f'{nombre}: ')
    try:
        open(path+name, 'w+')
        return f'Document {name} created successfully.'
    except FileExistsError:
        return f'Document {name} already exists.'
    except Exception as e:
        return f'Error creating document {name}: {e}'
   

def main():
    nombre = input('Guido_AI: How should I call you? // Como debería llamarte?\n...: ')
    #print(f'Guido_AI: Hello, {nombre}! How can I help you today? // Hola, {nombre}! En qué puedo ayudarte hoy?\n')
    response = get_response('Saluda y pregunta que necesita el usuario usando su nombre en ambos idiomas separados por una barra /', nombre)
    print(f'Guido_AI: {response}')
    while True:
        query = input(f'{nombre}: ')
        if palabras_clave(query, ['crear', 'create']):
            if palabras_clave(query, ['carpeta', 'folder']):
                response = get_response(query, nombre)
                print(f'Guido_AI: {response}')
                crear_carpeta(nombre)
            elif palabras_clave(query, ['documento', 'document', 'archivo', 'file']):
                response = get_response(query, nombre)
                print(f'Guido_AI: {response}')
                crear_documento(nombre)
            response = get_response(query, nombre, True)
            print(f'Guido_AI: {response}')
        else:       
            response = get_response(query, nombre)
            print(f'Guido_AI: {response}')
        if query.lower() in ['goodbye', 'exit', 'bye', 'quit', 'stop', 'adios', 'chau', 'salir', 'hasta luego', 'cerrar']:
            break

if __name__ == '__main__':
    main()