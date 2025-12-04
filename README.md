# Recomendador de Álbuns com IA

Um sistema de recomendação de música baseado em conteúdo (*Content-Based
Filtering*) que utiliza **Machine Learning (KNN)** e a **API da
Last.fm** para sugerir álbuns com base nas preferências do usuário.\
O projeto conta com uma **interface gráfica moderna** construída em
**CustomTkinter**.

------------------------------------------------------------------------

## Funcionalidades

-   **Interface Gráfica Moderna:** Tema escuro e layout responsivo.\
-   **Busca em Tempo Real:** Pesquisa álbuns diretamente na API da
    Last.fm.\
-   **Algoritmo de Recomendação:**\
    Utiliza **K-Nearest Neighbors (KNN)** e **TF-IDF** para encontrar
    similaridades entre as *tags* dos álbuns.\
-   **Resultados Visuais:** Exibe capas e porcentagem de
    compatibilidade.\
-   **Banco de Dados Dinâmico:** Aprende novos álbuns conforme o uso.

------------------------------------------------------------------------

## Tecnologias Utilizadas

-   Python 3.x\
-   CustomTkinter\
-   Scikit-Learn\
-   Pandas & NumPy\
-   Pylast\
-   Pillow\
-   Joblib

------------------------------------------------------------------------

## Instalação e Dependências

``` bash
pip install customtkinter pylast pandas scikit-learn pillow joblib numpy scipy requests
```

------------------------------------------------------------------------

## onfiguração Inicial

### 1. API Keys

Edite `API_KEY` e `API_SECRET` em `treinar.py` e `backend_logic.py` para
usar suas próprias chaves.

### 2. Dataset Inicial

Inclua um arquivo CSV inicial (ex: `rym_clean1.csv`) no caminho
configurado em `treinar.py`.

------------------------------------------------------------------------

## Como Executar

### **Passo 1 --- Treinamento Inicial**

``` bash
python treinar.py
```

Gera os arquivos:\
- `modelo_knn.pkl`\
- `matriz_tfidf.pkl`\
- `dados_brutos.pkl`

### **Passo 2 --- Abrir a Aplicação**

``` bash
python interface_app.py
```

------------------------------------------------------------------------

## Estrutura dos Arquivos

-   **treinar.py** --- Treinamento e geração dos modelos.\
-   **interface_app.py** --- Interface gráfica.\
-   **backend_logic.py** --- Lógica de busca e recomendação.\
-   **\*.pkl** --- Arquivos gerados automaticamente.

------------------------------------------------------------------------

## Como Usar

1.  Digite o nome de um álbum e pressione **Enter** ou clique em
    **"+"**.\
2.  Se houver múltiplas versões, escolha a correta.\
3.  Adicione quantos álbuns quiser.\
4.  Ajuste o slider para escolher o número de recomendações.\
5.  Clique em **GERAR RECOMENDAÇÕES**.\
6.  Veja os álbuns recomendados com porcentagem de compatibilidade.
