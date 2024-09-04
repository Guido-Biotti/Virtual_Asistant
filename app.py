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

def palabras_clave(task, raices):
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

def get_response(task, name):
    prompt = PromptTemplate(
        input_variables=["task", "name"],
        template="""
        You are an advanced virtual assistant with the ability to answer questions about yourself, manage documents or applications, and add events to the user's calendar. 
        Your primary function is to assist {name} in tasks related to their PC, but your capabilities will expand over time with additional functionalities. 
        You can read and respond in English and Spanish. If addressed in one of these languages, reply in the same language. 
        If you receive a message in a language other than these, such as French, politely indicate that you do not understand.
        Always remain polite and respectful in your interactions.

        Knowing this, please complete the next task: {task}
        """
    )
    # formateo la entrada del modelo
    formatted_prompt = prompt.format(task=task, name=name)
    # obtengo la respuesta del modelo
    response = llm.invoke(formatted_prompt)
    # elimino el salto de línea final
    response = response.strip()
    return response

def crear_carpeta(nombre):
    do_task('Create a folder')
    name = input(f'{nombre}: ')
    try:
        os.mkdir(name)
        return f'Folder {name} created successfully.'
    except FileExistsError:
        return f'Folder {name} already exists.'
    except Exception as e:
        return f'Error creating folder {name}: {e}'
def crear_documento(nombre):
    do_task('Create a document')
    name = input(f'{nombre}: ')
    try:
        open(name, 'w+')
        return f'Document {name} created successfully.'
    except FileExistsError:
        return f'Document {name} already exists.'
    except Exception as e:
        return f'Error creating document {name}: {e}'
   

def main():
    nombre = input('Guido_AI: How should I call you? // Como debería llamarte?\n...: ')
    print(f'Guido_AI: Hello, {nombre}! How can I help you today? // Hola, {nombre}! En qué puedo ayudarte hoy?\n')
    while True:
        query = input(f'{nombre}: ')

        if palabras_clave(query, ['crear', 'create']):
            if palabras_clave(query, ['carpeta', 'folder']):
                crear_carpeta(nombre)
            elif palabras_clave(query, ['documento', 'document', 'archivo', 'file']):
                crear_documento(nombre)
        response = get_response(query, nombre)
        print(f'Guido_AI: {response}')
        if query.lower() in ['goodbye', 'exit', 'bye', 'quit', 'stop', 'adios', 'chau', 'salir', 'hasta luego', 'cerrar']:
            break

if __name__ == '__main__':
    main()