import os
import re
from tqdm import tqdm
import google.generativeai as genai

# Diretórios
INPUT_DIR = "/home/alek/PycharmProjects/PythonProject/documentos_separados"
OUTPUT_DIR = "/home/alek/PycharmProjects/PythonProject/texts_extraidos"

# Configuração da API Gemini
genai.configure(api_key="")

def limpar_texto(texto: str) -> str:
    """Limpa e normaliza o texto extraído."""
    texto = re.sub(r'\s+', ' ', texto)
    texto = re.sub(r'–', '-', texto)
    return texto.strip()

def extrair_texto_via_gemini(caminho_pdf: str) -> str:
    """
    Envia o PDF para o modelo Gemini e retorna o texto limpo,
    pronto para extração de entidades com spaCy.
    """
    try:
        file_ref = genai.upload_file(caminho_pdf)
        response = genai.GenerativeModel("gemini-2.5-flash").generate_content([
            file_ref,
            (
                "Extraia **todo o texto legível** deste documento PDF de forma contínua. "
                "Remova formatações, quebras de linha, cabeçalhos, rodapés, numeração de páginas e caracteres estranhos. "
                "Mantenha apenas o conteúdo textual principal em uma única linha (ou frases separadas por ponto final). "
                "Preserve números, siglas, nomes e símbolos como nº, /, -, . e %. "
                "Retorne o texto limpo e linearizado, ideal para processamento com spaCy."
            )
        ])
        if response and response.text:
            texto = response.text.strip()
            # Normalização extra para garantir consistência
            texto = ' '.join(texto.split())  # remove múltiplos espaços e quebras
            return texto
        return ""
    except Exception as e:
        print(f"Erro ao processar {os.path.basename(caminho_pdf)}: {e}")
        return ""

def processar_pdfs(pasta_entrada: str = INPUT_DIR):
    """Processa todos os PDFs da pasta e salva o texto extraído em .txt."""
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)

    arquivos_pdf = [f for f in os.listdir(pasta_entrada) if f.lower().endswith(".pdf")]
    if not arquivos_pdf:
        print("Nenhum PDF encontrado.")
        return

    for arquivo in tqdm(arquivos_pdf, desc="Extraindo texto dos PDFs", ncols=80):
        caminho_pdf = os.path.join(pasta_entrada, arquivo)
        texto_extraido = extrair_texto_via_gemini(caminho_pdf)

        nome_saida = os.path.splitext(arquivo)[0] + ".txt"
        caminho_saida = os.path.join(OUTPUT_DIR, nome_saida)

        with open(caminho_saida, "w", encoding="utf-8") as f:
            f.write(texto_extraido)

    print(f"\nTextos extraídos salvos em: {OUTPUT_DIR}")