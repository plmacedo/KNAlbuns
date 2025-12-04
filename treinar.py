import pandas as pd
import joblib
import pylast
import time
from sklearn.neighbors import NearestNeighbors
from scipy.sparse import csr_matrix
from sklearn.feature_extraction.text import TfidfTransformer

# ================= CONFIGURAÇÃO DA API LAST.FM =================
API_KEY = "68098236d385bdd70b2618c15c53f7cd"
API_SECRET = "e9a7623ac218577c4bf5b315341109b6"

try:
    network = pylast.LastFMNetwork(api_key=API_KEY, api_secret=API_SECRET)
except:
    print("Erro: Configure API_KEY no script.")
    exit()

# ================= 1. CARREGAR E PROCESSAR DADOS =================
print("1. Lendo arquivo CSV...")
try:
    df_source = pd.read_csv('C:/Users/ric/Desktop/rik/code/Projeto IA/rym_clean1.csv')
    df_unique = df_source.drop_duplicates(subset=['release_name']).copy()
    
    # Opcional: Limite para testes (remova para produção)
    # df_unique = df_unique.head(50) 
    
    print(f"Total de álbuns iniciais: {len(df_unique)}")
except FileNotFoundError:
    print("Erro: CSV não encontrado.")
    exit()

data_list = []

print("2. Buscando dados no Last.fm...")

for index, row in df_unique.iterrows():
    album_name = row['release_name']
    artist_name = row['artist_name']
    
    print(f"Processando: {album_name}...")
    
    try:
        album_obj = network.get_album(artist_name, album_name)
        top_tags = album_obj.get_top_tags(limit=3)
        
        if not top_tags:
            genero_csv = str(row['primary_genres']).split(',')[0]
            data_list.append([album_name, genero_csv, 1.0])
            continue

        max_weight = int(top_tags[0].weight) or 1

        for tag_item in top_tags:
            tag_name = tag_item.item.get_name().title()
            tag_weight = int(tag_item.weight)
            normalized_weight = tag_weight / max_weight
            
            # Atenção: Usando lista aqui em vez de tupla para facilitar pandas
            data_list.append([album_name, tag_name, normalized_weight])
            
        time.sleep(0.2) # Rate limit

    except Exception as e:
        print(f"   -> Pulo: {e}")
        continue

# ================= 3. CRIAR E SALVAR TUDO =================
print("3. Gerando modelos...")

# DataFrame Bruto (Essencial para permitir atualizações no main.py)
df_final = pd.DataFrame(data_list, columns=['Album', 'Tag', 'Peso'])

# Processamento Matemático
matriz_albuns = df_final.pivot_table(index='Album', columns='Tag', values='Peso').fillna(0)
matriz_esparsa = csr_matrix(matriz_albuns.values)
transformer = TfidfTransformer()
matriz_tfidf = transformer.fit_transform(matriz_esparsa)

knn = NearestNeighbors(metric='cosine', algorithm='brute')
knn.fit(matriz_tfidf)

print("4. Salvando arquivos (incluindo dados brutos)...")

# SALVAMOS O DATAFRAME BRUTO AGORA:
joblib.dump(df_final, 'dados_brutos.pkl')

joblib.dump(knn, 'modelo_knn.pkl')
joblib.dump(matriz_tfidf, 'matriz_tfidf.pkl')
joblib.dump(matriz_albuns.index, 'lista_nomes.pkl')

print("Treinamento concluído! Execute o main.py agora.")