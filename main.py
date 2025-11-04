from extrair_texto import processar_pdfs
from analisar_spacy import analisar_textos

if __name__ == "__main__":
    print("=== ETAPA 1: Extração de texto ===")
    # processar_pdfs()  # descomente quando quiser rodar a extração

    print("\n=== ETAPA 2: Análise com spaCy ===")
    resultados = analisar_textos()  # já faz a validação internamente

    print("\n=== ENTIDADES EXTRAÍDAS ===")
    for documento, entidades in resultados.items():
        print(f"\n📄 Documento: {documento}")
        for label, textos in entidades.items():
            if textos:
                print(f" - {label}: {textos}")