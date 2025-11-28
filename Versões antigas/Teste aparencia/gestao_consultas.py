import tkinter as tk
from tkinter import messagebox, ttk
from supabase import create_client, Client
from datetime import date
import os
import sys

# --- CONFIGURAÇÕES DO SUPABASE (Anon Key) ---
SUPABASE_URL = 'https://jweuedxsfrxjkzkdbkas.supabase.co'
SUPABASE_ANON_KEY = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Imp3ZXVlZHhzZnJ4amt6a2Ria2FzIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NjM0OTA4MDcsImV4cCI6MjA3OTA2NjgwN30.0FnNI4RXLgwE0fkL1HJ9Qgi9hglLtKmdfbuxARrraFs'

class VetClinicApp:
    def __init__(self, master):
        self.master = master
        master.title("PetCare - Gestão de Consultas")
        master.geometry("1280x600") 
        # ESTILO: Fundo cinza claro
        master.configure(bg="#f4f4f5") 
        
        # Inicializa o cliente Supabase
        self.supabase: Client = create_client(SUPABASE_URL, SUPABASE_ANON_KEY)
        
        self.style = ttk.Style()
        
        # 💥 Tenta usar o tema 'clam' que respeita mais o background
        if 'clam' in self.style.theme_names():
            self.style.theme_use('clam')
        elif 'default' in self.style.theme_names():
            self.style.theme_use('default')
        
        # --- CONSTANTES DE COR ---
        ROXO_PRIMARIO = "#7e22ce" # purple-700
        ROXO_HOVER = "#6b21a8"   # purple-800
        
        self.titulo_cor = ROXO_PRIMARIO
        self.cor_selecao = ROXO_PRIMARIO 

        # Estilo de cor de fundo padrão para os TTK Frames (Cinza Claro)
        self.style.configure("TFrame", background="#f4f4f5") 
        self.style.configure("TNotebook.Tab", font=("Arial", 12, "bold"), padding=[10, 5])
        self.style.configure("TLabel", font=("Arial", 9)) 

        # 🟣 Estilo Customizado para os 'Cards' com BORDA ROXA 🟣
        self.style.configure("Card.TFrame", 
            background="white", 
            relief="solid", 
            borderwidth=1, 
            bordercolor=self.titulo_cor 
        )
        
        # 🟣 Configuração da cor roxa nos BOTÕES 🟣
        self.style.configure("Primary.TButton", 
            font=("Arial", 10, "bold"), 
            foreground="white", 
            background=ROXO_PRIMARIO, 
            padding=6,
            relief="flat", 
            borderwidth=0, 
            focuscolor=ROXO_PRIMARIO 
        )
        self.style.map("Primary.TButton",
            background=[('active', ROXO_HOVER), ('pressed', ROXO_HOVER)],
            foreground=[('active', 'white'), ('pressed', 'white')]
        )
        # --- FIM DO ESTILO ---

        # Variáveis de Estado
        self.is_vet_authenticated = False
        self.consultas_vet_map = {} 
        
        # --- Estrutura da UI ---
        self.notebook = ttk.Notebook(master)
        self.notebook.pack(pady=10, padx=10, expand=True, fill="both")

        # Abas
        self.aba_recepcao = ttk.Frame(self.notebook, padding="10", style="TFrame")
        self.aba_veterinario = ttk.Frame(self.notebook, padding="10", style="TFrame")
        
        self.notebook.add(self.aba_recepcao, text="Recepção (Status das Consultas)")
        self.notebook.add(self.aba_veterinario, text="Veterinário (Relatórios)")

        # Inicializa as abas
        self.setup_aba_recepcao() 
        self.setup_aba_veterinario()


    # --- ABA RECEPÇÃO (STATUS DAS CONSULTAS) ---
    def setup_aba_recepcao(self):
        
        # Frame de Controles (para o botão de Atualizar)
        self.recepcao_controles = ttk.Frame(self.aba_recepcao, style="TFrame")
        self.recepcao_controles.pack(fill="x", pady=5)
        
        # BOTÃO DE ATUALIZAÇÃO (Estilo Padrão, Secundário)
        ttk.Button(self.recepcao_controles, text="🔄 Atualizar Todas as Listas", command=self.carregar_consultas).pack(side="right", padx=10)
        
        # Frame principal da Recepção
        self.recepcao_frame = ttk.Frame(self.aba_recepcao, style="TFrame")
        self.recepcao_frame.pack(expand=True, fill="both")
        
        # Configurar 3 colunas para o grid
        self.recepcao_frame.columnconfigure(0, weight=1)
        self.recepcao_frame.columnconfigure(1, weight=1)
        self.recepcao_frame.columnconfigure(2, weight=1)

        # 1. Agendamentos (CARD)
        self.frame_agendamentos = self._create_column_frame(self.recepcao_frame, 0, "Agendamentos - Chegada do Cliente")
        self.list_agendamentos = self._create_listbox(self.frame_agendamentos, height_val=20, font_size=8) 
        self.list_agendamentos.pack(expand=True, fill="both", padx=10, pady=5)
        # ESTILO: Botão Primário (Roxo)
        self.btn_iniciar_atendimento = ttk.Button(self.frame_agendamentos, text="Iniciar Atendimento", command=self.mover_para_atendimento, style="Primary.TButton")
        self.btn_iniciar_atendimento.pack(pady=10, padx=10, fill="x")
        
        # 2. Em Atendimento (CARD)
        self.frame_atendimento = self._create_column_frame(self.recepcao_frame, 1, "Em Atendimento - Doutor com o Pet")
        self.list_atendimento = self._create_listbox(self.frame_atendimento, height_val=20, font_size=8) 
        self.list_atendimento.pack(expand=True, fill="both", padx=10, pady=10)
        
        # 3. Finalizadas (CARD)
        self.frame_finalizadas = self._create_column_frame(self.recepcao_frame, 2, "Finalizadas - Consulta Concluída")
        self.list_finalizadas = self._create_listbox(self.frame_finalizadas, height_val=20, font_size=8) 
        self.list_finalizadas.pack(expand=True, fill="both", padx=10, pady=10)

        # Carregar dados iniciais e configurar refresh
        self.carregar_consultas()
        self.master.after(30000, self.carregar_consultas) 
        
    def _create_column_frame(self, parent, col, title):
        # ESTILO: Usa o estilo 'Card.TFrame' (fundo branco com borda roxa)
        frame = ttk.Frame(parent, style="Card.TFrame")
        frame.grid(row=0, column=col, sticky="nsew", padx=10, pady=10)
        
        # 🟣 ALTERAÇÃO: Frame Roxo para simular a Borda do Título 🟣
        border_frame = tk.Frame(frame, bg=self.titulo_cor, bd=0)
        border_frame.pack(fill="x", padx=5, pady=5) # Adiciona margem interna ao frame principal
        
        # Título (Label branca interna)
        tk.Label(
            border_frame, # Anexado ao frame roxo
            text=title, 
            font=("Arial", 11, "bold"), 
            bg="white", 
            fg=self.titulo_cor, 
            anchor="w", 
            padx=10, 
            pady=8
        ).pack(fill="both", padx=1, pady=1) # Margem de 1px (borda) dentro do frame roxo
        
        return frame
        
    def _create_listbox(self, parent, height_val=15, font_size=10):
        # 🟣 Cor de fundo e de seleção roxa para Listbox 🟣
        listbox = tk.Listbox(parent, 
                             height=height_val, 
                             font=("Courier", font_size), 
                             selectmode=tk.SINGLE, 
                             bd=0, 
                             highlightthickness=0,
                             selectbackground=self.cor_selecao,
                             selectforeground="white" 
                            )
        return listbox

    def _format_consulta_display(self, item, include_tutor=True):
        """Formata o texto de exibição, tratando nulos nas relações e extraindo o primeiro nome do tutor."""
        
        tutor_nome_completo = item.get('tutores', {}).get('nome', '[Tutor N/A]') if item.get('tutores') else '[Tutor N/A]'
        
        if tutor_nome_completo != '[Tutor N/A]':
            tutor_primeiro_nome = tutor_nome_completo.split(' ')[0]
        else:
            tutor_primeiro_nome = tutor_nome_completo 
            
        pet_nome = item.get('pets', {}).get('nome', '[Pet N/A]') if item.get('pets') else '[Pet N/A]'
        especialidade_nome = item.get('especialidades', {}).get('nome', '[Especialidade N/A]') if item.get('especialidades') else '[Especialidade N/A]'

        data_iso = item.get('data_consulta', '0000-00-00').split('-')
        data_formatada = f"{data_iso[2]}/{data_iso[1]}/{data_iso[0]}" if len(data_iso) == 3 else '[Data N/A]'
        hora_consulta = item.get('hora_consulta', '00:00')[:5]
        
        parts = []
        parts.append(f"[{data_formatada}] {hora_consulta}h")
        if include_tutor:
             parts.append(tutor_primeiro_nome) 
        parts.append(pet_nome)
        parts.append(especialidade_nome)
        
        display_text = " - ".join(parts) + f" (ID:{item.get('id', 'N/A')})"
        return display_text

    # --- LÓGICA DE DADOS RECEPÇÃO (Sem Alterações na Lógica) ---
    def carregar_consultas(self):
        
        try:
            response = self.supabase.from_('consultas').select(
                'id, data_consulta, hora_consulta, status, tutores(nome), pets(nome), especialidades(nome)'
            ).order('data_consulta', desc=True).order('hora_consulta', desc=True).execute()
            
            data = response.data
            
            self.list_agendamentos.delete(0, tk.END)
            self.list_atendimento.delete(0, tk.END)
            self.list_finalizadas.delete(0, tk.END)
            
            if not data:
                print("DEBUG: Resposta do Supabase vazia. Verifique se há dados e as RLS.")
                self.list_agendamentos.insert(tk.END, "Nenhuma consulta agendada encontrada.")
                self.list_atendimento.insert(tk.END, "Nenhuma consulta em andamento encontrada.")
                self.list_finalizadas.insert(tk.END, "Nenhuma consulta finalizada encontrada.")
                return

            list_agendamentos_temp = []
            list_atendimento_temp = []
            list_finalizadas_temp = []

            for item in data:
                try:
                    display_text = self._format_consulta_display(item, include_tutor=True)
                    
                    if item['status'] == 1: 
                        list_agendamentos_temp.append(display_text)
                    elif item['status'] == 2: 
                        list_atendimento_temp.append(display_text)
                    elif item['status'] == 3: 
                        list_finalizadas_temp.append(display_text)
                except Exception as item_e:
                    print(f"Erro ao processar item ID {item.get('id', 'N/A')}: {item_e}. Dados: {item}")
            
            # Agendamentos (Ordem CRESCENTE)
            list_agendamentos_temp.reverse()
            for text in list_agendamentos_temp:
                 self.list_agendamentos.insert(tk.END, text)

            # Em Atendimento (Ordem DECRESCENTE)
            for text in list_atendimento_temp:
                self.list_atendimento.insert(tk.END, text)

            # Finalizadas (Ordem DECRESCENTE)
            for text in list_finalizadas_temp:
                self.list_finalizadas.insert(tk.END, text)
                        
        except Exception as e:
            print(f"Erro ao carregar consultas (Supabase/Rede): {e}")
            messagebox.showerror("Erro de Dados", "Não foi possível conectar ao Supabase ou carregar os dados das consultas.")
            
    def _get_selected_consulta_id(self, listbox):
        try:
            selection = listbox.curselection()
            if not selection:
                return None
            
            selected_item = listbox.get(selection[0])
            start_index = selected_item.rfind('(ID:')
            end_index = selected_item.rfind(')')
            if start_index != -1 and end_index != -1 and end_index > start_index:
                 return int(selected_item[start_index + 4:end_index])
            return None
        except:
            return None

    def _update_consulta_status(self, listbox, new_status):
        consulta_id = self._get_selected_consulta_id(listbox)
        if not consulta_id:
            messagebox.showwarning("Seleção", "Por favor, selecione uma consulta válida.")
            return

        try:
            response = self.supabase.from_('consultas').update({'status': new_status}).eq('id', consulta_id).execute()
            
            if response.data:
                messagebox.showinfo("Sucesso", f"Status da consulta {consulta_id} atualizado para {new_status}.")
                self.carregar_consultas() 
            else:
                messagebox.showerror("Erro", "Falha ao atualizar o status da consulta. Verifique RLS ou ID.")
                
        except Exception as e:
            messagebox.showerror("Erro de Atualização", f"Erro: {e}")

    def mover_para_atendimento(self):
        self._update_consulta_status(self.list_agendamentos, 2)
        
    # --- ABA VETERINÁRIO (RELATÓRIOS) ---
    def setup_aba_veterinario(self):
        # Frame de Login (Inicialmente cobre a aba)
        self.login_frame = ttk.Frame(self.aba_veterinario, style="TFrame")
        self.login_frame.pack(expand=True, fill="both")
        self.login_frame.columnconfigure(0, weight=1)
        self.login_frame.rowconfigure(0, weight=1)

        # ESTILO: Login centralizado em um card discreto
        login_center = ttk.Frame(self.login_frame, padding="20", style="Card.TFrame") 
        login_center.grid(row=0, column=0)
        
        tk.Label(login_center, text="Login do Veterinário", font=("Arial", 16, "bold"), bg="white").grid(row=0, column=0, columnspan=2, pady=10)
        
        tk.Label(login_center, text="Usuário (admin):", bg="white").grid(row=1, column=0, sticky="w", pady=5)
        self.vet_user_entry = ttk.Entry(login_center, width=20)
        self.vet_user_entry.grid(row=1, column=1, pady=5, padx=5)
        
        tk.Label(login_center, text="Senha (1234):", bg="white").grid(row=2, column=0, sticky="w", pady=5)
        self.vet_pass_entry = ttk.Entry(login_center, width=20, show="*")
        self.vet_pass_entry.grid(row=2, column=1, pady=5, padx=5)
        
        # ESTILO: Botão Primário (Roxo)
        ttk.Button(login_center, text="Entrar", command=self.autenticar_veterinario, style="Primary.TButton").grid(row=3, column=0, columnspan=2, pady=15, sticky="ew")

        # Frame de Relatórios (Oculto até o login)
        self.relatorio_frame = ttk.Frame(self.aba_veterinario, style="TFrame")
        self.relatorio_frame.pack_forget() 
        self.relatorio_frame.columnconfigure(0, weight=1)
        self.relatorio_frame.rowconfigure(4, weight=1) 
        
        # Linha 0: Título e Botão de Atualizar
        relatorio_header_frame = ttk.Frame(self.relatorio_frame, style="TFrame")
        relatorio_header_frame.grid(row=0, column=0, sticky="ew", pady=10)
        relatorio_header_frame.columnconfigure(0, weight=1) 
        
        ttk.Label(relatorio_header_frame, text="Registro e Edição de Relatórios Veterinários", font=("Arial", 14, "bold")).grid(row=0, column=0, sticky="w")
        
        ttk.Button(relatorio_header_frame, text="🔄 Atualizar Lista de Consultas", command=self.carregar_consultas_para_relatorio).grid(row=0, column=1, sticky="e", padx=5)

        # Linha 1/2: Lista de Consultas (DENTRO DE UM CARD)
        ttk.Label(self.relatorio_frame, text="1. Selecione a Consulta (Em Atendimento):", background="#f4f4f5").grid(row=1, column=0, sticky="nw", padx=5)
        
        # ESTILO: Card para a Listbox
        list_card_frame = ttk.Frame(self.relatorio_frame, style="Card.TFrame")
        list_card_frame.grid(row=2, column=0, sticky="nsew", padx=5, pady=5)
        list_card_frame.columnconfigure(0, weight=1)
        list_card_frame.rowconfigure(0, weight=1)
        
        # ESTILO: Listbox sem bordas, dentro do card. 
        self.vet_consulta_list = self._create_listbox(list_card_frame, height_val=12, font_size=8)
        self.vet_consulta_list.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)
        self.vet_consulta_list.bind('<<ListboxSelect>>', self.carregar_relatorio_existente)
        
        # Linha 3: Título da Área do Relatório
        ttk.Label(self.relatorio_frame, text="2. Relatório Médico Completo (Diagnóstico e Tratamento):", background="#f4f4f5").grid(row=3, column=0, sticky="w", pady=5)

        # Linha 4: Área do Relatório (DENTRO DE UM CARD)
        # ESTILO: Card para o Text Widget
        report_card_frame = ttk.Frame(self.relatorio_frame, style="Card.TFrame")
        report_card_frame.grid(row=4, column=0, sticky="nsew", padx=5, pady=5)
        report_card_frame.columnconfigure(0, weight=1)
        report_card_frame.rowconfigure(0, weight=1)
        
        # 🟣 Text Widget com cor de seleção roxa 🟣
        self.relatorio_text = tk.Text(report_card_frame, 
                                      height=30, 
                                      width=80, 
                                      font=("Arial", 9), 
                                      wrap="word", 
                                      bd=0, 
                                      highlightthickness=0,
                                      selectbackground=self.cor_selecao,
                                      selectforeground="white"
                                     ) 
        self.relatorio_text.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)
        
        # Linha 5: Botão de Ação
        # ESTILO: Botão Primário (Roxo)
        ttk.Button(self.relatorio_frame, text="Enviar e Salvar Relatório", command=self.salvar_relatorio, style="Primary.TButton").grid(row=5, column=0, pady=10, sticky="ew", padx=5)


    # --- LÓGICA DE DADOS VETERINÁRIO (Sem Alterações na Lógica) ---
    def autenticar_veterinario(self):
        user = self.vet_user_entry.get()
        password = self.vet_pass_entry.get()
        
        if user == "admin" and password == "1234":
            self.is_vet_authenticated = True
            self.login_frame.pack_forget()
            self.relatorio_frame.pack(expand=True, fill="both")
            self.carregar_consultas_para_relatorio()
            messagebox.showinfo("Sucesso", "Login do Veterinário realizado.")
        else:
            messagebox.showerror("Erro de Login", "Usuário ou senha inválidos.")

    def carregar_consultas_para_relatorio(self):
        
        try:
            # Buscar SOMENTE consultas com status 'Em Atendimento' (2)
            response = self.supabase.from_('consultas').select(
                'id, data_consulta, hora_consulta, status, tutores(nome), pets(nome), especialidades(nome)'
            ).eq('status', 2).order('data_consulta', desc=True).order('hora_consulta', desc=True).execute()
            
            data = response.data
            self.vet_consulta_list.delete(0, tk.END)
            self.consultas_vet_map = {} 

            if not data:
                self.vet_consulta_list.insert(tk.END, "Nenhuma consulta Em Atendimento.")
                return

            for i, item in enumerate(data):
                try:
                    display_text = self._format_consulta_display(item, include_tutor=False)
                    self.vet_consulta_list.insert(tk.END, display_text)
                    self.consultas_vet_map[i] = item['id']
                except Exception as item_e:
                    print(f"Erro ao processar item ID {item.get('id', 'N/A')} para relatório: {item_e}. Dados: {item}")
                
        except Exception as e:
            messagebox.showerror("Erro de Dados", "Não foi possível carregar as consultas para relatório.")

    def carregar_relatorio_existente(self, event):
        self.relatorio_text.delete(1.0, tk.END) 
        
        try:
            selection = self.vet_consulta_list.curselection()
            if not selection:
                return 

            selection_index = selection[0]
            consulta_id = self.consultas_vet_map.get(selection_index)
            
            if not consulta_id:
                return 

            response = self.supabase.from_('relatorios').select('relatorio').eq('consulta_id', consulta_id).execute()
            
            if response.data and response.data[0] and response.data[0].get('relatorio'):
                self.relatorio_text.insert(tk.END, response.data[0]['relatorio'])
            else:
                self.relatorio_text.insert(tk.END, "Nenhum relatório anterior para esta consulta. Digite aqui o diagnóstico e o tratamento.")
                
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao carregar relatório: {e}")

    def salvar_relatorio(self):
        try:
            selection = self.vet_consulta_list.curselection()
            if not selection:
                raise IndexError 
                
            selection_index = selection[0]
            consulta_id = self.consultas_vet_map.get(selection_index)
            if not consulta_id:
                raise IndexError
                
        except IndexError:
            messagebox.showwarning("Seleção", "Por favor, selecione uma consulta na lista.")
            return
            
        relatorio_content = self.relatorio_text.get(1.0, tk.END).strip()
        
        if not relatorio_content:
            messagebox.showwarning("Conteúdo", "O relatório completo não pode estar vazio.")
            return

        try:
            # 1. Tentar inserir/atualizar (upsert) o relatório
            response = self.supabase.from_('relatorios').upsert([
                {'consulta_id': consulta_id, 'relatorio': relatorio_content}
            ], on_conflict='consulta_id').execute() 

            if response.data:
                
                # 2. Mudar o status da consulta para FINALIZADA (3)
                update_status_response = self.supabase.from_('consultas').update({'status': 3}).eq('id', consulta_id).execute()

                if update_status_response.data:
                    messagebox.showinfo("Sucesso", f"Relatório salvo e consulta marcada como 'Finalizada' (ID: {consulta_id}).")
                    self.carregar_consultas_para_relatorio() 
                else:
                    messagebox.showwarning("Aviso", "Relatório salvo, mas falha ao marcar a consulta como 'Finalizada'.")
                    self.carregar_consultas_para_relatorio()

            else:
                messagebox.showerror("Erro", "Falha ao salvar o relatório. Verifique as permissões de escrita (RLS).")

        except Exception as e:
            messagebox.showerror("Erro de Banco de Dados", f"Erro: {e}")

if __name__ == "__main__":
    try:
        from supabase import create_client
    except ImportError:
        print("A biblioteca 'supabase-py' é necessária.")
        print("Instale-a com: pip install supabase")
        sys.exit(1)

    root = tk.Tk()
    app = VetClinicApp(root)
    root.mainloop()