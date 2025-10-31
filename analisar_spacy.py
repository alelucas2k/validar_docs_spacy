import os
import re
import spacy
from tqdm import tqdm
from spacy.pipeline import EntityRuler

OUTPUT_DIR = "/home/alek/PycharmProjects/PythonProject/texts_extraidos"

NER = spacy.load("pt_core_news_lg")
ruler = NER.add_pipe("entity_ruler", before="ner")

patterns = [
    {"label": "INTERESSADO", "pattern": [
        {"LOWER": "interessado"},
        {"IS_PUNCT": True, "OP": "?"},
        {"IS_SPACE": True, "OP": "*"},
        {"TEXT": {"REGEX": "^[A-ZÀ-ÿ][A-Za-zÀ-ÿ\\.\\s]+$"}, "OP": "+"}
    ]},
    {
        "label": "RELATORIO_FISC",
        "pattern": [
            {"LOWER": "relatório"}, {"LOWER": "de"}, {"LOWER": "fiscalização"},
            {"IS_SPACE": True, "OP": "*"},  # permite quebra de linha
            {"LOWER": {"IN": ["nº", "n°", "no"]}, "OP": "?"},
            {"IS_SPACE": True, "OP": "*"},
            {"TEXT": {"REGEX": r"^[0-9A-Za-z./-]+$"}, "OP": "+"}  # aceita letras, números, /, . e -
        ]
    },
    {"label": "NUM_SEI", "pattern": [
        {"LOWER": "sei"},
        {"LOWER": {"IN": ["nº", "n°", "no"]}, "OP": "?"},
        {"IS_DIGIT": True, "OP": "+"}
    ]},
    {
        "label": "NUM_PROC_FISC",
        "pattern": [
            {"LOWER": "processo"}, {"LOWER": "de"}, {"LOWER": "fiscalização"},
            {"IS_SPACE": True, "OP": "*"},                          # permite quebra de linha
            {"LOWER": {"IN": ["nº", "n°", "no"]}, "OP": "?"},
            {"IS_SPACE": True, "OP": "*"},
            {"TEXT": {"REGEX": r"^[0-9./-]+$"}, "OP": "+"}           # aceita 53504.003563/2016-11
        ]
    },
    {"label": "ARTIGO", "pattern": [{"LOWER": "artigo"}, {"IS_DIGIT": True, "OP": "+"}]},
    {"label": "RESOLUCAO", "pattern": [
        {"LOWER": "resolução"},
        {"LOWER": {"IN": ["nº", "n°", "no"]}, "OP": "?"},
        {"IS_DIGIT": True, "OP": "+"}, {"IS_PUNCT": True, "OP": "?"},
        {"IS_DIGIT": True, "OP": "?"}
    ]},
    {"label": "ASSINATURA_ELETRONICA", "pattern": [
        {"LOWER": "assinado"}, {"LOWER": "eletronicamente"},
        {"LOWER": "por"}, {"IS_TITLE": True, "OP": "+"}
    ]},
    {"label": "CODIGO_VERIFICADOR", "pattern": [
        {"LOWER": "código"}, {"LOWER": "verificador"},
        {"IS_DIGIT": True, "OP": "+"}
    ]},
    {"label": "CRC", "pattern": [
        {"LOWER": "crc"},
        {"TEXT": {"REGEX": "^[A-Za-z0-9]+$"}, "OP": "+"}
    ]},

    # Despacho ordinatório de instauração
    {"label": "DESPACHO", "pattern": [
        {"LOWER": "despacho"},
        {"LOWER": {"IN": ["ordinatório", "ordinatorio"]}, "OP": "?"},
        {"LOWER": "de"},
        {"LOWER": "instauração"},
        {"LOWER": {"IN": ["nº", "n°", "no"]}, "OP": "?"},
        {"TEXT": {"REGEX": "^[0-9/SEICODI]+$"}, "OP": "+"}
    ]},

    # Processo nº 53500.053021/2018-91
    {"label": "NUM_PROCESSO", "pattern": [
        {"LOWER": "processo"},
        {"LOWER": {"IN": ["nº", "n°", "no"]}, "OP": "?"},
        {"TEXT": {"REGEX": "^[0-9./-]+$"}, "OP": "+"}
    ]},

    # Pasta nº RADARRCTS32016000006
    {"label": "NUM_PASTA", "pattern": [
        {"LOWER": "pasta"},
        {"LOWER": {"IN": ["nº", "n°", "no"]}, "OP": "?"},
        {"TEXT": {"REGEX": "^[A-Z0-9]+$"}, "OP": "+"}
    ]},

    # CNPJ/MF nº 40.432.544.0001-47
    {"label": "CNPJ", "pattern": [
        {"TEXT": "CNPJ/MF"},
        {"TEXT": "nº"},
        {"TEXT": {"REGEX": "\\d{2}\\.\\d{3}\\.\\d{3}/\\d{4}-\\d{2}"}}
    ]},

    # Prazo de 15 (quinze) dias
    {
        "label": "PRAZO",
        "pattern": [
            {
                "TEXT": {
                    "REGEX": r"no\s+prazo\s+de\s+\d+\s*(\([a-zA-Z]+\))?\s+dias?"
                }
            }
        ]
    }
]

ruler.add_patterns(patterns)

def limpar_texto(texto: str) -> str:
    texto = re.sub(r'\s+', ' ', texto)
    texto = re.sub(r'–', '-', texto)
    return texto.strip()

def analisar_textos():
    """Lê os textos extraídos e aplica as regras de NER."""
    pattern_labels = [
        "INTERESSADO",
        "RELATORIO_FISC",
        "NUM_SEI",
        "NUM_PROC_FISC",
        "ARTIGO",
        "RESOLUCAO",
        "ASSINATURA_ELETRONICA",
        "CODIGO_VERIFICADOR",
        "CRC",
        "DESPACHO",  # Ex: DESPACHO ORDINATÓRIO DE INSTAURAÇÃO Nº 233/2018/SEI/CODI/SCO
        "NUM_PROCESSO",  # Ex: Processo nº 53500.053021/2018-91
        "NUM_PASTA",  # Ex: Pasta nº RADARRCTS32016000006
        "CNPJ",  # Ex: CNPJ/MF nº 40.432.544.0001-47
        "PRAZO"  # Ex: prazo de 15 (quinze) dias
    ]

    entidades = {label: [] for label in pattern_labels}

    for documento in tqdm(os.listdir(OUTPUT_DIR), desc="Analisando textos", ncols=80):
        caminho = os.path.join(OUTPUT_DIR, documento)
        try:
            with open(caminho, "r", encoding="utf-8") as f:
                texto = limpar_texto(f.read())
        except FileNotFoundError:
            print(f"Arquivo não encontrado: {documento}")
            continue

        doc = NER(texto)
        for ent in doc.ents:
            if ent.label_ in pattern_labels:
                entidades[ent.label_].append(ent.text)


    return entidades

criterios_obrigatorios = {
    "INTERESSADO": True,               # deve sempre aparecer
    "RELATORIO_FISC": True,            # essencial para validar o tipo de documento
    "NUM_SEI": True,                    # identificação do SEI obrigatória
    "NUM_PROC_FISC": True,              # número do processo de fiscalização obrigatório
    "ARTIGO": True,                    # opcional, aparece em citações de leis
    "RESOLUCAO": True,                 # opcional
    "ASSINATURA_ELETRONICA": True,      # importante para validar autenticidade
    "CODIGO_VERIFICADOR": True,         # importante para validar autenticidade
    "CRC": True,                        # opcional, verificação interna
    "DESPACHO": True,                   # geralmente presente no início do documento
    "NUM_PROCESSO": True,               # identificação essencial do processo
    "NUM_PASTA": True,                 # nem todos os documentos possuem
    "CNPJ": True,                       # essencial para identificar a empresa
    "PRAZO": False                       # só aparece em notificações ou intimações
}

def validar_documento(entidades, criterios):

    resultado = {label: bool(entidades.get(label)) for label, obrigatorio in criterios.items() if obrigatorio}
    documento_ok = all(resultado.values())

    print("\n🔍 Resultado da validação:")
    for label, status in resultado.items():
        print(f" - {label}: {'✅ OK' if status else '❌ Faltando'}")

    print("\n✅ Documento completo!" if documento_ok else "\n⚠️ Documento incompleto!")

    return documento_ok, resultado