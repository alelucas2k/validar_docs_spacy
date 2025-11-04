import os
import re
import spacy
from tqdm import tqdm
from spacy.pipeline import EntityRuler
from spacy.matcher import Matcher

OUTPUT_DIR = "despachos_txt"

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
            {"LOWER": {"IN": ["relatório", "relatórios"]}}, {"LOWER": "de"}, {"LOWER": "fiscalização"},
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
    {
        "label": "NUM_PROC_ADM",
        "pattern": [
            {"LOWER": "processo"}, {"LOWER": "administrativo"},
            {"IS_SPACE": True, "OP": "*"},  # permite quebra de linha
            {"LOWER": {"IN": ["nº", "n°", "no"]}, "OP": "?"},
            {"IS_SPACE": True, "OP": "*"},
            {"TEXT": {"REGEX": r"^[0-9./-]+$"}, "OP": "+"}  # aceita 53504.003563/2016-11
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
        {"LOWER": "código"},
        {"LOWER": "crc"},
        {"TEXT": {"REGEX": "^[A-Za-z0-9]"}, "OP": "+"}
    ]},

{
    "label": "INFORME",
    "pattern": [
        {"LOWER": {"IN": ["informe", "informes"]}},
        {"LOWER": {"IN": ["nº", "n°", "no"]}, "OP": "?"},
        {"IS_SPACE": True, "OP": "*"},
        {"TEXT": {"REGEX": r"^\d{1,4}/\d{4}$"}},
        {"TEXT": {"REGEX": r"^/[A-Z]{2,}(/[A-Z]{2,})*$"}, "OP": "?"}
    ]
},

    # Despacho ordinatório de instauração
    {"label": "DESPACHO", "pattern": [
        {"LOWER": {"IN": ["despacho", "despachos"]}},
        {"LOWER": {"IN": ["ordinatório", "ordinatorio"]}, "OP": "?"},
        {"LOWER": "de"},
        {"LOWER": "instauração"},
        {"LOWER": {"IN": ["nº", "n°", "no", '№']}, "OP": "?"},
        {"TEXT": {"REGEX": "^[0-9/SEICODI]+$"}, "OP": "+"}
    ]},

    # Processo nº 53500.053021/2018-91
    {"label": "NUM_PROCESSO", "pattern": [
        {"LOWER": "processo"},
        {"LOWER": {"IN": ["nº", "n°", "no"]}, "OP": "?"},
        {"TEXT": {"REGEX": "^[0-9./-]+$"}, "OP": "+"}
    ]},

    {"label": "HORA_ASSINATURA", "pattern": [
            {"TEXT": {"REGEX": "\\d{2}/\\d{2}/\\d{4}"}},                          # Data
            {"LOWER": ","},
            {"LOWER": {"REGEX": "[aà]s"}},
            {"TEXT": {"REGEX": "\\d{2}:\\d{2}"}},                                 # Hora
            {"TEXT": ","},
            {"TEXT": {"REGEX": "conforme"}},                                      # Frase fixa
            {"LOWER": {"REGEX": "hor[aá]rio"}},
            {"LOWER": {"REGEX": "oficial"}},
            {"LOWER": {"REGEX": "de"}},
            {"LOWER": {"REGEX": "bras[ií]lia"}},
    ]},
    # Pasta nº RADARRCTS32016000006
    {"label": "NUM_PASTA", "pattern": [
        {"LOWER": {"IN": ["pasta", "pastas"]}},
        {"LOWER": {"IN": ["nº", "n°", "no", "n.º"]}, "OP": "?"},
        {"TEXT": {"REGEX": "^[A-Z0-9]+$"}, "OP": "+"}
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

pattern_labels = [
    "INTERESSADO",
    "NUM_SEI",
    "RELATORIO_FISC",
    "NUM_PROC_FISC",
    "NUM_PROC_ADM",
    "INFORME",
    "ARTIGO",
    "RESOLUCAO",
    "ASSINATURA_ELETRONICA",
    "CODIGO_VERIFICADOR",
    "CRC",
    "DESPACHO",
    "NUM_PROCESSO",
    "NUM_PASTA",
    "CNPJ",
    "CPF",
    "HORA_ASSINATURA",
    "PRAZO"
]
def analisar_textos():

    matcher = Matcher(NER.vocab)
    pattern_cnpj_dois_tokens = [
        {"TEXT": {"REGEX": r"\d{2}\.\d{3}\.\d{3}/"}},
        {"TEXT": {"REGEX": r"\d{4}-\d{2}"}}
    ]
    matcher.add("CNPJ", [pattern_cnpj_dois_tokens])

    # PADRÃO PARA CPF
    pattern_cpf_dois_tokens = [
        {"TEXT": {"REGEX": r"\d{3}\.\d{3}\."}},  # Primeiro token com "." no final
        {"TEXT": {"REGEX": r"\d{3}-\d{2}"}}  # Segundo token
    ]
    matcher.add("CPF", [pattern_cpf_dois_tokens])

    resultados_gerais = {}

    for documento in tqdm(os.listdir(OUTPUT_DIR), desc="Analisando e validando", ncols=80):
        caminho = os.path.join(OUTPUT_DIR, documento)
        try:
            with open(caminho, "r", encoding="utf-8") as f:
                texto = limpar_texto(f.read())
        except FileNotFoundError:
            print(f"Arquivo não encontrado: {documento}")
            continue

        doc = NER(texto)

        # Dicionário de entidades do documento atual
        entidades = {label: [] for label in pattern_labels}

        # Entidades encontradas pelo NER
        for ent in doc.ents:
            if ent.label_ in pattern_labels:
                entidades[ent.label_].append(ent.text)

        # Entidades via Matcher
        matches = matcher(doc)
        for _, start, end in matches:
            span = doc[start:end]
            entidades["CNPJ"].append(span.text)

        # Salva no resultado geral
        resultados_gerais[documento] = entidades

        print(f"\n📄 Validando documento: {documento}")
        validar_documento(caminho, entidades, criterios_obrigatorios)

    return resultados_gerais

criterios_obrigatorios = {
    "INTERESSADO": True,               # deve sempre aparecer
    "RELATORIO_FISC": True,            # essencial para validar o tipo de documento
    "NUM_PROC_ADM": True,
    "INFORME" : True,
    "NUM_PROC_FISC": True,  # número do processo de fiscalização obrigatório
    "NUM_SEI": True,                    # identificação do SEI obrigatória
    "ARTIGO": True,                    # opcional, aparece em citações de leis
    "RESOLUCAO": True,                 # opcional
    "ASSINATURA_ELETRONICA": True,      # importante para validar autenticidade
    "CODIGO_VERIFICADOR": True,         # importante para validar autenticidade
    "CRC": True,                        # opcional, verificação interna
    "DESPACHO": True,                   # geralmente presente no início do documento
    "NUM_PROCESSO": True,               # identificação essencial do processo
    "NUM_PASTA": True,                 # nem todos os documentos possuem
    "CNPJ": True,                       # essencial para identificar a empresa
    "CPF": True,
    "HORA_ASSINATURA": True,
    "PRAZO": False                       # só aparece em notificações ou intimações
}

def validar_documento(caminho_arquivo, entidades, criterios):
    nome_processo = os.path.splitext(os.path.basename(caminho_arquivo))[0]
    saida = os.path.join(OUTPUT_DIR, f"{nome_processo}")

    resultado = {label: bool(entidades.get(label)) for label, obrigatorio in criterios.items() if obrigatorio}
    documento_ok = all(resultado.values())

    print("\n🔍 Resultado da validação:")
    for label, status in resultado.items():
        print(f" - {label}: {' OK' if status else '❌ Faltando'}")

    print("\n Documento completo!" if documento_ok else "\n⚠️ Documento incompleto!")

    caminho_rel = "relatorio.txt"
    with open(caminho_rel, "a", encoding="utf-8") as f:
        f.write(f"\n===========================\n")
        f.write(f"processo: {nome_processo}\n")
        for label, status in resultado.items():
            f.write(f" - {label} : {'✅' if status else '❌'}\n")
        f.write(f"Status final: {'COMPLETO ✅' if documento_ok else 'INCOMPLETO ⚠️'}\n")
        f.write(f"===============================\n")

    return documento_ok, resultado