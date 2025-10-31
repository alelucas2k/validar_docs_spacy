# 🧠 Validador Automático de Documentos — ANATEL / IA Generativa

## 📘 Visão Geral

Este projeto automatiza a **extração, análise e validação de documentos oficiais** (como relatórios e despachos administrativos) utilizando **IA generativa (Gemini)** e **Processamento de Linguagem Natural (spaCy)**.

O sistema realiza duas etapas principais:

1. **Extração de texto de PDFs** — envia os documentos para o modelo **Gemini 2.5 Flash**, que retorna o texto limpo e linearizado.
2. **Análise e validação** — usa o **spaCy** com padrões personalizados (EntityRuler) para identificar entidades e verificar se o documento contém todos os elementos obrigatórios.

---

## 🧩 Estrutura do Projeto

```
.
├── extrair_texto.py         # Extração e limpeza de texto via Gemini
├── analisar_spacy.py        # Regras NER e validação com spaCy
├── main.py                  # Ponto de entrada do pipeline
├── documentos_separados/    # PDFs de entrada
└── texts_extraidos/         # Textos .txt extraídos (saída intermediária)
```

---

## ⚙️ Requisitos

### Dependências principais
```bash
pip install spacy tqdm google-generativeai
python -m spacy download pt_core_news_lg
```

### Outras dependências
- Python ≥ 3.9
- Conta e **API key da Gemini** (configurada na variável `genai.configure(api_key="")` em `extrair_texto.py`)

---

## 🚀 Como Executar

### 1. Organize seus PDFs
Coloque os arquivos PDF a serem analisados dentro da pasta:
```
documentos_separados/
```

### 2. Configure a chave da API
Abra `extrair_texto.py` e insira sua **API key**:
```python
genai.configure(api_key="SUA_CHAVE_AQUI")
```

### 3. Execute o pipeline
No terminal:
```bash
python main.py
```

### Etapas:
- **Etapa 1**: (opcional) extrai o texto via Gemini e salva em `texts_extraidos/`  
  (descomente `processar_pdfs()` no `main.py` se quiser rodar)
- **Etapa 2**: analisa e valida os textos extraídos com spaCy.

---

## 🧮 Exemplo de Saída

```
=== ETAPA 2: Análise com spaCy ===
Analisando textos: 100%|████████████████████████████████| 3/3 [00:01<00:00,  2.50it/s]

🔍 Resultado da validação:
 - INTERESSADO: ✅ OK
 - RELATORIO_FISC: ✅ OK
 - NUM_SEI: ✅ OK
 - NUM_PROC_FISC: ❌ Faltando
 - ARTIGO: ✅ OK
 - RESOLUCAO: ❌ Faltando
 - ASSINATURA_ELETRONICA: ✅ OK
 - CODIGO_VERIFICADOR: ✅ OK
 - CRC: ✅ OK
 - DESPACHO: ✅ OK
 - NUM_PROCESSO: ✅ OK
 - NUM_PASTA: ✅ OK
 - CNPJ: ✅ OK

⚠️ Documento incompleto!
```

---

## 🧠 Como Funciona a Análise

O script `analisar_spacy.py` define **padrões personalizados (regex + regras linguísticas)** com o `EntityRuler` do spaCy para detectar informações específicas dos documentos administrativos, como:

| Entidade | Exemplo Detectado |
|-----------|------------------|
| `INTERESSADO` | Interessado: Empresa XYZ Ltda |
| `NUM_PROC_FISC` | Processo de Fiscalização nº 53504.003563/2016-11 |
| `RESOLUCAO` | Resolução nº 1234/2020 |
| `CNPJ` | CNPJ/MF nº 40.432.544.0001-47 |
| `PRAZO` | no prazo de 15 (quinze) dias |

Essas entidades são usadas para validar a **completude** e **autenticidade** do documento.

---

## 🧾 Critérios de Validação

O arquivo `analisar_spacy.py` contém o dicionário `criterios_obrigatorios`, onde cada tipo de entidade pode ser marcada como obrigatória (`True`) ou opcional (`False`):

```python
criterios_obrigatorios = {
    "INTERESSADO": True,
    "RELATORIO_FISC": True,
    "NUM_SEI": True,
    "NUM_PROC_FISC": True,
    "ASSINATURA_ELETRONICA": True,
    "CODIGO_VERIFICADOR": True,
    "CNPJ": True,
    "PRAZO": False
}
```

---

