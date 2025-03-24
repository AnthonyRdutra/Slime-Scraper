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

print(r'''
           ___                                                                                             
          (   ) .-.                                                                                        
    .--.   | | ( __) ___ .-. .-.    .--.       .--.     .--.   ___ .-.    .---.   .-..    .--.  ___ .-.    
  /  _  \  | | ('")(   )   '   \  /    \    /  _  \   /    \ (   )   \  / .-, \ /    \  /    \(   )   \   
 . .' `. ; | |  | |  |  .-.  .-. ;|  .-. ;  . .' `. ; |  .-. ; | ' .-. ;(__) ; |' .-,  ;|  .-. ;| ' .-. ;  
 | '   | | | |  | |  | |  | |  | ||  | | |  | '   | | |  |(___)|  / (___) .'`  || |  . ||  | | ||  / (___) 
 _\_`.(___)| |  | |  | |  | |  | ||  |/  |  _\_`.(___)|  |     | |       / .'| || |  | ||  |/  || |        
(   ). '.  | |  | |  | |  | |  | ||  ' _.' (   ). '.  |  | ___ | |      | /  | || |  | ||  ' _.'| |        
 | |  `\ | | |  | |  | |  | |  | ||  .'.-.  | |  `\ | |  '(   )| |      ; |  ; || |  ' ||  .'.-.| |        
 ; '._,' ' | |  | |  | |  | |  | |'  `-' /  ; '._,' ' '  `-' | | |      ' `-'  || `-'  ''  `-' /| |        
  '.___.' (___)(___)(___)(___)(___)`.__.'    '.___.'   `.__,' (___)     `.__.'_.| \__.'  `.__.'(___)       
                                                                                | |                        
                                                                               (___)                       
''')

URL = input("🔗 Insira a URL do capítulo: ").strip()

# Extração de valores com regex
match = re.search(r"ler/(\d+)/(.+)", URL)
if not match:
    raise ValueError("❌ Erro ao extrair ID do mangá e capítulo da URL. Verifique o link inserido.")

ID_MANGA, CAPITULO = match.groups()
URL_MANGA = f"https://slimeread.com/manga/{ID_MANGA}"

NOME_MANGA = None  
PASTA_IMAGENS = None
NOME_PDF = None

async def baixar_imagem(url, nome_arquivo):
    """Baixa uma imagem da URL e salva localmente."""
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                if response.status == 200:
                    caminho_arquivo = os.path.join(PASTA_IMAGENS, nome_arquivo)
                    with open(caminho_arquivo, "wb") as f:
                        f.write(await response.read())
                    print(f"✅ Imagem salva: {caminho_arquivo}")
                else:
                    print(f"❌ Erro ao baixar {url}: {response.status}")
    except Exception as e:
        print(f"❌ Falha ao baixar {url}: {e}")

async def capturar_imagens():
    global NOME_MANGA, PASTA_IMAGENS, NOME_PDF

    tentativas = 0
    max_tentativas = 3

    options = Options()
    options.add_argument("--headless=new")
    options.add_argument("--start-maximized")

    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)

    try:
        # Acessar a página do mangá para capturar o nome
        print("\n🌐 Acessando a página do mangá para capturar o nome...")
        driver.get(URL_MANGA)
        await asyncio.sleep(3)

        # Capturar nome do mangá
        try:
            elemento_nome = driver.find_element(By.XPATH, '//*[@id="__next"]/div/div/main/div[2]/div/div[2]/div[1]/h2')
            NOME_MANGA = elemento_nome.text.strip()
        except Exception as e:
            raise ValueError("❌ Erro ao capturar o nome do mangá: " + str(e))

        # Criar pasta para salvar imagens e PDF
        PASTA_IMAGENS = os.path.join(os.getcwd(), NOME_MANGA)
        os.makedirs(PASTA_IMAGENS, exist_ok=True)
        NOME_PDF = os.path.join(PASTA_IMAGENS, f"{NOME_MANGA} - {CAPITULO}.pdf")

        print(f"📁 Pasta criada: {PASTA_IMAGENS}")
        print(f"📄 Nome do PDF: {NOME_PDF}")

        # Agora acessar o capítulo específico
        while tentativas < max_tentativas:
            try:
                tentativas += 1
                print(f"\n🔄 Tentativa número: {tentativas}")

                print("\n🌐 Acessando o capítulo...")
                driver.get(URL)
                await asyncio.sleep(5)  # Espera o site carregar

                try:
                    # Fechar pop-up se aparecer
                    ele = driver.find_element(By.XPATH, '//*[@id="radix-:R36m:"]/div[2]/button[1]/div')
                    if ele:
                        print("\n🛑 Pop-up apareceu, clicando para fechar...")
                        ele.click()
                except:
                    print("\n✅ Nenhum pop-up encontrado.")

                # Capturar todas as imagens com alt="Pagina X"
                imagens = driver.find_elements(By.XPATH, '//img[starts-with(@alt, "Pagina ")]')
                urls_imagens = [img.get_attribute("src") for img in imagens]

                # Se não encontrar imagens, lançar exceção
                if not urls_imagens:
                    raise Exception("❌ Nenhuma imagem encontrada na página.")

                print("\n📸 Array de links das imagens:")
                print(urls_imagens)

                # Criar e executar tarefas para baixar imagens
                tarefas = []
                for i, url in enumerate(urls_imagens):
                    nome_arquivo = f"pagina_{i:03}.jpg" if ".jpg" in url else f"pagina_{i:03}.png"
                    tarefas.append(baixar_imagem(url, nome_arquivo))

                await asyncio.gather(*tarefas)  # Baixar todas as imagens simultaneamente
                break  # Se deu certo, sair do loop

            except Exception as e:
                print(f"❌ Erro ao capturar imagens: {e}")

    finally:
        driver.quit()
        print("\n🚪 Navegador fechado.")

def imagens_para_pdf():
    """Converte todas as imagens baixadas em um único PDF, mantendo a ordem correta."""
    print("\n📄 Convertendo imagens para PDF...")

    # Verifica se o PDF já existe
    if os.path.exists(NOME_PDF):
        raise FileExistsError(f"❌ O arquivo {NOME_PDF} já existe! Exclua-o ou renomeie antes de continuar.")

    # Listar e ordenar os arquivos corretamente
    arquivos = sorted(
        [f for f in os.listdir(PASTA_IMAGENS) if f.startswith("pagina_") and (f.endswith(".jpg") or f.endswith(".png"))],
        key=lambda x: int(x.split('_')[1].split('.')[0])
    )

    if not arquivos:
        raise FileNotFoundError("❌ Nenhuma imagem encontrada para converter em PDF.")

    # Abrir as imagens e converter para o formato correto
    imagens = [Image.open(os.path.join(PASTA_IMAGENS, arquivo)).convert("RGB") for arquivo in arquivos]

    # Criar o PDF
    imagens[0].save(NOME_PDF, save_all=True, append_images=imagens[1:])
    print(f"✅ PDF criado com sucesso: {NOME_PDF}")

def limpar_imagens():
    """Exclui todas as imagens da pasta após gerar o PDF."""
    print("\n🧹 Limpando imagens após a criação do PDF...")
    arquivos = os.listdir(PASTA_IMAGENS)

    for arquivo in arquivos:
        if arquivo.endswith(".jpg") or arquivo.endswith(".png"):
            caminho = os.path.join(PASTA_IMAGENS, arquivo)
            os.remove(caminho)
            print(f"🗑️ Excluído: {arquivo}")

# Executar a captura de imagens
asyncio.run(capturar_imagens())

# Gerar o PDF após baixar as imagens
imagens_para_pdf()

# Excluir imagens após a conversão
limpar_imagens()
