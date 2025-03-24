import asyncio
import os
import re
import aiohttp
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from PIL import Image  

print(r"""

           ___                                      ___           ___     ___                       
          (   ) .-.                                (   )         (   )   (   )                      
    .--.   | | ( __) ___ .-. .-.    .--.     .--.   | | ___  ___  | |_    | |_      .--.  ___ .-.   
  /  _  \  | | (''")(   )   '   \  /    \   /    \  | |(   )(   )(   __) (   __)   /    \(   )   \  
 . .' `. ; | |  | |  |  .-.  .-. ;|  .-. ; ;  ,-. ' | | | |  | |  | |     | |     |  .-. ;|  .-. .  
 | '   | | | |  | |  | |  | |  | ||  | | | | |  | | | | | |  | |  | | ___ | | ___ | |  | || |  | |  
 _\_`.(___)| |  | |  | |  | |  | ||  |/  | | |  | | | | | |  | |  | |(   )| |(   )| |  | || |  | |  
(   ). '.  | |  | |  | |  | |  | ||  ' _.' | |  | | | | | |  | |  | | | | | | | | | |  | || |  | |  
 | |  `\ | | |  | |  | |  | |  | ||  .'.-. | '  | | | | | |  ; '  | ' | | | ' | | | '  | || |  | |  
 ; '._,' ' | |  | |  | |  | |  | |'  `-' / '  `-' | | | ' `-'  /  ' `-' ; ' `-' ; '  `-' /| |  | |  
  '.___.' (___)(___)(___)(___)(___)`.__.'   `.__. |(___) '.__.'    `.__.   `.__.   `.__.'(___)(___) 
                                            ( `-' ;                                                 
                                             `.__.                                                  

""")

URL_MANGA = input("🔗 Insira a URL do mangá: ").strip()
match = re.search(r"manga/(\d+)/", URL_MANGA)
if not match:
    raise ValueError("❌ Erro ao extrair ID do mangá da URL. Verifique o link inserido.")

ID_MANGA = match.group(1)
intervalo = input("📚 Insira o intervalo de capítulos (ex: 113-120): ").strip()

try:
    CAPITULO_INICIO, CAPITULO_FIM = map(int, intervalo.split('-'))
except ValueError:
    raise ValueError("❌ Intervalo inválido. Use o formato: início-fim (ex: 113-120)")

async def baixar_imagem(url, nome_arquivo, pasta):
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                if response.status == 200:
                    caminho_arquivo = os.path.join(pasta, nome_arquivo)
                    with open(caminho_arquivo, "wb") as f:
                        f.write(await response.read())
                    print(f"✅ Imagem salva: {caminho_arquivo}")
                else:
                    print(f"❌ Erro ao baixar {url}: {response.status}")
    except Exception as e:
        print(f"❌ Falha ao baixar {url}: {e}")

async def capturar_nome_manga():
    options = Options()
    options.add_argument("--headless=new")
    options.add_argument("--start-maximized")

    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)

    try:
        print("\n🌐 Acessando a página do mangá para capturar o nome...")
        driver.get(URL_MANGA)
        await asyncio.sleep(3)

        try:
            elemento_nome = driver.find_element(By.XPATH, '//*[@id="__next"]/div/div/main/div[2]/div/div[2]/div[1]/h2')
            nome_manga = elemento_nome.text.strip()
        except Exception as e:
            raise ValueError("❌ Erro ao capturar o nome do mangá: " + str(e))
        
        print(f"📁 Nome do mangá capturado: {nome_manga}")
        return nome_manga
    finally:
        driver.quit()

async def capturar_imagens(capitulo, pasta_imagens):
    options = Options()
    options.add_argument("--headless=new")
    options.add_argument("--start-maximized")

    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)

    tentativas = 0
    max_tentativas = 5

    url_capitulo = f"https://slimeread.com/ler/{ID_MANGA}/{capitulo}"
    
    try:
        while tentativas < max_tentativas:
            try:
                tentativas += 1
                print(f"\n🔄 Tentativa número: {tentativas}")
                driver.get(url_capitulo)
                await asyncio.sleep(5)
                
                imagens = driver.find_elements(By.XPATH, '//img[starts-with(@alt, "Pagina ")]')
                urls_imagens = [img.get_attribute("src") for img in imagens]

                if not urls_imagens:
                    raise Exception("❌ Nenhuma imagem encontrada.")

                tarefas = [baixar_imagem(url, f"pagina_{i:03}.jpg", pasta_imagens) for i, url in enumerate(urls_imagens)]
                await asyncio.gather(*tarefas)
                break
            except Exception as e:
                print(f"❌ Erro ao capturar imagens: {e}")
    finally:
        driver.quit()

def imagens_para_pdf(pasta_imagens, nome_pdf):
    print(f"\n📄 Convertendo imagens para PDF: {nome_pdf}")
    arquivos = sorted(
        [f for f in os.listdir(pasta_imagens) if f.startswith("pagina_") and (f.endswith(".jpg") or f.endswith(".png"))],
        key=lambda x: int(x.split('_')[1].split('.')[0])
    )

    if not arquivos:
        raise FileNotFoundError("❌ Nenhuma imagem encontrada para converter em PDF.")

    imagens = [Image.open(os.path.join(pasta_imagens, arquivo)).convert("RGB") for arquivo in arquivos]
    imagens[0].save(nome_pdf, save_all=True, append_images=imagens[1:])
    print(f"✅ PDF criado com sucesso: {nome_pdf}")

def limpar_imagens(pasta_imagens):
    print("\n🧹 Limpando imagens...")
    for arquivo in os.listdir(pasta_imagens):
        if arquivo.endswith(".jpg") or arquivo.endswith(".png"):
            os.remove(os.path.join(pasta_imagens, arquivo))
            print(f"🗑️ Excluído: {arquivo}")

async def baixar_capitulos():
    nome_manga = await capturar_nome_manga()
    pasta_imagens = os.path.join(os.getcwd(), nome_manga)
    os.makedirs(pasta_imagens, exist_ok=True)
    
    for capitulo in range(CAPITULO_INICIO, CAPITULO_FIM + 1):
        print(f"\n📖 Baixando capítulo {capitulo}...")
        nome_pdf = os.path.join(pasta_imagens, f"{nome_manga} - {capitulo}.pdf")
        await capturar_imagens(capitulo, pasta_imagens)
        imagens_para_pdf(pasta_imagens, nome_pdf)
        limpar_imagens(pasta_imagens)

asyncio.run(baixar_capitulos())
