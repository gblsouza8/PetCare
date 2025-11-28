import tkinter as tk
from tkinter import messagebox, ttk
from supabase import create_client, Client
from datetime import date
import os
import sys

# --- CONFIGURAÇÕES DO SUPABASE (Anon Key) ---
# ATENÇÃO: Embora este código use a Anon Key, para operações de ESCRITA (salvar relatório),
# a RLS (Row Level Security) deve estar devidamente configurada no Supabase para permitir
# que o usuário 'admin' simulado realize o UPSERT na tabela 'relatorios'.
SUPABASE_URL = 'https://jweuedxsfrxjkzkdbkas.supabase.co'
SUPABASE_ANON_KEY = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Imp3ZXVlZHhzZnJ4amt6a2Ria2FzIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NjM0OTA4MDcsImV4cCI6MjA3OTA2NjgwN30.0FnNI4RXLgwE0fkL1HJ9Qgi9hglLtKmdfbuxARrraFs'

class VetClinicApp:
    def __init__(self, master):
        self.master = master
        master.title("PetCare - Gestão de Consultas")
        # --- ALTERAÇÃO PRINCIPAL AQUI: NOVA RESOLUÇÃO 1280x720 ---
        master.geometry("1280x720") 
        
        # Inicializa o cliente Supabase
        self.supabase: Client = create_client(SUPABASE_URL, SUPABASE_ANON_KEY)
        
        self.style = ttk.Style()
        self.style.configure("TNotebook.Tab", font=("Arial", 12, "bold"), padding=[10, 5])
        # Ajuste o tamanho da fonte padrão para maior densidade
        self.style.configure("TLabel", font=("Arial", 9)) 

        # Variáveis de Estado
        self.is_vet_authenticated = False
        self.consultas_vet_map = {} # Mapeia índice da listbox para o ID da consulta
        
        # --- Estrutura da UI ---
        self.notebook = ttk.Notebook(master)
        self.notebook.pack(pady=10, padx=10, expand=True, fill="both")

        # Abas
        self.aba_recepcao = ttk.Frame(self.notebook, padding="10")
        self.aba_veterinario = ttk.Frame(self.notebook, padding="10")
        
        self.notebook.add(self.aba_recepcao, text="Recepção (Status das Consultas)")
        self.notebook.add(self.aba_veterinario, text="Veterinário (Relatórios)")

        # Inicializa as abas
        self.setup_aba_recepcao()
        self.setup_aba_veterinario()

    # --- ABA RECEPÇÃO (STATUS DAS CONSULTAS) ---
    def setup_aba_recepcao(self):
        
        # Frame de Controles (para o botão de Atualizar)
        self.recepcao_controles = ttk.Frame(self.aba_recepcao)
        self.recepcao_controles.pack(fill="x", pady=5)
        
        # BOTÃO DE ATUALIZAÇÃO 
        ttk.Button(self.recepcao_controles, text="🔄 Atualizar Todas as Listas", command=self.carregar_consultas).pack(side="right", padx=10)
        
        # Frame principal da Recepção
        self.recepcao_frame = ttk.Frame(self.aba_recepcao)
        self.recepcao_frame.pack(expand=True, fill="both")
        
        # Configurar 3 colunas para o grid
        self.recepcao_frame.columnconfigure(0, weight=1)
        self.recepcao_frame.columnconfigure(1, weight=1)
        self.recepcao_frame.columnconfigure(2, weight=1)

        # 1. Agendamentos
        self.frame_agendamentos = self._create_column_frame(self.recepcao_frame, 0, "Agendamentos - Chegada do Cliente")
        # Altura aumentada para preencher a nova resolução (antes 15)
        self.list_agendamentos = self._create_listbox(self.frame_agendamentos, height_val=20, font_size=8) 
        self.list_agendamentos.pack(expand=True, fill="both", padx=5, pady=5)
        self.btn_iniciar_atendimento = ttk.Button(self.frame_agendamentos, text="Iniciar Atendimento", command=self.mover_para_atendimento)
        self.btn_iniciar_atendimento.pack(pady=5)
        
        # 2. Em Atendimento
        self.frame_atendimento = self._create_column_frame(self.recepcao_frame, 1, "Em Atendimento - Doutor com o Pet")
        # Altura aumentada para preencher a nova resolução (antes 15)
        self.list_atendimento = self._create_listbox(self.frame_atendimento, height_val=20, font_size=8) 
        self.list_atendimento.pack(expand=True, fill="both", padx=5, pady=5)
        # O botão "Finalizar e Pagar" foi removido.
        
        # 3. Finalizadas
        self.frame_finalizadas = self._create_column_frame(self.recepcao_frame, 2, "Finalizadas - Consulta Concluída")
        # Altura aumentada para preencher a nova resolução (antes 15)
        self.list_finalizadas = self._create_listbox(self.frame_finalizadas, height_val=20, font_size=8) 
        self.list_finalizadas.pack(expand=True, fill="both", padx=5, pady=5)

        # Carregar dados iniciais e configurar refresh
        self.carregar_consultas()
        # O refresh automático foi mantido, mas o botão dá controle manual
        self.master.after(30000, self.carregar_consultas) # Refresh a cada 30 segundos
        
    def _create_column_frame(self, parent, col, title):
        frame = ttk.Frame(parent, borderwidth=2, relief="groove")
        frame.grid(row=0, column=col, sticky="nsew", padx=10, pady=10)
        
        ttk.Label(frame, text=title, font=("Arial", 11, "bold"), background="#e0f7fa", padding=5).pack(fill="x")
        
        return frame
        
    def _create_listbox(self, parent, height_val=15, font_size=10):
        # Usando o parâmetro height_val que foi ajustado
        listbox = tk.Listbox(parent, height=height_val, font=("Courier", font_size), selectmode=tk.SINGLE)
        return listbox

    def _format_consulta_display(self, item, include_tutor=True):
        """Formata o texto de exibição, tratando nulos nas relações e extraindo o primeiro nome do tutor."""
        
        # Extrai o nome completo do tutor de forma segura
        tutor_nome_completo = item.get('tutores', {}).get('nome', '[Tutor N/A]') if item.get('tutores') else '[Tutor N/A]'
        
        # Extrai apenas o primeiro nome do tutor
        if tutor_nome_completo != '[Tutor N/A]':
            tutor_primeiro_nome = tutor_nome_completo.split(' ')[0]
        else:
            tutor_primeiro_nome = tutor_nome_completo # Mantém o fallback
            
        pet_nome = item.get('pets', {}).get('nome', '[Pet N/A]') if item.get('pets') else '[Pet N/A]'
        especialidade_nome = item.get('especialidades', {}).get('nome', '[Especialidade N/A]') if item.get('especialidades') else '[Especialidade N/A]'

        # Formata a data e hora
        data_iso = item.get('data_consulta', '0000-00-00').split('-')
        data_formatada = f"{data_iso[2]}/{data_iso[1]}/{data_iso[0]}" if len(data_iso) == 3 else '[Data N/A]'
        hora_consulta = item.get('hora_consulta', '00:00')[:5]
        
        # Monta a string de exibição
        parts = []
        parts.append(f"[{data_formatada}] {hora_consulta}h")
        if include_tutor:
             # Usa o primeiro nome aqui
             parts.append(tutor_primeiro_nome) 
        parts.append(pet_nome)
        parts.append(especialidade_nome)
        
        display_text = " - ".join(parts) + f" (ID:{item.get('id', 'N/A')})"
        return display_text

    # --- LÓGICA DE DADOS RECEPÇÃO ---
    def carregar_consultas(self):
        
        try:
            # Buscar TODAS as consultas com JOIN
            # A ordenação principal é DECRESCENTE (mais recentes no topo)
            response = self.supabase.from_('consultas').select(
                'id, data_consulta, hora_consulta, status, tutores(nome), pets(nome), especialidades(nome)'
            ).order('data_consulta', desc=True).order('hora_consulta', desc=True).execute()
            
            data = response.data
            
            # Limpa Listboxes
            self.list_agendamentos.delete(0, tk.END)
            self.list_atendimento.delete(0, tk.END)
            self.list_finalizadas.delete(0, tk.END)
            
            if not data:
                print("DEBUG: Resposta do Supabase vazia. Verifique se há dados e as RLS.")
                self.list_agendamentos.insert(tk.END, "Nenhuma consulta agendada encontrada.")
                self.list_atendimento.insert(tk.END, "Nenhuma consulta em andamento encontrada.")
                self.list_finalizadas.insert(tk.END, "Nenhuma consulta finalizada encontrada.")
                return
            
            print(f"DEBUG: {len(data)} consultas carregadas com sucesso.")

            # Listas temporárias para separar e reordenar Agendamentos
            list_agendamentos_temp = []
            list_atendimento_temp = []
            list_finalizadas_temp = []

            for item in data:
                try:
                    display_text = self._format_consulta_display(item, include_tutor=True)
                    
                    if item['status'] == 1: # Agendada
                        list_agendamentos_temp.append(display_text)
                    elif item['status'] == 2: # Em Atendimento
                        list_atendimento_temp.append(display_text)
                    elif item['status'] == 3: # Finalizada
                        list_finalizadas_temp.append(display_text)
                except Exception as item_e:
                    print(f"Erro ao processar item ID {item.get('id', 'N/A')}: {item_e}. Dados: {item}")
            
            # 1. Agendamentos (Ordem CRESCENTE - mais próximos primeiro)
            # A lista temporária está em ordem DECRESCENTE. Invertendo, fica CRESCENTE.
            list_agendamentos_temp.reverse()
            for text in list_agendamentos_temp:
                 self.list_agendamentos.insert(tk.END, text)

            # 2. Em Atendimento (Ordem DECRESCENTE - mais recente primeiro)
            for text in list_atendimento_temp:
                self.list_atendimento.insert(tk.END, text)

            # 3. Finalizadas (Ordem DECRESCENTE - mais recente primeiro)
            for text in list_finalizadas_temp:
                self.list_finalizadas.insert(tk.END, text)
                        
        except Exception as e:
            print(f"Erro ao carregar consultas (Supabase/Rede): {e}")
            messagebox.showerror("Erro de Dados", "Não foi possível conectar ao Supabase ou carregar os dados das consultas. Verifique sua conexão e RLS.")
            
    def _get_selected_consulta_id(self, listbox):
        try:
            selection = listbox.curselection()
            if not selection:
                return None
            
            selected_item = listbox.get(selection[0])
            # Extrai o ID da consulta do final da string
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
            # Tentar atualizar no Supabase
            response = self.supabase.from_('consultas').update({'status': new_status}).eq('id', consulta_id).execute()
            
            if response.data:
                messagebox.showinfo("Sucesso", f"Status da consulta {consulta_id} atualizado para {new_status}.")
                self.carregar_consultas() # Recarregar a lista para refletir a mudança
            else:
                messagebox.showerror("Erro", "Falha ao atualizar o status da consulta. Verifique RLS ou ID.")
                
        except Exception as e:
            messagebox.showerror("Erro de Atualização", f"Erro: {e}")

    def mover_para_atendimento(self):
        self._update_consulta_status(self.list_agendamentos, 2)
        
    # --- ABA VETERINÁRIO (RELATÓRIOS) ---
    def setup_aba_veterinario(self):
        # Frame de Login (Inicialmente cobre a aba)
        self.login_frame = ttk.Frame(self.aba_veterinario)
        self.login_frame.pack(expand=True, fill="both")
        self.login_frame.columnconfigure(0, weight=1)
        self.login_frame.rowconfigure(0, weight=1)

        login_center = ttk.Frame(self.login_frame, padding="20")
        login_center.grid(row=0, column=0)
        
        ttk.Label(login_center, text="Login do Veterinário", font=("Arial", 16, "bold")).grid(row=0, column=0, columnspan=2, pady=10)
        
        ttk.Label(login_center, text="Usuário (admin):").grid(row=1, column=0, sticky="w", pady=5)
        self.vet_user_entry = ttk.Entry(login_center, width=20)
        self.vet_user_entry.grid(row=1, column=1, pady=5, padx=5)
        
        ttk.Label(login_center, text="Senha (1234):").grid(row=2, column=0, sticky="w", pady=5)
        self.vet_pass_entry = ttk.Entry(login_center, width=20, show="*")
        self.vet_pass_entry.grid(row=2, column=1, pady=5, padx=5)
        
        ttk.Button(login_center, text="Entrar", command=self.autenticar_veterinario).grid(row=3, column=0, columnspan=2, pady=15)

        # Frame de Relatórios (Oculto até o login)
        self.relatorio_frame = ttk.Frame(self.aba_veterinario)
        self.relatorio_frame.pack_forget() 
        self.relatorio_frame.columnconfigure(0, weight=1)
        # A linha 4 (relatorio_text) deve ter peso para expandir verticalmente
        self.relatorio_frame.rowconfigure(4, weight=1) 
        
        # Linha 0: Título e Botão de Atualizar
        relatorio_header_frame = ttk.Frame(self.relatorio_frame)
        relatorio_header_frame.grid(row=0, column=0, sticky="ew", pady=10)
        relatorio_header_frame.columnconfigure(0, weight=1) # Faz o título expandir
        
        ttk.Label(relatorio_header_frame, text="Registro e Edição de Relatórios Veterinários", font=("Arial", 14, "bold")).grid(row=0, column=0, sticky="w")
        
        # BOTÃO DE ATUALIZAÇÃO 
        ttk.Button(relatorio_header_frame, text="🔄 Atualizar Lista de Consultas", command=self.carregar_consultas_para_relatorio).grid(row=0, column=1, sticky="e", padx=5)

        # Linha 1: Lista de Consultas
        ttk.Label(self.relatorio_frame, text="1. Selecione a Consulta (Em Atendimento):").grid(row=1, column=0, sticky="nw", padx=5)
        # Altura aumentada para preencher a nova resolução (antes 8)
        self.vet_consulta_list = tk.Listbox(self.relatorio_frame, height=12, font=("Courier", 8), selectmode=tk.SINGLE) 
        self.vet_consulta_list.grid(row=2, column=0, sticky="nsew", padx=5, pady=5)
        self.vet_consulta_list.bind('<<ListboxSelect>>', self.carregar_relatorio_existente)
        
        # Linha 3: Título da Área do Relatório
        ttk.Label(self.relatorio_frame, text="2. Relatório Médico Completo (Diagnóstico e Tratamento):").grid(row=3, column=0, sticky="w", pady=5)

        # Linha 4: Área do Relatório (UNIFICADA)
        # Altura aumentada para preencher a nova resolução (antes 20)
        self.relatorio_text = tk.Text(self.relatorio_frame, height=30, width=80, font=("Arial", 9), wrap="word") 
        self.relatorio_text.grid(row=4, column=0, sticky="nsew", padx=5, pady=5)
        
        # Linha 5: Botão de Ação
        ttk.Button(self.relatorio_frame, text="Enviar e Salvar Relatório", command=self.salvar_relatorio).grid(row=5, column=0, pady=10)


    # --- LÓGICA DE DADOS VETERINÁRIO ---
    def autenticar_veterinario(self):
        user = self.vet_user_entry.get()
        password = self.vet_pass_entry.get()
        
        # Login e Senha Simples (admin, 1234)
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
            # 💥 ALTERAÇÃO AQUI: Buscar SOMENTE consultas com status 'Em Atendimento' (2)
            response = self.supabase.from_('consultas').select(
                'id, data_consulta, hora_consulta, status, tutores(nome), pets(nome), especialidades(nome)'
            ).eq('status', 2).order('data_consulta', desc=True).order('hora_consulta', desc=True).execute()
            
            data = response.data
            self.vet_consulta_list.delete(0, tk.END)
            self.consultas_vet_map = {} # Mapeia índice da listbox para o ID da consulta

            if not data:
                print("DEBUG: Nenhuma consulta Em Atendimento encontrada no banco de dados.")
                self.vet_consulta_list.insert(tk.END, "Nenhuma consulta Em Atendimento.")
                return

            for i, item in enumerate(data):
                try:
                    # include_tutor=False para focar no Pet
                    display_text = self._format_consulta_display(item, include_tutor=False)
                    
                    self.vet_consulta_list.insert(tk.END, display_text)
                    self.consultas_vet_map[i] = item['id']
                except Exception as item_e:
                    print(f"Erro ao processar item ID {item.get('id', 'N/A')} para relatório: {item_e}. Dados: {item}")
                
        except Exception as e:
            print(f"Erro ao carregar consultas para relatório (Supabase/Rede): {e}")
            messagebox.showerror("Erro de Dados", "Não foi possível carregar as consultas para relatório.")

    def carregar_relatorio_existente(self, event):
        self.relatorio_text.delete(1.0, tk.END) # Limpa o campo único
        
        try:
            # Garante que haja uma seleção
            selection = self.vet_consulta_list.curselection()
            if not selection:
                return 

            selection_index = selection[0]
            consulta_id = self.consultas_vet_map.get(selection_index)
            
            if not consulta_id:
                return # Nenhuma seleção válida

            # Buscar relatório existente na tabela 'relatorios' (assumindo o nome original)
            response = self.supabase.from_('relatorios').select('relatorio').eq('consulta_id', consulta_id).execute()
            
            if response.data and response.data[0] and response.data[0].get('relatorio'):
                # Popula o campo único com o relatório completo
                self.relatorio_text.insert(tk.END, response.data[0]['relatorio'])
            else:
                self.relatorio_text.insert(tk.END, "Nenhum relatório anterior para esta consulta. Digite aqui o diagnóstico e o tratamento.")
                
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao carregar relatório: {e}")

    def salvar_relatorio(self):
        try:
            selection = self.vet_consulta_list.curselection()
            if not selection:
                raise IndexError # Força a captura da exceção para notificação
                
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
                    self.carregar_consultas_para_relatorio() # Atualiza a lista do veterinário, removendo a consulta
                else:
                    messagebox.showwarning("Aviso", "Relatório salvo, mas falha ao marcar a consulta como 'Finalizada'.")
                    self.carregar_consultas_para_relatorio()

            else:
                messagebox.showerror("Erro", "Falha ao salvar o relatório. Verifique as permissões de escrita (RLS).")

        except Exception as e:
            messagebox.showerror("Erro de Banco de Dados", f"Erro: {e}")

if __name__ == "__main__":
    # Verifica se a biblioteca supabase-py está instalada
    try:
        from supabase import create_client
    except ImportError:
        print("A biblioteca 'supabase-py' é necessária.")
        print("Instale-a com: pip install supabase")
        sys.exit(1)

    root = tk.Tk()
    app = VetClinicApp(root)
    root.mainloop()