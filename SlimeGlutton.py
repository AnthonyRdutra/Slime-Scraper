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
import pillow_avif
import aviftopng
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
avif = False
ID_MANGA = match.group(1)
intervalo = input("📚 Insira o intervalo de capítulos (ex: 113-120): ").strip()

try:
    CAPITULO_INICIO, CAPITULO_FIM = map(int, intervalo.split('-'))
except ValueError:
    raise ValueError("❌ Intervalo inválido. Use o formato: início-fim (ex: 113-120)")
    

async def baixar_imagem(url, nome_base, pasta):
    """Baixa e salva a imagem no formato correto (JPG, PNG ou AVIF)."""
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                if response.status == 200:
                    extensao = ".jpg"  # Padrão JPG
                    if ".png" in url:
                        extensao = ".png"
                    elif ".avif" in url:
                        extensao = ".avif"

                    nome_arquivo = f"{nome_base}{extensao}"
                    caminho_arquivo = os.path.join(pasta, nome_arquivo)

                    with open(caminho_arquivo, "wb") as f:
                        f.write(await response.read())

                    print(f"✅ Imagem salva: {caminho_arquivo}")
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


def aviftopng(input_folder):
    """
    Converte todos os arquivos AVIF para PNG na pasta especificada.
    """
    for filename in os.listdir(input_folder):
        if filename.lower().endswith(".avif"):
            avif_path = os.path.join(input_folder, filename)
            png_path = os.path.join(input_folder, filename.replace(".avif", ".png"))
            temp_png_path = png_path + ".tmp"  # Arquivo temporário para evitar corrupção
            
            try:
                with Image.open(avif_path) as img:
                    img.convert("RGB").save(temp_png_path, "PNG")  # Salva como PNG
                os.replace(temp_png_path, png_path)  # Substituir apenas se a conversão for bem-sucedida
                os.remove(avif_path)  # Excluir o arquivo AVIF após conversão
                print(f"Converted and deleted: {filename} -> {png_path}")
            except Exception as e:
                if os.path.exists(temp_png_path):
                    os.remove(temp_png_path)  # Remover arquivo temporário se houver falha
                print(f"Failed to convert {filename}: {e}")

def convert_avif_to_png(input_folder, output_folder):
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)
    
    for filename in os.listdir(input_folder):
        if filename.lower().endswith(".avif"):
            avif_path = os.path.join(input_folder, filename)
            png_path = os.path.join(output_folder, filename.replace(".avif", ".png"))
            temp_png_path = png_path + ".tmp"  # Arquivo temporário para evitar corrupção
            
            try:
                with Image.open(avif_path) as img:
                    img.convert("RGB").save(temp_png_path, "PNG")  # Salva como PNG
                os.replace(temp_png_path, png_path)  # Substituir apenas se a conversão for bem-sucedida
                os.remove(avif_path)  # Excluir o arquivo AVIF após conversão
                print(f"Converted and deleted: {filename} -> {png_path}")
            except Exception as e:
                if os.path.exists(temp_png_path):
                    os.remove(temp_png_path)  # Remover arquivo temporário se houver falha
                print(f"Failed to convert {filename}: {e}")

                # Chama a função aviftopng se o arquivo salvo for AVIF
                if filename.lower().endswith(".avif"):
                    print(f"Calling aviftopng() for directory {input_folder}")

def verificar_imagens_avif(pasta):
    """Verifica se existem imagens no formato .avif em uma pasta."""
    for arquivo in os.listdir(pasta):
        if arquivo.lower().endswith(".avif"):
            print(f"✅ Encontrado arquivo AVIF: {arquivo}")
            convert_avif_to_png(pasta, pasta)
    print("❌ Nenhum arquivo AVIF encontrado.")
    return False  # Se não encontrar nenhum arquivo AVIF

def imagens_para_pdf(pasta_imagens, nome_pdf):
    verificar_imagens_avif(pasta_imagens)
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