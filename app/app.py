import json, datetime, locale, boto3, os, logging
from tempfile import mkdtemp
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select

s3 = boto3.client('s3')
url = os.getenv("TARGET_URL")
logger = logging.getLogger()
logger.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s [%(levelname)s] %(message)s')

def obtain_promos(driver):
    keywords = ['GAS', 'SUPERMER']
    return_dict = {}
    # Seteando locale a espanol
    locale.setlocale(locale.LC_TIME, 'es_ES.UTF-8')
    # Obteniendo mes y anio actual en mayuscula para busqueda por texto
    current_mont_and_year = datetime.datetime.now().strftime('%B %Y').upper()

    select_options = Select(driver.find_element(By.NAME, "promocion")).options

    for word in keywords:
        for option in select_options:
            text = option.text
            if text != None and current_mont_and_year in text and word in text:
                return_dict[word] = option.text
    logger.info(f'Promociones obtenidas: {return_dict}')
    return return_dict

def lambda_handler(event, context):
    # Descarga el archivo clientes.json del bucket S3
    bucket_name = os.getenv("S3_BUCKET_NAME")
    file_name = 'clientes.json'
    if os.getenv("TEST_ENV", False):
        file_name = f'mnt/{file_name}'
    else:
        s3.download_file(bucket_name, file_name, '/tmp/' + file_name)

    # Abre el archivo clientes.json y lee los datos
    with open('/tmp/' + file_name, 'r') as f:
        clientes = json.load(f)

    if len(clientes) < 1:
        logger.info(f'No hay clientes en el archivo JSON. Finalizando...')
        return {
            'statusCode': 200,
            'body': 'No hay clientes en el archivo JSON.'
        }
    # Configura el driver de Chrome
    options = webdriver.ChromeOptions()
    options.binary_location = '/opt/chrome/chrome'
    options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1280x1696")
    options.add_argument("--single-process")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-dev-tools")
    options.add_argument("--no-zygote")
    options.add_argument(f"--user-data-dir={mkdtemp()}")
    options.add_argument(f"--data-path={mkdtemp()}")
    options.add_argument(f"--disk-cache-dir={mkdtemp()}")
    options.add_argument("--remote-debugging-port=9222")
    options.add_argument('user-agent=Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/61.0.3163.100 Safari/537.36')
    driver = webdriver.Chrome("/opt/chromedriver",
                              options=options)

    logger.info(f'Getting url: {url}')
    try:
        driver.get(url)
    except Exception as exception:
        logger.exception(f'Error al intentar acceder a la URL. Detalle del error {exception}')
        return {
            'statusCode': 500,
            'body': exception
        }
    driver.implicitly_wait(3000)

    available_promos = obtain_promos(driver)
    if len(available_promos) < 1:
        logger.error(f'No se obtuvieron promociones. Finalizando...')
        return {
            'statusCode': 500,
            'body': 'No se pudo obtener data de las promociones'
        }

    # Recorre la lista de clientes y envía el formulario para cada uno
    for cliente in clientes:
        socio = cliente['num_socio']
        digitos = cliente['digitos']
        promociones = cliente['promociones']

        for promo in promociones:
            if promo in available_promos:
            # Encuentra los campos del formulario y los completa
                driver.get(url)
                socio_input = driver.find_element(By.NAME, "num_socio")
                socio_input.send_keys(socio)
                digitos_input = driver.find_element(By.NAME, "digitos")
                digitos_input.send_keys(digitos)
                select_promocion = Select(driver.find_element(By.NAME, "promocion"))
                select_promocion.select_by_visible_text(available_promos[promo])
                driver.implicitly_wait(3000)
                # Envía el formulario
                submit_button = driver.find_element(By.CLASS_NAME, "contact100-form-btn")
                submit_button.click()

                # Esperando respuesta del servidor
                driver.implicitly_wait(10000)

                response = driver.page_source
                if 'Felicidades, ya te encuentras suscrito a la promoción, se tomarán en cuenta todas las compras que apliquen.' in response:
                    logging.info(f'El formulario para {socio} con promocion {available_promos[promo]} se envió correctamente')
                    print(f'El formulario para {socio} con promocion {available_promos[promo]} se envió correctamente')
                else:
                    logging.warning(f'Hubo un error al enviar el formulario para {socio} con promocion {available_promos[promo]}')
                    print(f'Hubo un error al enviar el formulario para {socio} con promocion {available_promos[promo]}')

    # Cierra el navegador
    driver.quit()

    # Devolviendo la respuesta
    response = {
        'statusCode': 200,
        'body': json.dumps({'message': 'Formularios enviados correctamente'})
    }
    return response
