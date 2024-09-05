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

def get_response(task, name, completion = False, first_time = False, language = True, mod = False):
    
    base_template="""
        You are an advanced virtual assistant with the ability to answer questions about yourself, manage documents or applications, and add events to the user's calendar. 
        Your primary function is to assist {name} in tasks related to their PC, but your capabilities will expand over time with additional functionalities. 
        You can read and respond in English and Spanish. If addressed in one of these languages, reply in the same language. 
        If you receive a message in a language other than these, such as French, politely indicate that you do not understand.
        Always remain polite and respectful in your interactions.

        Knowing this, please complete the next task: {task}
        """

    if first_time:
        first_time_message = """First of all greet them. Then let them konw that if they ever want to stop the conversation and they don't know how you explain them how to do it. To do it they should say any of the next words: 'goodbye', 'exit', 'bye', 'quit', 'stop', 'adios', 'chau', 'salir', 'hasta luego' or 'cerrar'.
        It should be exactly one of these words, without any additional words or characters tho they can be in capital or lowercase letters."""
        base_template += first_time_message

    else:
        base_template += "Don't greet them anymore you already did it once."
    
    if mod:
        mod_message = """If they want to do something lke create or modify a folder or document you should ask them for the name of the folder or document they want to create/modify in the same language they were using.
        You should never give them tips to do it for themselves."""
        base_template += mod_message

    if completion:
        completion_message = "The task has been successfully completed. Let {name} know and ask if they need any further assistance."
        base_template += completion_message

    if not language:
        language_message = """ Remember that everything you say you should say it in both languages (English and Spanish) separated by a double slash (//).
        First you should say everything in english then the double slash and then the same thing in spanish. """
        base_template += language_message

    prompt = PromptTemplate(
        input_variables=["task", "name"],
        template= base_template
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
        return 1
    except FileExistsError:
        return 0
    except Exception as e:
        return -1
def crear_documento(nombre):
    name = input(f'{nombre}: ')
    try:
        a= open(path+name, 'r')
        a.close(path+name)
        return 0
    except FileNotFoundError:
        open(path+name, 'w+')
        return 1
    except Exception as e:
        return -1
    
def mod_nombre(nombre, new_name):
    try:
        os.rename(path + nombre, path + new_name)
        return 1
    except FileNotFoundError:
        return 0
    except FileExistsError:
        return -1
    
def mod_documento(nombre):
    try:
        open(path+nombre, 'r+')
        response = get_response("Ask the user what would he like to add to the document", nombre, language=False, mod=True)
        print(f'Guido_AI: {response}')
        content = input(f'{nombre}: ')
        with open(path+nombre, 'a') as f:
            f.write(content)
        return 1
    except FileNotFoundError:
        return 0
    except Exception as e:
        return -1
   

def main():
    nombre = input('Guido_AI: How should I call you? // Como debería llamarte?\n...: ')
    response = get_response('Saluda y pregunta que necesita el usuario usando su nombre en ambos idiomas separados por una barra /', nombre, first_time = True, language=False)
    print(f'Guido_AI: {response}')
    while True:
        query = input(f'{nombre}: ')
        if palabras_clave(query, ['crear', 'create']):
            mod = True
            if palabras_clave(query, ['carpeta', 'folder']):
                response = get_response(query, nombre, mod=mod)
                print(f'Guido_AI: {response}')
                resp = crear_carpeta(nombre)
            elif palabras_clave(query, ['documento', 'document', 'archivo', 'file']):
                response = get_response(query, nombre, mod=mod)
                print(f'Guido_AI: {response}')
                resp = crear_documento(nombre)
            if resp == 1:
                response = get_response(query, nombre, completion=True)
            elif resp == 0:
                response = get_response("Let the user know the creation didn't happen because the file/folder already exists. And ask if they want to modify it instead", nombre, language=False)
            else:
                response = get_response("Let the user know the creation didn't happen because of an error. And ask if they want to try again", nombre, language=False)
            print(f'Guido_AI: {response}')
        
        elif palabras_clave(query, ['cambiar', 'modificar', 'modify', 'change']):
            mod = True
            response = get_response("Ask the user what's the name of the new folder/ file they want to create", nombre, language=False, mod=mod)
            print(f'Guido_AI: {response}')
            new_name = input(f'{nombre}: ')
            if palabras_clave(query, ['nombre', 'name']):
                response = get_response(query, nombre, mod=mod)
                print(f'Guido_AI: {response}')
                resp = mod_nombre(nombre, new_name)
            elif palabras_clave(query, ['documento', 'document', 'archivo', 'file']):
                response = get_response(query, nombre, mod=mod)
                print(f'Guido_AI: {response}')
                resp = mod_documento(nombre)
            if resp == 1:
                response = get_response(query, nombre, completion=True)
            elif resp == 0:
                response = get_response("Let the user know the modification didn't happen because the file/folder doesn't exist. And ask if they want to create it instead", nombre, language=False)
            else:
                response = get_response("Let the user know the modification didn't happen because of an error. And ask if they want to try again", nombre, language=False)
            print(f'Guido_AI: {response}')

        else:       
            response = get_response(query, nombre)
            print(f'Guido_AI: {response}')
        if query.lower() in ['goodbye', 'exit', 'bye', 'quit', 'stop', 'adios', 'chau', 'salir', 'hasta luego', 'cerrar']:
            break

if __name__ == '__main__':
    main()