import json
import boto3
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select

s3 = boto3.client('s3')

def lambda_handler(event, context):
    # Descarga el archivo clientes.json del bucket S3
    bucket_name = 'selenium-enroller'
    file_name = 'clientes.json'
    s3.download_file(bucket_name, file_name, '/tmp/' + file_name)
    
    # Abre el archivo clientes.json y lee los datos
    with open('/tmp/' + file_name, 'r') as f:
        clientes = json.load(f)
    
    # Configura el driver de Chrome
    options = webdriver.ChromeOptions()
    options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    driver = webdriver.Chrome(options=options)
    
    # Navega a la página web
    driver.get("https://servicios.comedica.com.sv/ReportaCompraTC-war/")
    
    # Recorre la lista de clientes y envía el formulario para cada uno
    for cliente in clientes:
        nombre = cliente['nombre']
        email = cliente['email']
        telefono = cliente['telefono']
        monto = cliente['monto']
        tipo_tarjeta = cliente['tipo_tarjeta']
        
        # Encuentra los campos del formulario y los completa
        nombre_input = driver.find_element(By.NAME, "nombre")
        nombre_input.send_keys(nombre)
        email_input = driver.find_element(By.NAME, "email")
        email_input.send_keys(email)
        telefono_input = driver.find_element(By.NAME, "telefono")
        telefono_input.send_keys(telefono)
        monto_input = driver.find_element(By.NAME, "monto")
        monto_input.send_keys(monto)
        select = Select(driver.find_element(By.NAME, "tipo_tarjeta"))
        select.select_by_value(tipo_tarjeta)
        
        # Envía el formulario
        submit_button = driver.find_element(By.NAME, "submit")
        submit_button.click()
        
        # Limpia los campos del formulario para el siguiente cliente
        nombre_input.clear()
        email_input.clear()
        telefono_input.clear()
        monto_input.clear()
    
    # Cierra el navegador
    driver.quit()
    
    # Retorna la respuesta
    response = {
        'statusCode': 200,
        'body': json.dumps({'message': 'Formularios enviados correctamente'})
    }
    return response
