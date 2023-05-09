import json, datetime, locale, boto3, os
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select

s3 = boto3.client('s3')

def lambda_handler(event, context):
    # Seteando locale a espanol
    locale.setlocale(locale.LC_TIME, 'es_ES.UTF-8')
    # Obteniendo mes y anio actual en mayuscula para busqueda por texto
    current_mont_and_year = datetime.datetime.now().strftime('%B %Y').upper()
    # Descarga el archivo clientes.json del bucket S3
    bucket_name = 'selenium-enroller'
    file_name = 'clientes.json'
    if os.getenv("TEST_ENV", False):
        file_name = f'mnt/{file_name}'
    else:
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
    # driver.get("https://servicios.comedica.com.sv/ReportaCompraTC-war/")
    
    # Recorre la lista de clientes y envía el formulario para cada uno
    for cliente in clientes:
        socio = cliente['num_socio']
        digitos = cliente['digitos']
        promociones = cliente['promocion']
        promociones_values = []

        select_promocion = Select(driver.find_element(By.NAME, "promocion"))
        select_options = select_promocion.getOptions()
        for promo in promociones:
            for option in select_options:
                text = option.getText()
                if text != None and text.contains(current_mont_and_year) and text.contains(promo):
                    promociones_values.append(option.getValue())

        for promocion_val in promociones_values:
        # Encuentra los campos del formulario y los completa
            driver.get("https://servicios.comedica.com.sv/ReportaCompraTC-war/")
            socio_input = driver.find_element(By.NAME, "num_socio")
            socio_input.send_keys(socio)
            digitos_input = driver.find_element(By.NAME, "digitos")
            digitos_input.send_keys(digitos)
            select_promocion = Select(driver.find_element(By.NAME, "promocion"))
            select_promocion.select_by_value(promocion_val)
        
            # Envía el formulario
            submit_button = driver.find_element(By.CLASS_NAME, "contact100-form-btn")
            submit_button.click()

            # Esperando respuesta del servidor
            driver.implicitly_wait(10)

            response = driver.page_source
            if 'Felicidades, ya te encuentras suscrito a la promoción, se tomarán en cuenta todas las compras que apliquen.' in response:
                print(f'El formulario para {socio} con promocion {promocion_val} se envió correctamente')
            else:
                print('Hubo un error al enviar el formulario para {socio} con promocion {promocion_val}')
        
            # Limpia los campos del formulario para el siguiente cliente
            socio_input.clear()
            digitos_input.clear()
    
    # Cierra el navegador
    driver.quit()
    
    # Devolviendo la respuesta
    response = {
        'statusCode': 200,
        'body': json.dumps({'message': 'Formularios enviados correctamente'})
    }
    return response
