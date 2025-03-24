
# Slime Scrapper

Um scraper automatizado para baixar capítulos de mangás do site [Slimeread](https:/slimeread.com/) e convertê-los em PDF.  

- Baixa todas as imagens de um capítulo (recomendando para download de apenas um capitulo)

- Salva as imagens localmente em uma pasta com o nome da obra

- Converte as imagens para PDF automaticamente

- Remove as imagens após a conversão

- Cria um PDF com o nome da obra e capítulo


# Slime Glutton

Um scraper automatizado para baixar mutiplos capítulos do site [Slimeread](https:/slimeread.com/) e convertê-los em PDF.  

- Baixa todas as imagens de multiplos capitulos (porém com maiores chances de bloqueio via cloud flare)
  
- Mesmas funções de escrita e edição do Slime Scrapper. 


## Uso/Exemplos

- Instalação:
```
    git clone https://github.com/SEU-USUARIO/Slime-Scraper.git
    cd Slime-Scraper (ou abra o diretório da instalação)
```
- Pip para todas as dependencias:
```
    pip install asyncio aiohttp selenium webdriver-manager pillow pillow-avif-plugin
```

- Execute o script:
```
    python SlimeScraper.py
```
ou  caso queira baixar multiplos capitulos:
```
    python SlimeGlutton.py
```

- Você será recebido pela tela: 
![image](https://github.com/user-attachments/assets/778f1712-0d16-44f4-b346-8010b7fddfb0)

Basta adicioar o link do capítulo que seja baxar. 
