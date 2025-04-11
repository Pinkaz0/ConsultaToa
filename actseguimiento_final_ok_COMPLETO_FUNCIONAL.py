from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from datetime import datetime
import time
import os

def iniciar_driver():
    chrome_options = webdriver.ChromeOptions()
    chrome_options.add_argument("--headless=new")  # Desactivado para pruebas visuales
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    return webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)

def es_pagina_login():
    try:
        WebDriverWait(driver, 3).until(
            EC.presence_of_element_located((By.ID, "username"))
        )
        return True
    except:
        return False

def manejar_timeout_o_reconexion():
    global driver
    try:
        WebDriverWait(driver, 3).until(
            EC.visibility_of_element_located((By.XPATH, '//h2[contains(text(), "Timeout de sesión")]'))
        )
        print("⚠️ Timeout de sesión detectado.")
        driver.quit()
        driver = iniciar_driver()
        driver.get("https://telefonica-cl.etadirect.com/")
        return True
    except:
        if es_pagina_login():
            print("⚠️ Redirigido a login. Reintentando sesión.")
            driver.quit()
            driver = iniciar_driver()
            driver.get("https://telefonica-cl.etadirect.com/")
            return True
        return False

def fue_expulsado_por_otro_login():
    try:
        WebDriverWait(driver, 3).until(EC.presence_of_element_located((By.ID, "username")))
        print("⚠️ Redirigido al login durante la consulta.")
        return True
    except:
        return False

def intentar_inicio_sesion():
    global driver
    if manejar_timeout_o_reconexion():
        time.sleep(1)

    WebDriverWait(driver, 20).until(EC.presence_of_element_located((By.ID, "username")))
    username = driver.find_element(By.ID, "username")
    password = driver.find_element(By.ID, "password")
    username.send_keys("26314408")
    password.send_keys("9498023Di")
    driver.find_element(By.ID, "sign-in").click()
    time.sleep(2)

    try:
        delsession_checkbox = driver.find_element(By.ID, "delsession")
        if not delsession_checkbox.is_selected():
            delsession_checkbox.click()
        password = driver.find_element(By.ID, "password")
        password.clear()
        password.send_keys("9498023Di")
        driver.find_element(By.ID, "sign-in").click()
        time.sleep(2)
    except:
        pass

meses_es_a_en = {
    "Ene": "Jan", "Feb": "Feb", "Mar": "Mar", "Abr": "Apr",
    "May": "May", "Jun": "Jun", "Jul": "Jul", "Ago": "Aug",
    "Sep": "Sep", "Oct": "Oct", "Nov": "Nov", "Dic": "Dec"
}

def consultar_orden_toa(numero_orden):
    global driver
    print(f"🟢 Iniciando consulta para orden: {numero_orden}")
    driver = iniciar_driver()
    driver.get("https://telefonica-cl.etadirect.com/")
    resultado = {}

    try:
        intentar_inicio_sesion()

        try:
            WebDriverWait(driver, 30).until(
                EC.invisibility_of_element_located((By.CLASS_NAME, "loading-overlay"))
            )
        except TimeoutException:
            pass

        search_icon = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.CLASS_NAME, "action-global-search-icon"))
        )
        driver.execute_script("arguments[0].click();", search_icon)

        search_field = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, "//input[contains(@class, 'search-bar-input') and @type='search']"))
        )
        search_field.clear()
        search_field.send_keys(numero_orden)
        search_field.send_keys(Keys.RETURN)
        time.sleep(5)

        resultados = driver.find_elements(By.CLASS_NAME, "global-search-found-item")
        mejor_resultado_index = None

        for i, resultado in enumerate(resultados):
            try:
                titulo = resultado.find_element(By.CLASS_NAME, "activity-title").text.strip()
                if "alta" in titulo.lower():
                    mejor_resultado_index = i
                    break
            except:
                continue

        if mejor_resultado_index is not None:
            mejor_resultado = resultados[mejor_resultado_index]
            driver.execute_script("arguments[0].scrollIntoView(true);", mejor_resultado)
            time.sleep(1)
            mejor_resultado.click()

            # Esperar que cargue la sección completa
            WebDriverWait(driver, 15).until(
                EC.presence_of_element_located((By.CLASS_NAME, "card-content"))
            )

            try:
                subtipo_element = driver.find_element(By.ID, "id_index_75")
                subtipo = subtipo_element.text.strip().lower() if subtipo_element else ""

                if "alta" in subtipo:
                    try:
                        estado = driver.find_element(By.ID, "id_index_78").text.strip()
                        fecha_emision = driver.find_element(By.ID, "id_index_168").text.strip()
                        fecha_cita = driver.find_element(By.ID, "id_index_169").text.strip()

                        try:
                            intervalo_tiempo = driver.find_element(By.ID, "id_index_384").text.strip()
                        except:
                            intervalo_tiempo = ""

                        try:
                            ventana_llegada = driver.find_element(By.ID, "id_index_173").text.strip()
                        except:
                            ventana_llegada = "SIN VENTANA"

                        try:
                            fecha_emision_fmt = datetime.strptime(fecha_emision.split(" ")[0], "%Y/%m/%d").strftime("%Y-%m-%d")
                        except:
                            fecha_emision_fmt = fecha_emision
                        try:
                            fecha_cita_fmt = datetime.strptime(fecha_cita, "%d/%m/%y").strftime("%Y-%m-%d")
                        except:
                            fecha_cita_fmt = fecha_cita

                        try:
                            cliente = driver.find_element(By.ID, "id_index_80").text.strip()
                        except:
                            cliente = "Desconocido"

                        try:
                            tecnico_raw = driver.find_element(By.CLASS_NAME, "page-header-description--text").text.strip()
                            tecnico = tecnico_raw.split(",")[0].strip()
                        except:
                            tecnico = "SIN TECNICO ASIGNADO"

                        fibra = "DATOS DE FIBRA OK"
                        try:
                            fibra_span = driver.find_element(By.XPATH, '//span[@data-label="custom-text" and @aria-describedby="index_66"]')
                            if "SIN VALIDACION TECNICA" in fibra_span.text.upper():
                                fibra = "ACTIVIDAD BELIEVE- SIN VALIDACION TECNICA"
                        except:
                            pass

                        obs = "ORDEN SIN OBSERVACIÓN"
                        if "cancelado" in estado.lower() or "no realizada" in estado.lower():
                            try:
                                driver.find_element(By.XPATH, "//a[contains(text(), 'Observaciones')]").click()
                                WebDriverWait(driver, 10).until(
                                    EC.presence_of_element_located((By.XPATH, "//table[contains(@class, 'Grid')]"))
                                )
                                filas = driver.find_elements(By.XPATH, "//table[contains(@class, 'Grid')]/tbody/tr")[1:]
                                if filas:
                                    columnas = filas[-1].find_elements(By.TAG_NAME, "td")
                                    if len(columnas) >= 3:
                                        obs = f"{columnas[0].text.strip()} | {columnas[1].text.strip()} | {columnas[2].text.strip()}"
                            except:
                                pass

                            # Dirección y teléfonos
                        direccion = "Sin dirección"  # Inicial por defecto
                        try:
                                    boton_contacto = WebDriverWait(driver, 10).until(
                                        EC.element_to_be_clickable((By.XPATH, '//a[contains(text(), "Contacto y Dirección")]'))
                                    )
                                    driver.execute_script("arguments[0].click();", boton_contacto)

                                    # Esperar a que los campos de dirección se carguen realmente
                                    WebDriverWait(driver, 10).until(
                                        EC.presence_of_element_located((By.ID, "id_index_40"))
                                    )
                                    time.sleep(1)  # dar un segundo adicional para asegurar visibilidad

                                    calle = driver.find_element(By.ID, "id_index_40").text.strip()
                                    entre_calles = driver.find_element(By.ID, "id_index_42").text.strip()
                                    ciudad = driver.find_element(By.ID, "id_index_45").text.strip()
                                    comuna = driver.find_element(By.ID, "id_index_46").text.strip()

                                    # Intentar obtener depto y piso si existen
                                    try:
                                        Departamento_Block_Casa = driver.find_element(By.ID, "id_index_43").text.strip()
                                        Departamento_Block_Casa = f"DEPTO {Departamento_Block_Casa}" if Departamento_Block_Casa and Departamento_Block_Casa != "/" else ""
                                    except:
                                        Departamento_Block_Casa = ""

                                    try:
                                        piso = driver.find_element(By.ID, "id_index_44").text.strip()
                                        piso = f"PISO {piso}" if piso and piso != "/" else ""
                                    except:
                                        piso = ""

                                    direccion_componentes = [calle, Departamento_Block_Casa, piso, entre_calles, ciudad, comuna]
                                    direccion = ", ".join([c for c in direccion_componentes if c and c.strip() != ""])

                                    if not direccion:
                                        direccion = "Sin dirección registrada"

                        except Exception as e:
                                    print("❌ Error al obtener dirección:", e)
                                    direccion = "Sin dirección"

                        try:
                            tel1 = driver.find_element(By.XPATH, '//a[@data-label="ccell"]').text.strip()
                        except:
                            tel1 = ""
                        try:
                            tel2 = driver.find_element(By.XPATH, '//label[@for="id_index_35"]/ancestor::div[@class="form-label-group"]/following-sibling::a').text.strip()
                        except:
                            tel2 = ""
                        try:
                            tel3 = driver.find_element(By.XPATH, '//a[@data-label="XA_CONTACT_PHONE_NUMBER_3"]').text.strip()
                        except:
                            tel3 = ""

                        telefonos = " / ".join([t for t in [tel1, tel2, tel3] if t])

                        resultado = {
                            "orden": numero_orden,
                            "cliente": cliente,
                            "direccion": direccion,
                            "estado": estado,
                            "fecha_emision": fecha_emision_fmt,
                            "fecha_agenda": fecha_cita_fmt,
                            "bloque_horario": intervalo_tiempo,
                            "observacion": obs,
                            "fibra": fibra,
                            "tecnico": tecnico,
                            "ventana_llegada": ventana_llegada,
                            "telefonos": telefonos
                        }

                    except Exception as e:
                        print("❌ Error al procesar el detalle de la orden:", str(e))
                        resultado = {
                            "orden": numero_orden,
                            "cliente": "Desconocido",
                            "direccion": "Sin dirección",
                            "estado": "Error",
                            "fecha_emision": "",
                            "fecha_agenda": "",
                            "observacion": f"Error general: {str(e)}",
                            "fibra": ""
                        }

                else:
                    resultado = {
                        "orden": numero_orden,
                        "cliente": "Desconocido",
                        "direccion": "",
                        "estado": "Subtipo no Alta",
                        "fecha_emision": "",
                        "fecha_agenda": "",
                        "observacion": "No es subtipo Alta",
                        "fibra": ""
                    }

            except Exception as e:
                resultado = {
                    "orden": numero_orden,
                    "cliente": "Desconocido",
                    "direccion": "",
                    "estado": "Error",
                    "fecha_emision": "",
                    "fecha_agenda": "",
                    "observacion": f"Error general: {str(e)}",
                    "fibra": ""
                }

        else:
            resultado = {
                "orden": numero_orden,
                "cliente": "Desconocido",
                "direccion": "",
                "estado": "No encontrada",
                "fecha_emision": "",
                "fecha_agenda": "",
                "observacion": "No se encontró subtipo Alta",
                "fibra": ""
            }

    except Exception as e:
        resultado = {
            "orden": numero_orden,
            "cliente": "Desconocido",
            "direccion": "",
            "estado": "Error",
            "fecha_emision": "",
            "fecha_agenda": "",
            "observacion": f"Error general: {str(e)}",
            "fibra": ""
        }

    finally:
        try:
            driver.quit()
        except:
            pass

    return resultado
def lock_and_run(numero_orden):
    while os.path.exists("lock.tmp"):
        print("🕒 Esperando turno para consultar...")
        time.sleep(2)

    open("lock.tmp", "w").close()
    try:
        return consultar_orden_toa(numero_orden)
    finally:
        os.remove("lock.tmp")