import customtkinter as ctk
import sys
import threading
import requests
from PIL import Image
from io import BytesIO
from backend_logic import Sistema

ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("dark-blue")

class PrintRedirector:
    def __init__(self, text_widget):
        self.text_widget = text_widget

    def write(self, string):
        if not string: return
        try:
            self.text_widget.configure(state="normal")
            self.text_widget.insert("end", string)
            self.text_widget.see("end")
            self.text_widget.configure(state="disabled")
        except: pass

    def flush(self): pass

class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        
        # Configurações Globais
        self.font_main = "Arial"
        self.colors = {
            "bg_dark": "#1c1c1c",
            "bg_med": "#2b2b2b",
            "accent": "#8c47ff",
            "accent_hover": "#6e37cc",
            "text_white": "#ffffff",
            "placeholder": ["#FF9900", "#00A651", "#00BBDD", "#8C47FF"]
        }

        self.sistema = Sistema()
        self.lista_albuns_usuario = []
        
        self.title("KNAlbuns - Recomendador de álbuns com KNN")
        self.geometry("1280x720")
        
        # Configuração do Grid Principal
        self.grid_columnconfigure((0, 1), weight=1)
        self.grid_columnconfigure(2, weight=1, minsize=400)
        self.grid_rowconfigure(2, weight=1)

        # Inicialização da Interface
        self._setup_background()
        self._setup_menu()
        self._setup_left_panel()   # Coluna 0
        self._setup_center_panel() # Coluna 1
        self._setup_right_panel()  # Coluna 2

        # Redirecionamento do Print
        sys.stdout = PrintRedirector(self.terminal)

    def _carregar_imagem(self, path, size):
        """Helper para carregar e redimensionar imagens com segurança."""
        try:
            img = Image.open(path)
            if size[1] == 0: 
                w, h = img.size
                size = (size[0], int(size[0] * (h / w)))
            
            return ctk.CTkImage(img, img, size=size)
        except Exception as e:
            print(f"Erro imagem ({path}): {e}")
            return None

    def _truncar_texto(self, texto, limite):
        return (texto[:limite] + '..') if len(texto) > limite else texto

    def _setup_background(self):
        bg_ctk = self._carregar_imagem("./fundo.png", (1280, 720))
        if bg_ctk:
            bg_label = ctk.CTkLabel(self, image=bg_ctk, text="")
            bg_label.place(relx=0, rely=0, relwidth=1, relheight=1)

    def _setup_menu(self):
        menu_bar = ctk.CTkFrame(self, height=30, fg_color=self.colors["bg_dark"], corner_radius=0)
        menu_bar.grid(row=0, column=0, columnspan=3, sticky="new")
        
        menu_frame = ctk.CTkFrame(menu_bar, height=30, fg_color="transparent")
        menu_frame.pack(side="left", padx=10)
        
        for btn_text in ["Opções", "Editar", "Arquivo"]:
            ctk.CTkButton(menu_frame, text=btn_text, fg_color="transparent",
                          text_color="#f0f0f0", hover_color="#3c3c3c",
                          width=60, height=20, font=(self.font_main, 12)).pack(side="left", padx=5)

    def _setup_left_panel(self):
        # 1. Frame KNN (Imagem/Logo)
        knn_frame = ctk.CTkFrame(self, fg_color=self.colors["bg_med"])
        knn_frame.grid(row=1, column=0, sticky="ew", padx=10, pady=(10, 5))
        
        ctk.CTkLabel(knn_frame, text="Recomendador de álbuns com KNN", 
                     font=(self.font_main, 16, "bold")).pack(padx=10, pady=(10, 5), anchor="w")
        
        img_knn = self._carregar_imagem("./KNAlbuns.png", (200, 0))
        if img_knn:
            ctk.CTkLabel(knn_frame, text="", image=img_knn).pack(padx=10, pady=(0, 10), anchor="w")
        else:
            ctk.CTkButton(knn_frame, text="Img Off", width=180).pack(padx=10, pady=(0, 10))

        # 2. Terminal
        term_container = ctk.CTkFrame(self, fg_color=self.colors["bg_med"])
        term_container.grid(row=2, column=0, sticky="nsew", padx=10, pady=(5, 10))
        
        ctk.CTkLabel(term_container, text="Terminal", 
                     font=(self.font_main, 16, "bold")).pack(padx=10, pady=(10, 5), anchor="w")

        self.terminal = ctk.CTkTextbox(term_container, fg_color=self.colors["bg_dark"], 
                                       text_color=self.colors["text_white"], 
                                       font=(self.font_main, 13), wrap="word", state="disabled")
        self.terminal.pack(padx=10, pady=(0, 10), fill="both", expand=True)

    def _setup_center_panel(self):
        # 1. Input
        input_frame = ctk.CTkFrame(self, fg_color=self.colors["bg_med"])
        input_frame.grid(row=1, column=1, sticky="ew", padx=10, pady=(10, 5))
        
        ctk.CTkLabel(input_frame, text="Insira o nome do álbum:", 
                     font=(self.font_main, 16, "bold")).pack(padx=10, pady=(10, 5), anchor="w")
        
        entry_cont = ctk.CTkFrame(input_frame, fg_color="transparent")
        entry_cont.pack(fill="x", padx=10, pady=(0, 10))

        self.entry = ctk.CTkEntry(entry_cont, placeholder_text="Ex: The Dark Side of the Moon",
                                  height=35, fg_color=self.colors["bg_dark"], border_width=0,
                                  font=(self.font_main, 14))
        self.entry.pack(side="left", expand=True, fill="x")
        self.entry.bind("<Return>", lambda e: self.adicionar_album())

        # 2. Lista e Ações
        list_container = ctk.CTkFrame(self, fg_color=self.colors["bg_med"])
        list_container.grid(row=2, column=1, sticky="nsew", padx=10, pady=(5, 10))

        # Controles (Slider + Botões)
        actions_frame = ctk.CTkFrame(list_container, fg_color="transparent")
        actions_frame.pack(fill="x", padx=10, pady=(10, 5))

        slider_frame = ctk.CTkFrame(actions_frame, fg_color="transparent")
        slider_frame.pack(fill="x")
        
        self.lbl_qtd = ctk.CTkLabel(slider_frame, text="Qtd de Recomendações: 05", font=(self.font_main, 12, "bold"))
        self.lbl_qtd.pack(side="left", padx=(0, 5))
        
        self.slider = ctk.CTkSlider(slider_frame, from_=1, to=12, number_of_steps=11, 
                                    command=lambda v: self.lbl_qtd.configure(text=f"Qtd de Recomendações: {int(v):02}"), height=10)
        self.slider.set(5)
        self.slider.pack(side="left", fill="x", expand=True)

        btn_frame = ctk.CTkFrame(actions_frame, fg_color="transparent")
        btn_frame.pack(fill="x", pady=(5, 0))

        self.btn_rec = ctk.CTkButton(btn_frame, text="Gerar Recomendações",
                                     fg_color=self.colors["accent"], hover_color=self.colors["accent_hover"],
                                     command=self.iniciar_recomendacao, height=35)
        self.btn_rec.pack(side="left", expand=True, fill="x", padx=(0, 5))
        
        ctk.CTkButton(btn_frame, text="Limpar", width=80, fg_color="#505050", hover_color="#666666",
                      command=self.limpar, height=35).pack(side="right")

        ctk.CTkLabel(list_container, text="Lista de Álbuns:", font=(self.font_main, 16, "bold")).pack(padx=10, pady=(10, 5), anchor="w")
        
        self.list_scroll = ctk.CTkScrollableFrame(list_container, fg_color=self.colors["bg_dark"], label_text=None)
        self.list_scroll.pack(padx=10, pady=(0, 10), fill="both", expand=True)
        self.list_scroll.columnconfigure(0, weight=1)

    def _setup_right_panel(self):
        self.results_container = ctk.CTkFrame(self, fg_color=self.colors["bg_med"])
        self.results_container.grid(row=1, column=2, rowspan=2, sticky="nsew", padx=10, pady=10)
        
        ctk.CTkLabel(self.results_container, text="Álbuns Recomendados:", font=(self.font_main, 18, "bold")).pack(pady=15)
        
        self.scroll_results = ctk.CTkScrollableFrame(self.results_container, fg_color="transparent")
        self.scroll_results.pack(fill="both", expand=True, padx=5, pady=5)
        self.scroll_results.columnconfigure((0, 1), weight=1)

    # --- Lógica ---

    def adicionar_album(self):
        nome = self.entry.get()
        if not nome: return
        self.entry.delete(0, "end")
        threading.Thread(target=self._buscar_backend, args=(nome,)).start()

    def _buscar_backend(self, nome):
        status, dados = self.sistema.buscar_candidatos(nome)
        if status == 'CACHE_HIT':
            self.after(0, lambda: self._add_visual(dados))
            print(f"Cache: {dados}")
        elif status == 'API_OPTIONS':
            self.after(0, lambda: self._popup_escolha(dados))
        elif status == 'NOT_FOUND':
            print(f"Não encontrado: {nome}")

    def _popup_escolha(self, candidatos):
        popup = ctk.CTkToplevel(self)
        popup.title("Escolha o Álbum")
        popup.geometry("400x400")
        popup.attributes("-topmost", True)
        
        scroll = ctk.CTkScrollableFrame(popup)
        scroll.pack(fill="both", expand=True, padx=10, pady=10)
        
        for cand in candidatos:
            ctk.CTkButton(scroll, text=f"{cand['titulo']}\n{cand['artista']}", anchor="w",
                          fg_color=self.colors["bg_med"], hover_color=self.colors["accent"], height=50,
                          font=(self.font_main, 12),
                          command=lambda c=cand, p=popup: [p.destroy(), threading.Thread(target=self._processar_novo, args=(c,)).start()]
                          ).pack(fill="x", pady=2)

    def _processar_novo(self, candidato):
        if self.sistema.processar_escolha_usuario(candidato['objeto'], candidato['titulo'], candidato['artista']):
            self.after(0, lambda: self._add_visual(candidato['titulo']))

    def _add_visual(self, nome):
        if nome in self.lista_albuns_usuario: return
        self.lista_albuns_usuario.append(nome)
        row = len(self.lista_albuns_usuario) - 1
        ctk.CTkLabel(self.list_scroll, text=f"• {nome}", anchor="w", 
                     font=(self.font_main, 20), height=25).grid(row=row, column=0, sticky="ew", padx=10, pady=1)

    def limpar(self):
        self.lista_albuns_usuario.clear()
        for w in self.list_scroll.winfo_children(): w.destroy()
        for w in self.scroll_results.winfo_children(): w.destroy()

    def iniciar_recomendacao(self):
        if not self.lista_albuns_usuario:
            print("Adicione álbuns para gerar recomendações.")
            return
        
        self.btn_rec.configure(state="disabled", text="BUSCANDO...")
        for w in self.scroll_results.winfo_children(): w.destroy()
        
        threading.Thread(target=self._thread_recomendacao, args=(int(self.slider.get()),)).start()

    def _thread_recomendacao(self, qtd):
        print("\n=== INICIANDO RECOMENDAÇÃO ===")
        print(f"Busca original: {self.lista_albuns_usuario}")

        recomendacoes = self.sistema.gerar_recomendacoes_com_detalhes(self.lista_albuns_usuario, qtd=qtd)

        print(f">>> TOP {qtd:02} RECOMENDAÇÕES <<<")
        for i, item in enumerate(recomendacoes, 1):
            print(f"{i}: {item['album']} ({item['score']:.1f}%)")

        print("\n=== DOWNLOAD DAS IMAGENS ===")
        
        session = requests.Session()
        final_data = []

        for item in recomendacoes:
            img_tk = None
            url = item.get('image_url')
            if url:
                try:
                    print(f"Baixando: {item['album']}")
                    resp = session.get(url, timeout=10)
                    if resp.status_code == 200:
                        img_pil = Image.open(BytesIO(resp.content))
                        img_tk = ctk.CTkImage(light_image=img_pil, dark_image=img_pil, size=(160, 160))
                except Exception as e:
                    print(f"Erro download {item['album']}: {e}")

            item['image_obj'] = img_tk
            final_data.append(item)

        print("\n=== FINALIZADO ===\n")
        self.after(0, lambda: self._mostrar_resultados(final_data))

    def _mostrar_resultados(self, dados):
        self.btn_rec.configure(state="normal", text="Gerar Recomendações")
        for i, item in enumerate(dados):
            self.criar_card(i, item)

    def criar_card(self, index, item):
        card = ctk.CTkFrame(self.scroll_results, fg_color="transparent")
        card.grid(row=index//2, column=index%2, padx=10, pady=10)
        card.columnconfigure(0, weight=1)

        # Match Score
        ctk.CTkLabel(card, text=f"{item.get('score', 0):.1f}% Match", 
                     font=(self.font_main, 14, "bold"), text_color="#00bdb6").grid(row=0, column=0, sticky="w", pady=(0, 5))

        # Imagem ou Placeholder
        if item['image_obj']:
            ctk.CTkLabel(card, text="", image=item['image_obj'], corner_radius=0).grid(row=1, column=0)
        else:
            color = self.colors["placeholder"][index % len(self.colors["placeholder"])]
            placeholder = ctk.CTkFrame(card, width=160, height=160, fg_color=color, corner_radius=0)
            placeholder.grid(row=1, column=0)
            placeholder.grid_propagate(False)
            ctk.CTkLabel(placeholder, text="Foto do album", 
                         font=(self.font_main, 14, "bold")).place(relx=0.5, rely=0.5, anchor="center")

        ctk.CTkLabel(card, text=self._truncar_texto(item['album'], 18), 
                     font=(self.font_main, 14, "bold")).grid(row=2, column=0, sticky="w", pady=(5, 0))
        
        ctk.CTkLabel(card, text=self._truncar_texto(item['artist'], 22), 
                     font=(self.font_main, 11), text_color="gray").grid(row=3, column=0, sticky="w")

if __name__ == "__main__":
    app = App()
    app.mainloop()