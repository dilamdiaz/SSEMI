from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC
import time
import os
from reportlab.pdfgen import canvas

# Crear carpetas necesarias
os.makedirs("tests/screenshots", exist_ok=True)
os.makedirs("tests/files", exist_ok=True)

# Ruta del archivo PDF de prueba
pdf_path = os.path.abspath("tests/files/test.pdf")

# Crear un PDF de prueba si no existe
if not os.path.exists(pdf_path):
    c = canvas.Canvas(pdf_path)
    c.drawString(100, 750, "PDF de prueba para Selenium")
    c.save()
    print(f"PDF de prueba creado en: {pdf_path}")

def init_driver():
    options = webdriver.ChromeOptions()
    options.add_argument("--start-maximized")
    driver = webdriver.Chrome(options=options)
    return driver

def prueba_datos_formulario(driver):
    print("=== Prueba: Datos Correctos e Incorrectos ===")
    driver.get("https://ssemi.onrender.com/static/subir_evidencias.html")

    wait = WebDriverWait(driver, 10)
    wait.until(EC.presence_of_element_located((By.ID, "titulo")))

    # --- Datos Correctos ---
    driver.find_element(By.ID, "titulo").send_keys("Evidencia Selenium")
    driver.find_element(By.ID, "descripcion").send_keys("Prueba automatizada")

    # Seleccionar categoría
    select = Select(driver.find_element(By.ID, "categoria"))
    select.select_by_value("desempeño")

    # Subir archivo de prueba
    driver.find_element(By.ID, "archivos").send_keys(pdf_path)

    # Enviar formulario
    driver.find_element(By.TAG_NAME, "button").click()
    time.sleep(2)
    driver.save_screenshot("tests/screenshots/prueba_correcta.png")
    print("Captura de datos correctos guardada.")

    # --- Datos Incorrectos (Título vacío) ---
    driver.find_element(By.ID, "titulo").clear()
    driver.find_element(By.TAG_NAME, "button").click()
    time.sleep(2)
    driver.save_screenshot("tests/screenshots/prueba_incorrecta.png")
    print("Captura de datos incorrectos guardada.")

def prueba_pantalla_completa(driver):
    print("=== Prueba: Pantalla Completa ===")
    driver.get("https://ssemi.onrender.com/")  # Home del proyecto

    wait = WebDriverWait(driver, 10)
    wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))

    # Ajustar ventana al tamaño completo
    S = lambda X: driver.execute_script('return document.body.parentNode.scroll'+X)
    driver.set_window_size(S('Width'), S('Height'))
    driver.save_screenshot("tests/screenshots/pantalla_completa.png")
    print("Captura de pantalla completa guardada.")

def prueba_espera_cargue(driver):
    print("=== Prueba: Espera de Cargue ===")
    driver.get("https://ssemi.onrender.com/static/subir_evidencias.html")

    wait = WebDriverWait(driver, 10)
    elementos = ["titulo", "descripcion", "categoria", "archivos", "button"]

    for elem in elementos:
        if elem == "button":
            wait.until(EC.presence_of_element_located((By.TAG_NAME, "button")))
        else:
            wait.until(EC.presence_of_element_located((By.ID, elem)))
        print(f"Elemento {elem} cargado correctamente")

    driver.save_screenshot("tests/screenshots/espera_cargue.png")
    print("Captura de espera de cargue guardada.")

def main():
    driver = init_driver()
    try:
        prueba_datos_formulario(driver)
        prueba_pantalla_completa(driver)
        prueba_espera_cargue(driver)
        print("Todas las pruebas finalizadas correctamente.")
    except Exception as e:
        print("Error durante las pruebas:", e)
    finally:
        driver.quit()

if __name__ == "__main__":
    main()
