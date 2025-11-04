import unicodedata
import fitz  # PyMuPDF
import re
import sys
import os
from datetime import datetime

# --- parâmetros ajustáveis ---
MAX_OFFSET = 10       # quantos chars do início da linha a palavra pode aparecer
MAX_LINE_LEN = 90     # comprimento máximo da linha para ser considerada cabeçalho
NUM_LINHAS_ANALISAR = 12
SEPARAR_DOCUMENTOS = True  # ✅ define se os documentos serão salvos separadamente


def sanitize_filename(name: str) -> str:
    """Remove caracteres inválidos para nomes de arquivo no Windows."""
    return re.sub(r'[<>:"/\\|?*]', '_', name)

# -------------------------------------------------------------------
# utilitário: remover acentos (normalizar unicode)
# -------------------------------------------------------------------
def strip_accents(text: str) -> str:
    """Remove marcas diacríticas (acentos) e devolve string normalizada."""
    if not text:
        return text
    nfkd = unicodedata.normalize("NFD", text)
    return "".join(c for c in nfkd if unicodedata.category(c) != "Mn")

# -------------------------------------------------------------------
# palavras-chave principais
# -------------------------------------------------------------------
PALAVRAS_CHAVE = [
    r"\bOF[IÍ]CIO",
    r"\bRELAT[ÓO]RIO DE FISCALIZ",
    r"\bPARECER\b",
    r"\bDESPACHO\b",
    r"\bMEMORANDO\b",
    r"\bPORTARIA\b",
    r"\bCERTID[ÃA]O(?:\s+DE\b)?",
    r"\bTERMO DE CANCELAMENTO DE DOCUMENTO\b",
    r"\bRECIBO ELETR[OÔ]NICO DE PROTOCOLO\b",
]
compiled_patterns = [(p, re.compile(strip_accents(p), re.IGNORECASE)) for p in PALAVRAS_CHAVE]

# -------------------------------------------------------------------
# linhas irrelevantes
# -------------------------------------------------------------------
LINHAS_IRRELEVANTES = [
    r"^ANEXOS?:",
    r"^REFER[ÊE]NCIA:",
    r"WWW\.",
    r"TELEFONE",
    r"CEP",
    r"SAUS|ASA SUL|BRAS[ÍI]LIA",
]
LINHAS_IRRELEVANTES_NORM = [strip_accents(r) for r in LINHAS_IRRELEVANTES]

PADROES_SECAO = [
    r"^[IVXLCDM]+\s*[-–]",
    r"^\d+\s*[-.–]",
    r"^[A-Z]\s*[-.–]",
    r"\bVIDE\b",
]
PADROES_SECAO_NORM = [re.compile(strip_accents(p), re.IGNORECASE) for p in PADROES_SECAO]

# -------------------------------------------------------------------
# limpeza de linhas
# -------------------------------------------------------------------
def limpar_linhas(linhas):
    """Remove linhas administrativas e de rodapé."""
    linhas_filtradas = []
    for linha in linhas:
        linha_clean = linha.strip()
        if not linha_clean:
            continue
        linha_norm = strip_accents(linha_clean.upper())
        skip = False
        for p in LINHAS_IRRELEVANTES_NORM:
            if re.search(p, linha_norm):
                skip = True
                break
        if skip:
            continue
        linhas_filtradas.append(linha_clean)
    return linhas_filtradas

# -------------------------------------------------------------------
# heurística de cabeçalho
# -------------------------------------------------------------------
def parece_cabecalho(linha: str) -> bool:
    linha_stripped = linha.strip()
    if len(linha_stripped) < 5:
        return False
    linha_norm = strip_accents(linha_stripped.upper())
    if any(pat.search(linha_norm) for pat in PADROES_SECAO_NORM):
        return False
    if len(linha_stripped.split()) < 1:
        return False
    return True

# -------------------------------------------------------------------
# função principal com log em arquivo
# -------------------------------------------------------------------
def detectar_inicios_debug(pdf_path: str):
    """
    Detecta inícios de documentos em um PDF com base em palavras-chave.
    🔹 Gera log detalhado em arquivo
    🔹 Garante que a página 1 sempre será considerada início de documento
    """
    doc = fitz.open(pdf_path)
    inicios = []
    tipo_atual = None

    # --- prepara log ---
    log_name = f"log_deteccao_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
    sys.stdout = open(log_name, "w", encoding="utf-8")
    print(f"📘 Iniciando análise: {pdf_path}")
    print(f"🕒 Log salvo em: {log_name}\n")
    print(f"Total de páginas: {len(doc)}\n")

    for i, page in enumerate(doc):
        texto = page.get_text("text")
        raw_lines = texto.splitlines()[:NUM_LINHAS_ANALISAR]
        linhas = limpar_linhas(raw_lines)
        if not linhas:
            continue

        print(f"\n===========================")
        print(f"📄 Página {i+1} — {len(linhas)} linhas úteis")
        print("===========================\n")

        print(f"raw lines: {raw_lines}\n")

        found_in_page = False

        for linha in linhas:
            linha_norm = strip_accents(linha).upper()
            print(f"🔸 Linha: {linha!r}")
            print(f"   ↳ Normalizada: {linha_norm!r} (len={len(linha_norm)})")

            if found_in_page:
                print("   ⚠️ Já houve um início detectado nesta página → ignorando o restante.\n")
                break

            for orig_pattern, comp_pat in compiled_patterns:
                m = comp_pat.search(linha_norm)
                if not m:
                    continue

                start = m.start()
                end = m.end()
                l_len = len(linha_norm)
                is_header = parece_cabecalho(linha)

                label = re.sub(r"[\\\[\]\(\)\?\*\+\^\$\|]", "", orig_pattern)
                label = strip_accents(label).upper().replace(r"\B", "").replace(r"\b", "").strip()

                print(f"   ✅ Match em '{label}' (pos={start}-{end}) usando padrão {orig_pattern!r}")

                if start > MAX_OFFSET:
                    print(f"   🚫 Rejeitado: posição inicial {start} > {MAX_OFFSET}")
                    continue
                if l_len > MAX_LINE_LEN:
                    print(f"   🚫 Rejeitado: linha muito longa ({l_len}>{MAX_LINE_LEN})")
                    continue
                if not is_header:
                    print(f"   🚫 Rejeitado: linha não parece cabeçalho")
                    continue

                if label == tipo_atual:
                    print(f"    🔁 Mesmo tipo detectado ({label}) → continuação do mesmo documento.\n")
                    found_in_page = True
                    break

                # 🎯 Novo documento detectado
                inicios.append((i, label))
                tipo_atual = label
                found_in_page = True
                print(f"   🎯 Aceito: detectado novo início -> {label!r}\n")
                break

            if found_in_page:
                break

        if i == 0 and not found_in_page:
            print("⚠️ Nenhuma palavra-chave encontrada na página 1, mas ela será forçada como início de documento.\n")
            inicios.append((0, "INÍCIO AUTOMÁTICO"))
            tipo_atual = "INÍCIO AUTOMÁTICO"

    doc.close()

    print("\n\n📋 RESUMO DOS TIPOS DETECTADOS:")
    for idx, (pg, tipo) in enumerate(inicios, start=1):
        print(f"   {idx:02d}. Página {pg+1} → {tipo}")
    print("\n✅ Fim da análise.")
    sys.stdout = sys.__stdout__

    return inicios

# -------------------------------------------------------------------
# separação opcional dos documentos detectados
# -------------------------------------------------------------------
def separar_documentos(pdf_path: str, inicios):
    """
    Separa documentos detectados em PDFs individuais.
    Modo híbrido: tenta copiar página original; se falhar, rasteriza.
    Corrigido para evitar caracteres inválidos no nome do arquivo (ex: ':').
    """
    if not SEPARAR_DOCUMENTOS:
        print("⚙️ Separação de documentos desativada.")
        return

    print("\n📂 Iniciando separação de documentos...")
    output_dir = os.path.join(os.path.dirname(pdf_path), "documentos_separados")
    os.makedirs(output_dir, exist_ok=True)

    # Abre o documento de origem apenas uma vez
    doc_origem = fitz.open(pdf_path)

    for i, (pg, tipo) in enumerate(inicios):
        start_page = pg
        end_page = inicios[i + 1][0] if i + 1 < len(inicios) else len(doc_origem)
        novo_pdf = fitz.open()
        total_paginas = end_page - start_page

        print(f"\n📄 Criando documento {i+1}: {tipo} ({total_paginas} pág.)")

        for page_num in range(start_page, end_page):
            try:
                # === TENTATIVA 1: cópia direta (melhor qualidade) ===
                novo_pdf.insert_pdf(doc_origem, from_page=page_num, to_page=page_num)
                print(f"   🟢 Copiada página {page_num+1}")
            except Exception as e1:
                print(f"   ⚠️ Falha ao copiar página {page_num+1}, tentando rasterizar... ({e1})")
                try:
                    page = doc_origem.load_page(page_num)
                    pix = page.get_pixmap(matrix=fitz.Matrix(2, 2), alpha=False)
                    img_as_pdf = fitz.open("pdf", pix.tobytes(format="pdf"))
                    novo_pdf.insert_pdf(img_as_pdf)
                    img_as_pdf.close()
                    print(f"   🟢 Página {page_num+1} convertida via imagem (rasterização).")
                except Exception as e2:
                    print(f"   ❌ Erro total ao inserir página {page_num+1}: {e2}")
                    erro_page = novo_pdf.new_page()
                    erro_page.insert_text((50, 100), f"[ERRO AO INSERIR PÁG {page_num+1}]", fontsize=16)

        # 🔤 Sanitiza o nome do arquivo para evitar erros no Windows
        nome_tipo = sanitize_filename(tipo.replace(" ", "_").replace("(", "").replace(")", ""))
        out_path = os.path.join(output_dir, f"{i+1:02d}_{nome_tipo or 'SEM_TIPO'}.pdf")

        try:
            if novo_pdf.page_count > 0:
                # 🔐 Salvamento seguro, sem otimizações destrutivas
                novo_pdf.save(out_path, garbage=0, deflate=True)
                print(f"✅ Documento salvo: {out_path} ({novo_pdf.page_count} pág.)")
            else:
                print(f"❌ Documento vazio (0 páginas) - não salvo: {out_path}")
        except Exception as e3:
            print(f"❌ Erro crítico ao salvar {out_path}: {e3}")
        finally:
            novo_pdf.close()

    doc_origem.close()
    print("\n📁 Separação concluída!\n")

# -------------------------------------------------------------------
# execução principal
# -------------------------------------------------------------------
if __name__ == "__main__":
    PDF_PATH = "validar_docs/SEI_53500.053021_2018_91.pdf"  # seu arquivo
    inicios = detectar_inicios_debug(PDF_PATH)
    separar_documentos(PDF_PATH, inicios)
