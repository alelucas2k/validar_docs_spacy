from extrair_texto import processar_pdfs
from analisar_spacy import analisar_textos, validar_documento, criterios_obrigatorios


if __name__ == "__main__":
    print("=== ETAPA 1: Extração de texto===")
    #processar_pdfs()

    print("\n=== ETAPA 2: Análise com spaCy ===")
    entidades = analisar_textos()
    validar_documento(entidades, criterios_obrigatorios)

    # print("\n=== ENTIDADES EXTRAÍDAS ===")
    # for label, textos in entidades.items():
    #     if textos:
    #         print(f"{label}: {textos}")