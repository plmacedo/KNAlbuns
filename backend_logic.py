import joblib
import pandas as pd
import numpy as np
import pylast
from sklearn.neighbors import NearestNeighbors
from scipy.sparse import csr_matrix
from sklearn.feature_extraction.text import TfidfTransformer
import os

# ================= CONFIGURAÇÃO =================
API_KEY = "API_KEY"
API_SECRET = "API_SECRET"

class Sistema:
    def __init__(self):
        self.network = None
        self.knn = None
        self.matriz_tfidf = None
        self.lista_nomes = None
        self.df_bruto = None
        
        self.inicializar_api()
        self.carregar_dados()

    def inicializar_api(self):
        try:
            self.network = pylast.LastFMNetwork(api_key=API_KEY, api_secret=API_SECRET)
            print("[Backend] API Last.fm conectada.")
        except Exception as e:
            print(f"[Backend] Erro API: {e}")

    def carregar_dados(self):
        print("[Backend] Carregando modelos .pkl...")
        try:
            if os.path.exists('modelo_knn.pkl'):
                self.knn = joblib.load('modelo_knn.pkl')
                self.matriz_tfidf = joblib.load('matriz_tfidf.pkl')
                self.lista_nomes = joblib.load('lista_nomes.pkl')
                self.df_bruto = joblib.load('dados_brutos.pkl')
                print("[Backend] Dados carregados com sucesso.")
            else:
                raise FileNotFoundError("Arquivos não encontrados")
        except Exception as e:
            print(f"[Backend] {e}. Iniciando modo limpo.")
            self.df_bruto = pd.DataFrame(columns=['Album', 'Tag', 'Peso'])
            self.lista_nomes = pd.Index([])
            self.matriz_tfidf = None
            self.knn = None

    def buscar_candidatos(self, nome_busca):
        if self.lista_nomes is not None:
            # Busca no Cache
            match_exact = [n for n in self.lista_nomes if nome_busca.lower() == n.lower()]
            if match_exact: return 'CACHE_HIT', match_exact[0]

            match_partial = [n for n in self.lista_nomes if nome_busca.lower() in n.lower()]
            if match_partial: return 'CACHE_HIT', match_partial[0]

        # Busca na API
        print(f"[Backend] Buscando '{nome_busca}' na API...")
        try:
            if not self.network: return 'ERROR', "API Offline"
            
            search = self.network.search_for_album(nome_busca)
            resultados = search.get_next_page()
            
            if not resultados: return 'NOT_FOUND', None
            
            candidatos = []
            for item in resultados[:5]:
                try:
                    candidatos.append({
                        'titulo': item.title,
                        'artista': item.artist.name,
                        'objeto': item
                    })
                except: continue
                
            return 'API_OPTIONS', candidatos
        except Exception as e:
            return 'ERROR', str(e)

    def processar_escolha_usuario(self, candidato_obj, titulo_real, artista_real): # Atualiza o sistema com o álbum escolhido pelo usuário. Busca as tags do album e caso nao existam, busca as do artista.
        print(f"[Backend] Analisando tags: {titulo_real}...")
        try:
            # busca direta para garantir metadados frescos
            album_final = self.network.get_album(artista_real, titulo_real)
            top_tags = album_final.get_top_tags(limit=3)
            
            if not top_tags:
                print("[Backend] Sem tags no álbum. Tentando artista...")
                artist_obj = self.network.get_artist(artista_real)
                top_tags = artist_obj.get_top_tags(limit=3)
            
            if not top_tags:
                print("[Backend] Falha: Sem tags disponíveis.")
                return False

            max_weight = int(top_tags[0].weight)
            if max_weight == 0: max_weight = 1
            novos_dados = []
            
            for tag_item in top_tags:
                novos_dados.append({
                    'Album': titulo_real,
                    'Tag': tag_item.item.get_name().title(),
                    'Peso': int(tag_item.weight) / max_weight
                })
            
            novo_df = pd.DataFrame(novos_dados)
            self.df_bruto = pd.concat([self.df_bruto, novo_df], ignore_index=True)
            self.retreinar_sistema()
            return True

        except Exception as e:
            print(f"[Backend] Erro ao processar: {e}")
            return False

    def retreinar_sistema(self): #Recalcula as matrizes com base no df_bruto atualizado e salva no disco.

        print("[Backend] Re-treinando inteligência com novos dados...")
        try:
            # Refaz a matriz pivô
            matriz_albuns = self.df_bruto.pivot_table(index='Album', columns='Tag', values='Peso').fillna(0)

            # Prepara para o KNN
            matriz_esparsa = csr_matrix(matriz_albuns.values)
            transformer = TfidfTransformer()
            matriz_tfidf_nova = transformer.fit_transform(matriz_esparsa)
            
            # Treina KNN
            knn_novo = NearestNeighbors(metric='cosine', algorithm='brute')
            knn_novo.fit(matriz_tfidf_nova)
            
            # Atualiza variáveis em memória
            self.knn = knn_novo
            self.matriz_tfidf = matriz_tfidf_nova
            self.lista_nomes = matriz_albuns.index
            
            # Persiste no disco
            joblib.dump(self.df_bruto, 'dados_brutos.pkl')
            joblib.dump(self.knn, 'modelo_knn.pkl')
            joblib.dump(self.matriz_tfidf, 'matriz_tfidf.pkl')
            joblib.dump(self.lista_nomes, 'lista_nomes.pkl')
            print("[Backend] Sistema salvo!")
        except Exception as e:
            print(f"[Backend] Erro treino: {e}")

    def gerar_recomendacoes_com_detalhes(self, albuns_selecionados, qtd=4):
        """
        Gera recomendações e busca capa/artista na API para cada recomendação.
        """
        if self.knn is None: return []

        # Limite de segurança para não travar a UI com muitas requisições
        if qtd > 20: qtd = 20
        
        print(f"[Backend] Calculando {qtd} recomendações para: {albuns_selecionados}...")
        
        try:
            # Lógica KNN Padrão
            # pega vetores dos álbuns selecionados
            indices = [self.lista_nomes.get_loc(a) for a in albuns_selecionados if a in self.lista_nomes]
            if not indices: return []

            vetores = self.matriz_tfidf[indices]

            # calcula Centróide (Vetor do perfil de gosto do usuário)
            user_vector = np.asarray(vetores.mean(axis=0))

            # Busca mais vizinhos para garantir que teremos 'qtd' únicos após filtrar os inputs
            num_vizinhos = qtd + len(indices) + 5
            distancias, result_indices = self.knn.kneighbors(user_vector, n_neighbors=num_vizinhos)
            
            # Recomendações brutas (sem detalhes como artista/capa)
            raw_recs = []
            result_indices = result_indices.flatten()
            distancias = distancias.flatten()
            
            for i, idx in enumerate(result_indices):
                nome = self.lista_nomes[idx]
                if nome not in albuns_selecionados:
                    score = (1 - distancias[i]) * 100
                    raw_recs.append((nome, score))
                    if len(raw_recs) >= qtd: break
            
            # Busca artista e capa de cada album recomendado na API
            print("[Backend] Buscando capas e artistas dos recomendados...")
            final_recs = []
            
            for nome_album, score in raw_recs:
                try:
                    # Busca direta para pegar metadados frescos
                    res = self.network.search_for_album(nome_album)
                    page = res.get_next_page()
                    
                    if page:
                        best_match = page[0] # Pega o primeiro resultado
                        artist_name = best_match.artist.name
                        image_url = best_match.get_cover_image(size=3) 
                    else:
                        artist_name = "Desconhecido"
                        image_url = None
                        
                    final_recs.append({
                        'album': nome_album,
                        'artist': artist_name,
                        'image_url': image_url,
                        'score': score
                    })
                except Exception as e:
                    print(f"[Backend] Erro ao detalhar {nome_album}: {e}")
                    # Caso nao encontrar as informações, adiciona mesmo sem detalhes para não perder a recomendação
                    final_recs.append({'album': nome_album, 'artist': '?', 'image_url': None, 'score': score})
            
            return final_recs

        except Exception as e:
            print(f"[Backend] Erro recomendação: {e}")
            return []