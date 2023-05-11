import json, datetime, locale, boto3, os, logging
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select

s3 = boto3.client('s3')

def obtain_promos(driver):
    keywords = ['GAS', 'SUPERMER']
    return_dict = {}
    # Seteando locale a espanol
    locale.setlocale(locale.LC_TIME, 'es_ES.UTF-8')
    # Obteniendo mes y anio actual en mayuscula para busqueda por texto
    current_mont_and_year = datetime.datetime.now().strftime('%B %Y').upper()

    driver.get("https://servicios.comedica.com.sv/ReportaCompraTC-war/")
    select_options = Select(driver.find_element(By.NAME, "promocion")).options

    for word in keywords:
        for option in select_options:
            text = option.text
            if text != None and current_mont_and_year in text and word in text:
                return_dict[word] = option.text

    return return_dict

def lambda_handler(event, context):
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

    available_promos = obtain_promos(driver)
    logging.info(f'promos:{available_promos}')
    # Navega a la página web
    # driver.get("https://servicios.comedica.com.sv/ReportaCompraTC-war/")

    # Recorre la lista de clientes y envía el formulario para cada uno
    for cliente in clientes:
        socio = cliente['num_socio']
        digitos = cliente['digitos']
        promociones = cliente['promociones']

        for promo in promociones:
            if promo in available_promos:
            # Encuentra los campos del formulario y los completa
                driver.get("https://servicios.comedica.com.sv/ReportaCompraTC-war/")
                socio_input = driver.find_element(By.NAME, "num_socio")
                socio_input.send_keys(socio)
                digitos_input = driver.find_element(By.NAME, "digitos")
                digitos_input.send_keys(digitos)
                select_promocion = Select(driver.find_element(By.NAME, "promocion"))
                select_promocion.select_by_visible_text(available_promos[promo])

                # Envía el formulario
                submit_button = driver.find_element(By.CLASS_NAME, "contact100-form-btn")
                submit_button.click()

                # Esperando respuesta del servidor
                driver.implicitly_wait(10)

                response = driver.page_source
                if 'Felicidades, ya te encuentras suscrito a la promoción, se tomarán en cuenta todas las compras que apliquen.' in response:
                    logging.info(f'El formulario para {socio} con promocion {available_promos[promo]} se envió correctamente')
                    print(f'El formulario para {socio} con promocion {available_promos[promo]} se envió correctamente')
                else:
                    logging.warning(f'Hubo un error al enviar el formulario para {socio} con promocion {available_promos[promo]}')
                    print(f'Hubo un error al enviar el formulario para {socio} con promocion {available_promos[promo]}')

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
