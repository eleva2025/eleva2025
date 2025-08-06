from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, session
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
import os
import requests
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
import json
from unidecode import unidecode



app = Flask(__name__)
app.secret_key = os.getenv('FLASK_SECRET_KEY', 'sua_chave_secreta_aqui')

# Configurações do Xano
XANO_BASE_URL = os.getenv('XANO_BASE_URL', "https://xidg-u2cu-sa8e.n7c.xano.io/api:loOqZbWF")
XANO_API_KEY = os.getenv('XANO_API_KEY', "eyJhbGciOiJBMjU2S1ciLCJlbmMiOiJBMjU2Q0JDLUhTNTEyIiwiemlwIjoiREVGIn0.aRt3MssA75PtosO2lpbxDvlqAp1bMatG2Eopn64GTYTx7KtxuO918R9gxw-9Qh4luNIRt8UpI7xiFnwJiv0duNXtKl5ZojML.iv2L64zizo-y_iemPIFARA.dLJ2JhSRikH9OgPaa03zD51Jb3q5KKYchkIPjWvxfkv-EGP5USRpHXqdsjXxMnGWcgG3g8Xt3gFtKMnSDaH1X3bBD3ndZfXUUmcsb4Q43xAycaWjY2d8-K3soa4MLaUyr57NWG5A-lgCDcEPwFpgaQ.fUKabyMbdHyjMdUBsNfB8QYPqDgcLzQEkc-HtnaMm1M")
# Estrutura das tabelas no Xano
XANO_TABLES = {
    'users': 'user_eleva',
    'disciplines': 'disciplines_eleva',
    'contents': 'contents_eleva',
    'grades': 'grades_eleva',
    'messages': 'messages_eleva',
    'student_disciplines': 'student_disciplines_eleva',
    'professor_disciplines': 'professor_disciplines_eleva',
    'respostas_prova':'respostas_prova',
    'respostas_prova_1':'respostas_prova_1',
    'respostas_prova_2':'respostas_prova_2',
    'pesquisa_nps_respostas':'pesquisa_nps_respostas',
    'respostas_prova_3':'respostas_prova_3',
    'respostas_prova_5':'respostas_prova_5',
    'respostas_prova_6':'respostas_prova_6',
    'respostas_prova_7':'respostas_prova_7',
    'respostas_prova_8':'respostas_prova_8',
    'respostas_prova_9':'respostas_prova_9',
    'respostas_prova_10':'respostas_prova_10',
    'respostas_prova_11':'respostas_prova_11',
    'respostas_prova_12':'respostas_prova_12',
    'prova_gestao_talentos':'prova_gestao_talentos',
    'prova_lideranca_situacional':'prova_lideranca_situacional',
    'prova_cultura_organizacional':'prova_cultura_organizacional',
    'prova_gestao_tal':'prova_gestao_tal',
    'prova_autoconhecimento':'prova_autoconhecimento',
    'prova_profissional_futuro':'prova_profissional_futuro',
    'prova_metorneilider':'prova_metorneilider',
    'prova_inteligencia_emocional':'prova_inteligencia_emocional',
    'prova_comunicacao_assertiva':'prova_comunicacao_assertiva',
    'prova_gestao_conflitos':'prova_gestao_conflitos',
    'prova_gestao_estrategica':'prova_gestao_estrategica',
    'prova_cultura_feedback':'prova_cultura_feedback',
    'prova_gestao_equipe':'prova_gestao_equipe,'
}

# Configuração do Flask-Login
login_manager = LoginManager()
from functools import wraps

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            return redirect(url_for('login'))
        if current_user.role != 'admin':
            flash('Acesso restrito a administradores', 'error')
            return redirect(url_for('index'))
        return f(*args, **kwargs)
    return decorated_function

login_manager.init_app(app)
login_manager.login_view = 'login'

class User(UserMixin):
    def __init__(self, user_id, username, role):
        self.id = user_id
        self.username = username
        self.role = role

def xano_request(method, table_key, data=None, params=None, id=None):
    table_name = XANO_TABLES.get(table_key)
    if not table_name:
        raise ValueError(f"Tabela {table_key} não configurada")
    
    endpoint = f'/{table_name}'
    if id is not None:
        endpoint += f'/{id}'
    
    url = f"{XANO_BASE_URL}{endpoint}"
    headers = {
        "Authorization": f"Bearer {XANO_API_KEY}",
        "Content-Type": "application/json"
    }
    
    try:
        print(f"DEBUG: Fazendo requisição {method} para {url}")
        print(f"DEBUG: Dados enviados: {data}")
        print(f"DEBUG: Parâmetros: {params}")
        
        # Métodos específicos para cada verbo HTTP
        if method.upper() == 'GET':
            response = requests.get(url, params=params, headers=headers, timeout=15)
        elif method.upper() == 'POST':
            response = requests.post(url, json=data, headers=headers, timeout=15)
        elif method.upper() == 'PUT':
            response = requests.put(url, json=data, headers=headers, timeout=15)
        elif method.upper() == 'PATCH':
            response = requests.patch(url, json=data, headers=headers, timeout=15)  # ← CORREÇÃO AQUI
        elif method.upper() == 'DELETE':
            response = requests.delete(url, headers=headers, timeout=15)
        else:
            raise ValueError(f"Método HTTP não suportado: {method}")
        
        print(f"DEBUG: Status Code: {response.status_code}")
        print(f"DEBUG: Resposta: {response.text}")
        
        if response.status_code == 404:
            return None
        
        if response.status_code >= 400:
            error_msg = response.json().get('message', response.text)
            raise Exception(f"Erro {response.status_code}: {error_msg}")
            
        return response.json() if response.content else None
        
    except requests.exceptions.RequestException as e:
        print(f"ERRO na requisição ao Xano: {str(e)}")
        raise

@login_manager.user_loader
def load_user(user_id):
    try:
        # Busca específica incluindo o campo de senha
        user_data = xano_request('GET', 'users', id=user_id)
        
        if user_data:
            print(f"DEBUG: Usuário carregado: {user_data}")
            return User(user_data['id'], user_data['username'], user_data['role'])
        
        print(f"DEBUG: Usuário ID {user_id} não encontrado")
        return None
        
    except Exception as e:
        print(f"ERRO ao carregar usuário: {str(e)}")
        return None

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('home'))

    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '').strip()

        if not username or not password:
            flash('Preencha todos os campos', 'error')
            return redirect(url_for('login'))

        try:
            # Busca específica no Xano
            params = {
                'username': f'"{username}"',
                '_fields': 'id,username,role,password,created_at'
            }
            
            users = xano_request('GET', 'users', params=params)
            
            if not users or not isinstance(users, list):
                flash('Erro ao buscar usuário', 'error')
                return redirect(url_for('login'))
            
            user_data = next((u for u in users if u.get('username') == username), None)
            
            if not user_data:
                flash('Usuário não encontrado', 'error')
                return redirect(url_for('login'))
            
            print(f"DEBUG: Dados do usuário: {user_data}")
            
            # Autenticação direta (para desenvolvimento)
            user_obj = User(user_data['id'], user_data['username'], user_data['role'])
            login_user(user_obj)
            
            # Debug da sessão
            print(f"DEBUG: Usuário autenticado - ID: {user_obj.id}")
            print(f"DEBUG: Role do usuário: {user_obj.role}")
            print(f"DEBUG: Session: {dict(session)}")
            
            # Redirecionamento seguro
            next_page = request.args.get('next')
            if not next_page or not next_page.startswith('/'):
                if user_obj.role == 'admin':
                    next_page = url_for('admin_dashboard')
                elif user_obj.role == 'teacher':
                    next_page = url_for('professor_dashboard')
                else:
                    next_page = url_for('student_dashboard')
            
            return redirect(next_page)
            
        except Exception as e:
            print(f"ERRO no login: {str(e)}")
            flash('Erro durante o login. Tente novamente.', 'error')
            return redirect(url_for('login'))

    return render_template('login.html')

# Rota temporária para diagnóstico
@app.route('/debug_user/<username>')
def debug_user(username):
    user = xano_request('GET', 'users', params={'username': username})
    return jsonify({
        'api_response': user,
        'expected_structure': {
            'id': 'number',
            'username': 'string',
            'password': 'string',
            'role': 'string'
        }
    })
    

from flask import render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from datetime import datetime

@app.route('/pesquisa_nps_gestao', methods=['GET', 'POST'])
@login_required
def pesquisa_nps_gestao():
    nome_aula = request.args.get('aula', 'Aula Genérica')
    username = current_user.username.strip() if current_user.username else "Desconhecido"

    perguntas = [
        "O conteúdo da aula foi relevante para minha jornada como líder.",
        "O(a) facilitador(a) conduziu a aula com clareza e domínio do tema.",
        "As dinâmicas, exemplos e explicações foram aplicáveis ao meu contexto de trabalho.",
        "O tempo da aula foi adequado ao conteúdo proposto.",
        "Consegui me manter engajado(a) durante a aula.",
        "Essa aula contribuiu para meu desenvolvimento profissional.",
        "A estrutura da aula (apresentação, atividades, interação) foi bem organizada."
    ]

    if request.method == 'POST':
        # Coleta e sanitização dos dados
        respostas = {
            'username': username,
            'aula': request.form.get('aula', '').strip(),
            'r1': int(request.form.get('r1', 0)),
            'r2': int(request.form.get('r2', 0)),
            'r3': int(request.form.get('r3', 0)),
            'r4': int(request.form.get('r4', 0)),
            'r5': int(request.form.get('r5', 0)),
            'r6': int(request.form.get('r6', 0)),
            'r7': int(request.form.get('r7', 0)),
            'r8': request.form.get('r8', '').strip(),
            'r9': request.form.get('r9', '').strip(),
            'r10': request.form.get('r10', '').strip(),
            'data_envio': datetime.utcnow().isoformat()
        }

        print("🔍 DEBUG - RESPOSTAS A ENVIAR:")
        for k, v in respostas.items():
            print(f"{k}: {v}")

        try:
            resultado = xano_request('POST', 'pesquisa_nps_respostas', data=respostas)
            print("✅ Envio ao Xano bem-sucedido:")
            print(resultado)
            flash('Pesquisa enviada com sucesso!', 'success')
        except Exception as e:
            print(f"❌ ERRO AO ENVIAR PARA XANO: {str(e)}")
            flash('Erro ao enviar a pesquisa. Tente novamente.', 'error')

        return redirect(url_for('student_dashboard'))

    # GET: renderiza o formulário
    return render_template(
        'pesquisa_nps_gestao.html',
        nome_aula=nome_aula,
        username=username,
        perguntas=perguntas
    )


@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('home'))

@app.route('/')
def home():
    try:
        if not current_user.is_authenticated:
            return render_template('page eleva/index.html')
        
        if current_user.role == 'student':
            return redirect(url_for('student_dashboard'))
        elif current_user.role == 'teacher':
            return redirect(url_for('professor_dashboard'))
        elif current_user.role == 'admin':
            return redirect(url_for('admin_dashboard'))
        
        return redirect(url_for('login'))
    except Exception as e:
        print(f"ERRO na rota principal: {str(e)}")
        return redirect(url_for('login'))

@app.route('/student_dashboard')
@login_required
def student_dashboard():
    if current_user.role != 'student':
        return redirect(url_for('home'))

    try:
        # Buscar disciplinas do aluno
        raw_disciplines = xano_request('GET', 'student_disciplines', params={'student_id': current_user.id}) or []

        # Buscar todas as disciplinas e criar o mapa
        all_disciplines = xano_request('GET', 'disciplines') or []
        discipline_map = {int(d['id']): d['name'] for d in all_disciplines}

        disciplines = []
        discipline_ids = set()

        for d in raw_disciplines:
            discipline_id = int(d['discipline_id'])

            if discipline_id in discipline_ids:
                continue

            provas = []

            if discipline_id == 6:
                respostas = []
                respostas_1 = []
                respostas_2 = []
                respostas_3 = []
                respostas_5 = []
                respostas_6 = []
                respostas_7 = []
                respostas_8 = []
                respostas_9 = []
                respostas_10 = []
                respostas_11 = []
                respostas_12 = []
                try:
                    respostas = xano_request('GET', 'prova_autoconhecimento') or []
                    respostas_1 = xano_request('GET', 'prova_gestao_tal') or []
                    respostas_2 = xano_request('GET', 'prova_lideranca_situacional') or []
                    respostas_3 = xano_request('GET', 'prova_cultura_organizacional') or []
                    respostas_5 = xano_request('GET', 'prova_profissional_futuro') or []
                    respostas_6 = xano_request('GET', 'prova_metorneilider') or []
                    respostas_7 = xano_request('GET', 'prova_inteligencia_emocional') or []
                    respostas_8 = xano_request('GET', 'prova_comunicacao_assertiva') or []
                    respostas_9 = xano_request('GET', 'prova_gestao_conflitos') or []
                    respostas_10 = xano_request('GET', 'prova_gestao_estrategica') or []
                    respostas_11 = xano_request('GET', 'prova_cultura_feedback') or []
                    respostas_12 = xano_request('GET', 'prova_gestao_equipe') or []
                except Exception as e:
                    print(f"Erro ao consultar respostas: {e}")

                usuario = unidecode(current_user.username.strip().lower())

                def nome_bate(resp):
                    nome = unidecode(resp.get('aluno_nome', '').strip().lower())
                    return usuario in nome or nome in usuario

                provas = [
                    {
                        "url": url_for('prova', disciplina_id=discipline_id),
                        "label": "Gestão de Talentos e Sucessão",
                        "respondida": any(nome_bate(r) for r in respostas_1)
                    },
                    {
                        "url": url_for('prova2', disciplina_id=discipline_id),
                        "label": "Liderança Situacional e Fortalecimento da Cultura",
                        "respondida": any(nome_bate(r) for r in respostas_2)
                    },
                    {
                        "url": url_for('prova3', disciplina_id=discipline_id),
                        "label": "Cultura Organizacional e Bem-Estar",
                        "respondida": any(nome_bate(r) for r in respostas_3)
                    },
                    {
                        "url": url_for('prova4', disciplina_id=discipline_id),
                        "label": "Autoconhecimento e Propósito",
                        "respondida": any(nome_bate(r) for r in respostas)
                    },
                    {
                        "url": url_for('prova5', disciplina_id=discipline_id),
                        "label": "Competências do Profissional do Futuro",
                        "respondida": any(nome_bate(r) for r in respostas_5)
                    },
                    {
                        "url": url_for('prova6', disciplina_id=discipline_id),
                        "label": "Me tornei líder, e agora?",
                        "respondida": any(nome_bate(r) for r in respostas_6)
                    },
                    {
                        "url": url_for('prova7', disciplina_id=discipline_id),
                        "label": "Inteligência Emocional e Saúde Mental para Líderes",
                        "respondida": any(nome_bate(r) for r in respostas_7)
                    },
                    {
                        "url": url_for('prova8', disciplina_id=discipline_id),
                        "label": "Comunicação Assertiva e Comunicação Não-Violenta",
                        "respondida": any(nome_bate(r) for r in respostas_8)
                    },
                    {
                        "url": url_for('prova9', disciplina_id=discipline_id),
                        "label": "Gestão de Conflitos e Resolução de Problemas",
                        "respondida": any(nome_bate(r) for r in respostas_9)
                    },
                    {
                        "url": url_for('prova10', disciplina_id=discipline_id),
                        "label": "Gestão Estratégica de Pessoas no Franchising",
                        "respondida": any(nome_bate(r) for r in respostas_10)
                    },
                    {
                        "url": url_for('prova11', disciplina_id=discipline_id),
                        "label": "Desenvolvimento da Cultura de Feedback",
                        "respondida": any(nome_bate(r) for r in respostas_11)
                    },
                    {
                        "url": url_for('prova12', disciplina_id=discipline_id),
                        "label": "Gestão de Equipes de Vendas e Negociação",
                        "respondida": any(nome_bate(r) for r in respostas_12)
                    },
                ]

            disciplines.append({
                'id': discipline_id,
                'name': discipline_map.get(discipline_id, 'Desconhecida'),
                'provas': provas
            })

            discipline_ids.add(discipline_id)


        for d in raw_disciplines:
            discipline_id = int(d['discipline_id'])

            if discipline_id in discipline_ids:
                continue

            provas = []
            prova_respondida = False

            if discipline_id == 6:
                provas = [
                    {"url": url_for('prova6', disciplina_id=discipline_id), "label": "Aula 06/06"},
                ]

                try:
                    resposta_existente = xano_request('GET', 'respostas_prova_6') or []
                    prova_respondida = any(
                        r.get('aluno_nome', '').strip().lower() == current_user.username.strip().lower()
                        for r in resposta_existente
                    )
                except Exception as e:
                    print(f"Erro ao verificar prova respondida: {str(e)}")
                    prova_respondida = False
            else:
                provas = []
                prova_respondida = False

            disciplines.append({
                'id': discipline_id,
                'name': discipline_map.get(discipline_id, 'Desconhecida'),
                'provas': provas,
                'prova_respondida': prova_respondida
            })

            discipline_ids.add(discipline_id)


        # Buscar notas
        grades = xano_request('GET', 'grades', params={'student_id': current_user.id}) or []
        processed_grades = []
        for grade in grades:
            discipline_name = discipline_map.get(grade.get('discipline_id'), 'Desconhecida')
            processed_grades.append({
                'name': discipline_name,
                'grade': grade.get('grade', 0),
                'frequency': grade.get('frequency', 0)
            })

        # Buscar mensagens
        messages = xano_request('GET', 'messages', params={'student_id': current_user.id}) or []

        # Buscar conteúdos
        conteudos_ids_adicionados = set()
        contents = []

        for discipline_id in discipline_ids:
            disciplina_conteudos = xano_request('GET', 'contents', params={'discipline_id': discipline_id}) or []

            for content in disciplina_conteudos:
                if content.get("id") in conteudos_ids_adicionados:
                    continue
                if content.get("discipline_id") != discipline_id:
                    continue

                content_dict = {
                    "id": content.get("id"),
                    "content": content.get("content"),
                    "title": content.get("title"),
                    "link": content.get("link"),
                    "discipline_id": content.get("discipline_id"),
                    "discipline_name": discipline_map.get(discipline_id, "Desconhecida"),
                    "created_at": content.get("created_at")
                }

                contents.append(content_dict)
                conteudos_ids_adicionados.add(content["id"])

        # ✅ Aulas com pesquisas NPS habilitadas
        aulas_disponiveis = [
            {"nome": "Aula Magna (Pedro Demetrius))"},
            {"nome": "15/05: Gestão de Talentos e Sucessão (Pedro Demetrius)"},
            {"nome": "20/05: Liderança Situacional e Fortalecimento da Cultura (Pedro Demetrius)"},
            {"nome": "22/05: Cultura Organizacional e Bem-estar (Alane Nascimento)"},
            {"nome": "27/05: Autoconhecimento e Propósito (Janaína Reis) "},
            {"nome": "03/06: Competências do Profissional do Futuro (Pedro Demetrius) "},
            {"nome": "06/06: Me tornei líder, e agora? (Maria Luiza Diniz) "},
            {"nome": "10/06: Inteligência Emocional e Saúde Mental para Líderes (Pedro Demetrius) "},
            {"nome": "17/06: Comunicação Assertiva e Comunicação Não-Violenta (Monique Zuza) "},
            {"nome": "24/06: Gestão de Conflitos e Resolução de Problemas (Giovanna Diniz) "},
            {"nome": "26/06: Gestão Estratégica de Pessoas no Franchising (Clarissa Medeiros) "},
            {"nome": "01/07: Desenvolvimento da Cultura de Feedback (Alane Nascimento) "},
            {"nome": "03/07: Gestão de Equipes de Vendas e Negociação (Fabiana Rodrigues) "},
            {"nome": "10/07: Gestão Financeira no Franchising (lexandre Custódio) "}
        ]

        # ✅ Renderiza o painel com todos os dados
        return render_template('student_dashboard.html',
                               disciplines=disciplines,
                               grades=processed_grades,
                               messages=messages,
                               contents=contents,
                               aulas_disponiveis=aulas_disponiveis)

    except Exception as e:
        print(f"ERRO no dashboard do aluno: {str(e)}")
        flash('Erro ao carregar dashboard', 'error')
        return redirect(url_for('home'))



    
@app.route('/send_message', methods=['POST'])
@login_required
def send_message():
    try:
        data = {
            'professor_id': current_user.id,
            'subject': request.form.get('assunto'),
            'content': request.form.get('mensagem'),
            'created_at': datetime.now().isoformat(),
            'is_read': False
        }

        # Adiciona student_id se foi selecionado um aluno específico
        if request.form.get('aluno'):
            data['student_id'] = request.form.get('aluno')
        
        # Adiciona discipline_id se foi selecionada uma disciplina
        if request.form.get('disciplina'):
            data['discipline_id'] = request.form.get('disciplina')

        # Envia para o Xano
        response = xano_request('POST', 'messages', data)
        
        if response:
            flash('Mensagem enviada com sucesso!', 'success')
            
            # Aqui você pode adicionar notificação em tempo real (opcional)
            # notify_student(data.get('student_id')) 
        else:
            flash('Erro ao enviar mensagem', 'error')

    except Exception as e:
        print(f"ERRO AO ENVIAR MENSAGEM: {str(e)}")
        flash('Erro interno ao enviar mensagem', 'error')
    
    return redirect(url_for('admin_dashboard' if current_user.role == 'admin' else 'professor_dashboard'))

@app.route('/professor_dashboard')
@login_required
def professor_dashboard():
    if current_user.role != 'teacher':
        return redirect(url_for('home'))

    try:
        # 1. Obter as disciplinas atribuídas ao professor
        professor_disciplines = xano_request(
            'GET', 
            'professor_disciplines',
            params={'professor_id': current_user.id}
        ) or []
        
        # 2. Obter detalhes completos de cada disciplina
        disciplines = []
        for pd in professor_disciplines:
            discipline = xano_request('GET', 'disciplines', id=pd['discipline_id'])
            if discipline:
                disciplines.append({
                    'id': discipline['id'],
                    'name': discipline['name'],
                    'professor_id': discipline.get('professor_id')
                })
        
        # 3. Obter conteúdos criados pelo professor
        contents_response = xano_request(
            'GET', 
            'contents',
            params={'professor_id': current_user.id}
        ) or []
        
        # 4. Processar conteúdos para incluir nome da disciplina
        contents = []
        for content in contents_response:
            discipline = next((d for d in disciplines if d['id'] == content['discipline_id']), None)
            if discipline:
                contents.append({
                    'id': content['id'],
                    'content': content['content'],
                    'date': content.get('created_at', ''),
                    'discipline_id': content['discipline_id'],
                    'discipline_name': discipline['name']
                })
        
        # Debug - Verificar os dados que estão sendo enviados para o template
        print("DEBUG - Disciplinas do professor:", disciplines)
        print("DEBUG - Conteúdos do professor:", contents)
        
        return render_template('professor_dashboard.html',
                            disciplines=disciplines,
                            contents=contents)
        
    except Exception as e:
        print(f"ERRO no dashboard do professor: {str(e)}")
        flash('Erro ao carregar dashboard', 'error')
        return redirect(url_for('home'))
    
@app.route('/add_content/<int:discipline_id>', methods=['GET', 'POST'])
@login_required
def add_content(discipline_id):
    if current_user.role != 'teacher':
        return redirect(url_for('home'))

    try:
        discipline = xano_request('GET', 'disciplines', id=discipline_id)
        if not discipline:
            flash('Disciplina não encontrada.', 'error')
            return redirect(url_for('professor_dashboard'))

        if request.method == 'POST':
            content = request.form.get('content')
            if not content:
                flash('Por favor, preencha o conteúdo.', 'error')
            else:
                xano_request('POST', 'contents', {
                    'professor_id': current_user.id,
                    'discipline_id': discipline_id,
                    'content': content,
                    'created_at': datetime.now().isoformat()
                })
                flash('Conteúdo adicionado com sucesso!', 'success')
                return redirect(url_for('professor_dashboard'))

        return render_template('add_content.html', discipline=discipline)
    except Exception as e:
        print(f"ERRO ao adicionar conteúdo: {str(e)}")
        flash('Erro ao adicionar conteúdo', 'error')
        return redirect(url_for('professor_dashboard'))

@app.route('/admin_dashboard', methods=['GET', 'POST'])
@login_required
def admin_dashboard():
    if current_user.role != 'admin':
        return redirect(url_for('home'))

    try:
        # Obter todos os dados
        users = xano_request('GET', 'users') or []
        disciplines = xano_request('GET', 'disciplines') or []
        teachers = [u for u in users if u.get('role') == 'teacher']
        students = [u for u in users if u.get('role') == 'student']
        grades = xano_request('GET', 'grades') or []
        professor_disciplines = xano_request('GET', 'professor_disciplines') or []
        student_disciplines = xano_request('GET', 'student_disciplines') or []

        # Criar mapeamentos para relacionamentos
        all_disciplines = xano_request('GET', 'disciplines') or []
        user_map = {u['id']: u['username'] for u in users}
        discipline_map = {int(d['id']): d['name'] for d in all_disciplines}

        professor_discipline_map = {(pd['professor_id'], pd['discipline_id']): pd for pd in professor_disciplines}

        # Processar histórico completo
        history = []
        for grade in grades:
            history.append({
                'student_id': grade['student_id'],
                'student_name': user_map.get(grade['student_id'], 'Desconhecido'),
                'discipline_id': grade['discipline_id'],
                'discipline_name': discipline_map.get(grade['discipline_id'], 'Desconhecida'),
                'grade': grade['grade'],
                'frequency': grade['frequency'],
                'professor_id': next((pd['professor_id'] for pd in professor_disciplines 
                                    if pd['discipline_id'] == grade['discipline_id']), None),
                'professor_name': user_map.get(next((pd['professor_id'] for pd in professor_disciplines 
                                                  if pd['discipline_id'] == grade['discipline_id']), None), 'Não atribuído'),
                'updated_at': grade.get('created_at', '')
            })

        # Ordenar histórico por disciplina e aluno
        history_sorted = sorted(history, key=lambda x: (x['discipline_name'], x['student_name']))

        # Processar dados para o template
        grades_dict = {(g['student_id'], g['discipline_id']): g for g in grades}

        # Lógica para filtrar por aluno
        selected_student = None
        student_grades = []
        student_id = request.args.get('student_id')
        
        if student_id:
            selected_student = next((s for s in students if s['id'] == int(student_id)), None)
            if selected_student:
                # Obter disciplinas do aluno
                student_disciplines = xano_request('GET', 'student_disciplines', 
                                                 params={'student_id': student_id}) or []
                
                # Obter notas do aluno
                student_grades_data = xano_request('GET', 'grades',
                                                 params={'student_id': student_id}) or []
                
                # Processar os dados para exibição
                for grade in student_grades_data:
                    discipline_id = grade['discipline_id']
                    discipline_name = discipline_map.get(discipline_id, 'Desconhecida')
                    
                    # Encontrar o professor da disciplina
                    professor_id = next((pd['professor_id'] for pd in professor_disciplines 
                                       if pd['discipline_id'] == discipline_id), None)
                    professor_name = user_map.get(professor_id, 'Não atribuído')
                    
                    student_grades.append({
                        'discipline_id': discipline_id,
                        'discipline_name': discipline_name,
                        'teacher_id': professor_id,
                        'teacher_name': professor_name,
                        'grade': grade.get('grade'),
                        'frequency': grade.get('frequency')
                    })

        # Cadastrar novo usuário
        if request.method == 'POST' and 'username' in request.form:
            username = request.form['username']
            password = request.form['password']
            role = request.form['role']

            if not all([username, password, role]):
                flash('Preencha todos os campos.', 'error')
            else:
                existing = next((u for u in users if u.get('username') == username), None)
                if existing:
                    flash('Nome de usuário já existe!', 'error')
                else:
                    xano_request('POST', 'users', {
                        'username': username,
                        'password': password,  # Em produção, use hash
                        'role': role,
                        'created_at': datetime.now().isoformat()
                    })
                    flash('Usuário cadastrado com sucesso!', 'success')
                    return redirect(url_for('admin_dashboard'))

        # Na rota admin_dashboard, dentro do bloco if request.method == 'POST' and 'disciplina' in request.form:
        if request.method == 'POST' and 'disciplina' in request.form:
            disciplina = request.form['disciplina'].strip()
            professor_id = request.form.get('professor')
            
            if not disciplina or not professor_id:
                flash('Preencha todos os campos.', 'error')
                return redirect(url_for('admin_dashboard'))
            
            try:
                # Verifica se a disciplina já existe
                existing_discipline = next((d for d in disciplines if d.get('name', '').lower() == disciplina.lower()), None)
                if existing_discipline:
                    flash('Disciplina já existe!', 'error')
                    return redirect(url_for('admin_dashboard'))
                
                # Verifica se o professor existe
                professor = next((t for t in teachers if str(t['id']) == str(professor_id)), None)
                if not professor:
                    flash('Professor não encontrado!', 'error')
                    return redirect(url_for('admin_dashboard'))
                
                # Cria a nova disciplina
                new_discipline = xano_request('POST', 'disciplines', {
                    'name': disciplina,
                    'professor_id': int(professor_id),
                    'created_at': datetime.now().isoformat()
                })
                
                if not new_discipline or 'id' not in new_discipline:
                    flash('Erro ao criar disciplina', 'error')
                    return redirect(url_for('admin_dashboard'))
                
                # Cria o relacionamento na tabela professor_disciplines
                relation_data = {
                    'professor_id': int(professor_id),
                    'discipline_id': new_discipline['id'],
                    'created_at': datetime.now().isoformat()
                }
                relation = xano_request('POST', 'professor_disciplines', relation_data)
                
                if not relation:
                    # Se falhou ao criar relação, remove a disciplina criada
                    xano_request('DELETE', 'disciplines', id=new_discipline['id'])
                    flash('Erro ao associar professor', 'error')
                    return redirect(url_for('admin_dashboard'))
                
                flash('Disciplina cadastrada com sucesso!', 'success')
                return redirect(url_for('admin_dashboard'))
                
            except requests.exceptions.RequestException as e:
                print(f"ERRO na requisição à API: {str(e)}")
                flash('Erro de conexão com o servidor', 'error')
            except ValueError as e:
                print(f"ERRO de valor: {str(e)}")
                flash('Erro nos dados enviados', 'error')
            except Exception as e:
                print(f"ERRO inesperado: {str(e)}")
                flash('Erro interno no sistema', 'error')
            
            return redirect(url_for('admin_dashboard'))

        # Atribuir disciplina ao aluno
        if request.method == 'POST' and 'aluno' in request.form and 'disciplina' in request.form:
            aluno_id = request.form['aluno']
            disciplina_id = request.form['disciplina']

            existing = next((sd for sd in xano_request('GET', 'student_disciplines') or [] 
                           if sd['student_id'] == aluno_id and sd['discipline_id'] == disciplina_id), None)
            
            if existing:
                flash('Aluno já está matriculado nesta disciplina!', 'warning')
            else:
                xano_request('POST', 'student_disciplines', {
                    'student_id': aluno_id,
                    'discipline_id': disciplina_id,
                    'created_at': datetime.now().isoformat()
                })
                flash('Disciplina atribuída com sucesso!', 'success')
                return redirect(url_for('admin_dashboard'))

        # Atribuir nota e frequência
        if request.method == 'POST' and 'nota' in request.form:
            aluno_id = request.form['aluno']
            disciplina_id = request.form['disciplina']
            nota = request.form['nota']
            frequencia = request.form.get('frequencia', 0)

            # Verifica se já existe uma nota para este aluno e disciplina
            existing_grade = next((g for g in grades 
                                if g['student_id'] == aluno_id and g['discipline_id'] == disciplina_id), None)
            
            if existing_grade:
                # Atualiza a nota existente
                xano_request('PATCH', 'grades', {
                    'grade': nota,
                    'frequency': frequencia
                }, id=existing_grade['id'])
            else:
                # Cria uma nova nota
                xano_request('POST', 'grades', {
                    'student_id': aluno_id,
                    'discipline_id': disciplina_id,
                    'grade': nota,
                    'frequency': frequencia,
                    'created_at': datetime.now().isoformat()
                })
            
            flash('Nota atualizada com sucesso!', 'success')
            return redirect(url_for('admin_dashboard'))

        # Enviar mensagem
        if request.method == 'POST' and 'assunto' in request.form:
            assunto = request.form['assunto']
            mensagem = request.form['mensagem']
            aluno_id = request.form.get('aluno')
            disciplina_id = request.form.get('disciplina')

            msg_data = {
                'professor_id': current_user.id,
                'assunto': assunto,
                'content': mensagem,
                'created_at': datetime.now().isoformat()
            }
            
            if aluno_id:
                msg_data['student_id'] = aluno_id
            if disciplina_id:
                msg_data['discipline_id'] = disciplina_id
                
            xano_request('POST', 'messages', msg_data)
            flash('Mensagem enviada com sucesso!', 'success')
            return redirect(url_for('admin_dashboard'))

        return render_template('admin_dashboard.html',
                            users=users,
                            disciplines=disciplines,
                            teachers=teachers,
                            students=students,
                            grades_dict=grades_dict,
                            professor_disciplines_dict=professor_discipline_map,
                            history=history_sorted,
                            selected_student=selected_student,
                            student_grades=student_grades)

    except Exception as e:
        print(f"ERRO no painel admin: {str(e)}")
        flash('Erro no painel de administração', 'error')
        return redirect(url_for('home'))


@app.route('/prova/<int:disciplina_id>', methods=['GET', 'POST'])
@login_required
def prova(disciplina_id):
    aluno_nome = current_user.username.strip()

    # ✅ Verificar se o aluno já respondeu usando apenas o aluno_nome
    try:
        resposta_existente = xano_request('GET', 'prova_gestao_tal', params={
            'aluno_nome': aluno_nome
        })
        # após o GET
        resposta_existente = xano_request('GET', 'prova_gestao_tal', params={
            'aluno_nome': aluno_nome
        })

        # filtra localmente por segurança
        ja_respondido = any(
            r.get('aluno_nome') == aluno_nome for r in resposta_existente
        )

    except Exception as e:
        print(f"❌ ERRO ao verificar resposta: {str(e)}")
        ja_respondido = False

    # Submissão da prova
    if request.method == 'POST':
        print("📥 POST recebido")

        if ja_respondido:
            print("⚠️ Prova já respondida - não enviando de novo.")
            flash("Você já respondeu esta prova.", "warning")
            return redirect(url_for('student_dashboard'))  # ✅ redireciona mesmo sem reenvio
        else:
            try:
                respostas = {
                    'q1': request.form.get('q1'),
                    'q2': request.form.get('q2'),
                    'q3': request.form.get('q3'),
                    'q4': request.form.get('q4'),
                    'q5': request.form.get('q5'),
                    'q6': request.form.get('q6'),
                    'q7': request.form.get('q7'),
                }

                payload = {
                    'aluno_nome': aluno_nome,
                    'respostas': json.dumps(respostas, ensure_ascii=False),
                    'created_at': datetime.now().isoformat()
                }

                xano_request('POST', 'prova_gestao_tal', data=payload)
                flash("Prova enviada com sucesso!", "success")
                return redirect(url_for('student_dashboard'))

            except Exception as e:
                print(f"❌ Erro ao enviar prova: {str(e)}")
                flash("Erro ao enviar a prova.", "error")


    return render_template('prova.html', 
                           aluno_nome=aluno_nome, 
                           disciplina_id=disciplina_id,
                           ja_respondido=ja_respondido)
    
@app.route('/prova4/<int:disciplina_id>', methods=['GET', 'POST'])
@login_required
def prova4(disciplina_id):
    aluno_nome = current_user.username.strip()

    # ✅ Verificar se o aluno já respondeu usando apenas o aluno_nome
    try:
        resposta_existente = xano_request('GET', 'prova_autoconhecimento', params={
            'aluno_nome': aluno_nome
        })
        # após o GET
        resposta_existente = xano_request('GET', 'prova_autoconhecimento', params={
            'aluno_nome': aluno_nome
        })

        # filtra localmente por segurança
        ja_respondido = any(
            r.get('aluno_nome') == aluno_nome for r in resposta_existente
        )

    except Exception as e:
        print(f"❌ ERRO ao verificar resposta: {str(e)}")
        ja_respondido = False

    # Submissão da prova
    if request.method == 'POST':
        print("📥 POST recebido")

        if ja_respondido:
            print("⚠️ Prova já respondida - não enviando de novo.")
            flash("Você já respondeu esta prova.", "warning")
            return redirect(url_for('student_dashboard'))  # ✅ redireciona mesmo sem reenvio
        else:
            try:
                respostas = {
                    'q1': request.form.get('q1'),
                    'q2': request.form.get('q2'),
                    'q3': request.form.get('q3'),
                    'q4': request.form.get('q4'),
                    'q5': request.form.get('q5'),
                    'q6': request.form.get('q6'),
                    'q7': request.form.get('q7'),
                }

                payload = {
                    'aluno_nome': aluno_nome,
                    'respostas': json.dumps(respostas, ensure_ascii=False),
                    'created_at': datetime.now().isoformat()
                }

                xano_request('POST', 'prova_autoconhecimento', data=payload)
                flash("Prova enviada com sucesso!", "success")
                return redirect(url_for('student_dashboard'))

            except Exception as e:
                print(f"❌ Erro ao enviar prova: {str(e)}")
                flash("Erro ao enviar a prova.", "error")


    return render_template('prova4.html', 
                           aluno_nome=aluno_nome, 
                           disciplina_id=disciplina_id,
                           ja_respondido=ja_respondido)

@app.route('/prova3/<int:disciplina_id>', methods=['GET', 'POST'])
@login_required
def prova3(disciplina_id):
    aluno_nome = current_user.username.strip()

    # ✅ Verificar se o aluno já respondeu usando apenas o aluno_nome
    try:
        resposta_existente = xano_request('GET', 'prova_cultura_organizacional', params={
            'aluno_nome': aluno_nome
        })
        # após o GET
        resposta_existente = xano_request('GET', 'prova_cultura_organizacional', params={
            'aluno_nome': aluno_nome
        })

        # filtra localmente por segurança
        ja_respondido = any(
            r.get('aluno_nome') == aluno_nome for r in resposta_existente
        )

    except Exception as e:
        print(f"❌ ERRO ao verificar resposta: {str(e)}")
        ja_respondido = False

    # Submissão da prova
    if request.method == 'POST':
        print("📥 POST recebido")

        if ja_respondido:
            print("⚠️ Prova já respondida - não enviando de novo.")
            flash("Você já respondeu esta prova.", "warning")
            return redirect(url_for('student_dashboard'))  # ✅ redireciona mesmo sem reenvio
        else:
            try:
                respostas = {
                    'q1': request.form.get('q1'),
                    'q2': request.form.get('q2'),
                    'q3': request.form.get('q3'),
                    'q4': request.form.get('q4'),
                    'q5': request.form.get('q5'),
                    'q6': request.form.get('q6'),
                    'q7': request.form.get('q7'),
                }

                payload = {
                    'aluno_nome': aluno_nome,
                    'respostas': json.dumps(respostas, ensure_ascii=False),
                    'created_at': datetime.now().isoformat()
                }

                xano_request('POST', 'prova_cultura_organizacional', data=payload)
                flash("Prova enviada com sucesso!", "success")
                return redirect(url_for('student_dashboard'))

            except Exception as e:
                print(f"❌ Erro ao enviar prova: {str(e)}")
                flash("Erro ao enviar a prova.", "error")


    return render_template('prova3.html', 
                           aluno_nome=aluno_nome, 
                           disciplina_id=disciplina_id,
                           ja_respondido=ja_respondido)

@app.route('/prova5/<int:disciplina_id>', methods=['GET', 'POST'])
@login_required
def prova5(disciplina_id):
    aluno_nome = current_user.username.strip()

    # ✅ Verificar se o aluno já respondeu usando apenas o aluno_nome
    try:
        resposta_existente = xano_request('GET', 'prova_profissional_futuro', params={
            'aluno_nome': aluno_nome
        })
        # após o GET
        resposta_existente = xano_request('GET', 'prova_profissional_futuro', params={
            'aluno_nome': aluno_nome
        })

        # filtra localmente por segurança
        ja_respondido = any(
            r.get('aluno_nome') == aluno_nome for r in resposta_existente
        )

    except Exception as e:
        print(f"❌ ERRO ao verificar resposta: {str(e)}")
        ja_respondido = False

    # Submissão da prova
    if request.method == 'POST':
        print("📥 POST recebido")

        if ja_respondido:
            print("⚠️ Prova já respondida - não enviando de novo.")
            flash("Você já respondeu esta prova.", "warning")
            return redirect(url_for('student_dashboard'))  # ✅ redireciona mesmo sem reenvio
        else:
            try:
                respostas = {
                    'q1': request.form.get('q1'),
                    'q2': request.form.get('q2'),
                    'q3': request.form.get('q3'),
                    'q4': request.form.get('q4'),
                    'q5': request.form.get('q5'),
                    'q6': request.form.get('q6'),
                    'q7': request.form.get('q7'),
                }

                payload = {
                    'aluno_nome': aluno_nome,
                    'respostas': json.dumps(respostas, ensure_ascii=False),
                    'created_at': datetime.now().isoformat()
                }

                xano_request('POST', 'prova_profissional_futuro', data=payload)
                flash("Prova enviada com sucesso!", "success")
                return redirect(url_for('student_dashboard'))

            except Exception as e:
                print(f"❌ Erro ao enviar prova: {str(e)}")
                flash("Erro ao enviar a prova.", "error")


    return render_template('prova5.html', 
                           aluno_nome=aluno_nome, 
                           disciplina_id=disciplina_id,
                           ja_respondido=ja_respondido)
    
@app.route('/prova2/<int:disciplina_id>', methods=['GET', 'POST'])
@login_required
def prova2(disciplina_id):
    aluno_nome = current_user.username.strip()

    # ✅ Verificar se o aluno já respondeu usando apenas o aluno_nome
    try:
        resposta_existente = xano_request('GET', 'prova_lideranca_situacional', params={
            'aluno_nome': aluno_nome
        })
        # após o GET
        resposta_existente = xano_request('GET', 'prova_lideranca_situacional', params={
            'aluno_nome': aluno_nome
        })

        # filtra localmente por segurança
        ja_respondido = any(
            r.get('aluno_nome') == aluno_nome for r in resposta_existente
        )

    except Exception as e:
        print(f"❌ ERRO ao verificar resposta: {str(e)}")
        ja_respondido = False

    # Submissão da prova
    if request.method == 'POST':
        print("📥 POST recebido")

        if ja_respondido:
            print("⚠️ Prova já respondida - não enviando de novo.")
            flash("Você já respondeu esta prova.", "warning")
            return redirect(url_for('student_dashboard'))  # ✅ redireciona mesmo sem reenvio
        else:
            try:
                respostas = {
                    'q1': request.form.get('q1'),
                    'q2': request.form.get('q2'),
                    'q3': request.form.get('q3'),
                    'q4': request.form.get('q4'),
                    'q5': request.form.get('q5'),
                    'q6': request.form.get('q6'),
                    'q7': request.form.get('q7'),
                }

                payload = {
                    'aluno_nome': aluno_nome,
                    'respostas': json.dumps(respostas, ensure_ascii=False),
                    'created_at': datetime.now().isoformat()
                }

                xano_request('POST', 'prova_lideranca_situacional', data=payload)
                flash("Prova enviada com sucesso!", "success")
                return redirect(url_for('student_dashboard'))

            except Exception as e:
                print(f"❌ Erro ao enviar prova: {str(e)}")
                flash("Erro ao enviar a prova.", "error")


    return render_template('prova2.html', 
                           aluno_nome=aluno_nome, 
                           disciplina_id=disciplina_id,
                           ja_respondido=ja_respondido)
    
@app.route('/prova6/<int:disciplina_id>', methods=['GET', 'POST'])
@login_required
def prova6(disciplina_id):
    aluno_nome = current_user.username.strip()

    # ✅ Verificar se o aluno já respondeu usando apenas o aluno_nome
    try:
        resposta_existente = xano_request('GET', 'prova_metorneilider', params={
            'aluno_nome': aluno_nome
        })
        # após o GET
        resposta_existente = xano_request('GET', 'prova_metorneilider', params={
            'aluno_nome': aluno_nome
        })

        # filtra localmente por segurança
        ja_respondido = any(
            r.get('aluno_nome') == aluno_nome for r in resposta_existente
        )

    except Exception as e:
        print(f"❌ ERRO ao verificar resposta: {str(e)}")
        ja_respondido = False

    # Submissão da prova
    if request.method == 'POST':
        print("📥 POST recebido")

        if ja_respondido:
            print("⚠️ Prova já respondida - não enviando de novo.")
            flash("Você já respondeu esta prova.", "warning")
            return redirect(url_for('student_dashboard'))  # ✅ redireciona mesmo sem reenvio
        else:
            try:
                respostas = {
                    'q1': request.form.get('q1'),
                    'q2': request.form.get('q2'),
                    'q3': request.form.get('q3'),
                    'q4': request.form.get('q4'),
                    'q5': request.form.get('q5'),
                    'q6': request.form.get('q6'),
                    'q7': request.form.get('q7'),
                }

                payload = {
                    'aluno_nome': aluno_nome,
                    'respostas': json.dumps(respostas, ensure_ascii=False),
                    'created_at': datetime.now().isoformat()
                }

                xano_request('POST', 'prova_metorneilider', data=payload)
                flash("Prova enviada com sucesso!", "success")
                return redirect(url_for('student_dashboard'))

            except Exception as e:
                print(f"❌ Erro ao enviar prova: {str(e)}")
                flash("Erro ao enviar a prova.", "error")


    return render_template('prova6.html', 
                           aluno_nome=aluno_nome, 
                           disciplina_id=disciplina_id,
                           ja_respondido=ja_respondido)

@app.route('/prova7/<int:disciplina_id>', methods=['GET', 'POST'])
@login_required
def prova7(disciplina_id):
    aluno_nome = current_user.username.strip()

    # ✅ Verificar se o aluno já respondeu usando apenas o aluno_nome
    try:
        resposta_existente = xano_request('GET', 'prova_inteligencia_emocional', params={
            'aluno_nome': aluno_nome
        })
        # após o GET
        resposta_existente = xano_request('GET', 'prova_inteligencia_emocional', params={
            'aluno_nome': aluno_nome
        })

        # filtra localmente por segurança
        ja_respondido = any(
            r.get('aluno_nome') == aluno_nome for r in resposta_existente
        )

    except Exception as e:
        print(f"❌ ERRO ao verificar resposta: {str(e)}")
        ja_respondido = False

    # Submissão da prova
    if request.method == 'POST':
        print("📥 POST recebido")

        if ja_respondido:
            print("⚠️ Prova já respondida - não enviando de novo.")
            flash("Você já respondeu esta prova.", "warning")
            return redirect(url_for('student_dashboard'))  # ✅ redireciona mesmo sem reenvio
        else:
            try:
                respostas = {
                    'q1': request.form.get('q1'),
                    'q2': request.form.get('q2'),
                    'q3': request.form.get('q3'),
                    'q4': request.form.get('q4'),
                    'q5': request.form.get('q5'),
                    'q6': request.form.get('q6'),
                    'q7': request.form.get('q7'),
                }

                payload = {
                    'aluno_nome': aluno_nome,
                    'respostas': json.dumps(respostas, ensure_ascii=False),
                    'created_at': datetime.now().isoformat()
                }

                xano_request('POST', 'prova_inteligencia_emocional', data=payload)
                flash("Prova enviada com sucesso!", "success")
                return redirect(url_for('student_dashboard'))

            except Exception as e:
                print(f"❌ Erro ao enviar prova: {str(e)}")
                flash("Erro ao enviar a prova.", "error")


    return render_template('prova7.html', 
                           aluno_nome=aluno_nome, 
                           disciplina_id=disciplina_id,
                           ja_respondido=ja_respondido)
    
@app.route('/prova8/<int:disciplina_id>', methods=['GET', 'POST'])
@login_required
def prova8(disciplina_id):
    aluno_nome = current_user.username.strip()

    # ✅ Verificar se o aluno já respondeu usando apenas o aluno_nome
    try:
        resposta_existente = xano_request('GET', 'prova_comunicacao_assertiva', params={
            'aluno_nome': aluno_nome
        })
        # após o GET
        resposta_existente = xano_request('GET', 'prova_comunicacao_assertiva', params={
            'aluno_nome': aluno_nome
        })

        # filtra localmente por segurança
        ja_respondido = any(
            r.get('aluno_nome') == aluno_nome for r in resposta_existente
        )

    except Exception as e:
        print(f"❌ ERRO ao verificar resposta: {str(e)}")
        ja_respondido = False

    # Submissão da prova
    if request.method == 'POST':
        print("📥 POST recebido")

        if ja_respondido:
            print("⚠️ Prova já respondida - não enviando de novo.")
            flash("Você já respondeu esta prova.", "warning")
            return redirect(url_for('student_dashboard'))  # ✅ redireciona mesmo sem reenvio
        else:
            try:
                respostas = {
                    'q1': request.form.get('q1'),
                    'q2': request.form.get('q2'),
                    'q3': request.form.get('q3'),
                    'q4': request.form.get('q4'),
                    'q5': request.form.get('q5'),
                    'q6': request.form.get('q6'),
                    'q7': request.form.get('q7'),
                }

                payload = {
                    'aluno_nome': aluno_nome,
                    'respostas': json.dumps(respostas, ensure_ascii=False),
                    'created_at': datetime.now().isoformat()
                }

                xano_request('POST', 'prova_comunicacao_assertiva', data=payload)
                flash("Prova enviada com sucesso!", "success")
                return redirect(url_for('student_dashboard'))

            except Exception as e:
                print(f"❌ Erro ao enviar prova: {str(e)}")
                flash("Erro ao enviar a prova.", "error")


    return render_template('prova8.html', 
                           aluno_nome=aluno_nome, 
                           disciplina_id=disciplina_id,
                           ja_respondido=ja_respondido)
    
@app.route('/prova9/<int:disciplina_id>', methods=['GET', 'POST'])
@login_required
def prova9(disciplina_id):
    aluno_nome = current_user.username.strip()

    # ✅ Verificar se o aluno já respondeu usando apenas o aluno_nome
    try:
        resposta_existente = xano_request('GET', 'prova_gestao_conflitos', params={
            'aluno_nome': aluno_nome
        })
        # após o GET
        resposta_existente = xano_request('GET', 'prova_gestao_conflitos', params={
            'aluno_nome': aluno_nome
        })

        # filtra localmente por segurança
        ja_respondido = any(
            r.get('aluno_nome') == aluno_nome for r in resposta_existente
        )

    except Exception as e:
        print(f"❌ ERRO ao verificar resposta: {str(e)}")
        ja_respondido = False

    # Submissão da prova
    if request.method == 'POST':
        print("📥 POST recebido")

        if ja_respondido:
            print("⚠️ Prova já respondida - não enviando de novo.")
            flash("Você já respondeu esta prova.", "warning")
            return redirect(url_for('student_dashboard'))  # ✅ redireciona mesmo sem reenvio
        else:
            try:
                respostas = {
                    'q1': request.form.get('q1'),
                    'q2': request.form.get('q2'),
                    'q3': request.form.get('q3'),
                    'q4': request.form.get('q4'),
                    'q5': request.form.get('q5'),
                    'q6': request.form.get('q6'),
                    'q7': request.form.get('q7'),
                }

                payload = {
                    'aluno_nome': aluno_nome,
                    'respostas': json.dumps(respostas, ensure_ascii=False),
                    'created_at': datetime.now().isoformat()
                }

                xano_request('POST', 'prova_gestao_conflitos', data=payload)
                flash("Prova enviada com sucesso!", "success")
                return redirect(url_for('student_dashboard'))

            except Exception as e:
                print(f"❌ Erro ao enviar prova: {str(e)}")
                flash("Erro ao enviar a prova.", "error")


    return render_template('prova9.html', 
                           aluno_nome=aluno_nome, 
                           disciplina_id=disciplina_id,
                           ja_respondido=ja_respondido)
    
@app.route('/prova10/<int:disciplina_id>', methods=['GET', 'POST'])
@login_required
def prova10(disciplina_id):
    aluno_nome = current_user.username.strip()

    # ✅ Verificar se o aluno já respondeu usando apenas o aluno_nome
    try:
        resposta_existente = xano_request('GET', 'prova_gestao_estrategica', params={
            'aluno_nome': aluno_nome
        })
        # após o GET
        resposta_existente = xano_request('GET', 'prova_gestao_estrategica', params={
            'aluno_nome': aluno_nome
        })

        # filtra localmente por segurança
        ja_respondido = any(
            r.get('aluno_nome') == aluno_nome for r in resposta_existente
        )

    except Exception as e:
        print(f"❌ ERRO ao verificar resposta: {str(e)}")
        ja_respondido = False

    # Submissão da prova
    if request.method == 'POST':
        print("📥 POST recebido")

        if ja_respondido:
            print("⚠️ Prova já respondida - não enviando de novo.")
            flash("Você já respondeu esta prova.", "warning")
            return redirect(url_for('student_dashboard'))  # ✅ redireciona mesmo sem reenvio
        else:
            try:
                respostas = {
                    'q1': request.form.get('q1'),
                    'q2': request.form.get('q2'),
                    'q3': request.form.get('q3'),
                    'q4': request.form.get('q4'),
                    'q5': request.form.get('q5'),
                    'q6': request.form.get('q6'),
                    'q7': request.form.get('q7'),
                }

                payload = {
                    'aluno_nome': aluno_nome,
                    'respostas': json.dumps(respostas, ensure_ascii=False),
                    'created_at': datetime.now().isoformat()
                }

                xano_request('POST', 'prova_gestao_estrategica', data=payload)
                flash("Prova enviada com sucesso!", "success")
                return redirect(url_for('student_dashboard'))

            except Exception as e:
                print(f"❌ Erro ao enviar prova: {str(e)}")
                flash("Erro ao enviar a prova.", "error")


    return render_template('prova10.html', 
                           aluno_nome=aluno_nome, 
                           disciplina_id=disciplina_id,
                           ja_respondido=ja_respondido)

@app.route('/prova11/<int:disciplina_id>', methods=['GET', 'POST'])
@login_required
def prova11(disciplina_id):
    aluno_nome = current_user.username.strip()

    # ✅ Verificar se o aluno já respondeu usando apenas o aluno_nome
    try:
        resposta_existente = xano_request('GET', 'prova_cultura_feedback', params={
            'aluno_nome': aluno_nome
        })
        # após o GET
        resposta_existente = xano_request('GET', 'prova_cultura_feedback', params={
            'aluno_nome': aluno_nome
        })

        # filtra localmente por segurança
        ja_respondido = any(
            r.get('aluno_nome') == aluno_nome for r in resposta_existente
        )

    except Exception as e:
        print(f"❌ ERRO ao verificar resposta: {str(e)}")
        ja_respondido = False

    # Submissão da prova
    if request.method == 'POST':
        print("📥 POST recebido")

        if ja_respondido:
            print("⚠️ Prova já respondida - não enviando de novo.")
            flash("Você já respondeu esta prova.", "warning")
            return redirect(url_for('student_dashboard'))  # ✅ redireciona mesmo sem reenvio
        else:
            try:
                respostas = {
                    'q1': request.form.get('q1'),
                    'q2': request.form.get('q2'),
                    'q3': request.form.get('q3'),
                    'q4': request.form.get('q4'),
                    'q5': request.form.get('q5'),
                    'q6': request.form.get('q6'),
                    'q7': request.form.get('q7'),
                }

                payload = {
                    'aluno_nome': aluno_nome,
                    'respostas': json.dumps(respostas, ensure_ascii=False),
                    'created_at': datetime.now().isoformat()
                }

                xano_request('POST', 'prova_cultura_feedback', data=payload)
                flash("Prova enviada com sucesso!", "success")
                return redirect(url_for('student_dashboard'))

            except Exception as e:
                print(f"❌ Erro ao enviar prova: {str(e)}")
                flash("Erro ao enviar a prova.", "error")


    return render_template('prova11.html', 
                           aluno_nome=aluno_nome, 
                           disciplina_id=disciplina_id,
                           ja_respondido=ja_respondido)
    
@app.route('/prova12/<int:disciplina_id>', methods=['GET', 'POST'])
@login_required
def prova12(disciplina_id):
    aluno_nome = current_user.username.strip()

    # ✅ Verificar se o aluno já respondeu usando apenas o aluno_nome
    try:
        resposta_existente = xano_request('GET', 'prova_gestao_equipe', params={
            'aluno_nome': aluno_nome
        })
        # após o GET
        resposta_existente = xano_request('GET', 'prova_gestao_equipe', params={
            'aluno_nome': aluno_nome
        })

        # filtra localmente por segurança
        ja_respondido = any(
            r.get('aluno_nome') == aluno_nome for r in resposta_existente
        )

    except Exception as e:
        print(f"❌ ERRO ao verificar resposta: {str(e)}")
        ja_respondido = False

    # Submissão da prova
    if request.method == 'POST':
        print("📥 POST recebido")

        if ja_respondido:
            print("⚠️ Prova já respondida - não enviando de novo.")
            flash("Você já respondeu esta prova.", "warning")
            return redirect(url_for('student_dashboard'))  # ✅ redireciona mesmo sem reenvio
        else:
            try:
                respostas = {
                    'q1': request.form.get('q1'),
                    'q2': request.form.get('q2'),
                    'q3': request.form.get('q3'),
                    'q4': request.form.get('q4'),
                    'q5': request.form.get('q5'),
                    'q6': request.form.get('q6'),
                    'q7': request.form.get('q7'),
                }

                payload = {
                    'aluno_nome': aluno_nome,
                    'respostas': json.dumps(respostas, ensure_ascii=False),
                    'created_at': datetime.now().isoformat()
                }

                xano_request('POST', 'prova_gestao_equipe', data=payload)
                flash("Prova enviada com sucesso!", "success")
                return redirect(url_for('student_dashboard'))

            except Exception as e:
                print(f"❌ Erro ao enviar prova: {str(e)}")
                flash("Erro ao enviar a prova.", "error")


    return render_template('prova12.html', 
                           aluno_nome=aluno_nome, 
                           disciplina_id=disciplina_id,
                           ja_respondido=ja_respondido)
    
# @app.route('/prova2/<int:disciplina_id>', methods=['GET', 'POST'])
# @login_required
# def prova2(disciplina_id):
#     print("⚡ Método recebido:", request.method)
#     aluno_nome = current_user.username

#     # 🚀 Submissão da prova
#     if request.method == 'POST':
#         respostas = {
#             'q1': request.form.get('q1'),
#             'q2': request.form.get('q2'),
#             'q3': request.form.get('q3'),
#             'q4': request.form.get('q4'),
#             'q5': request.form.get('q5'),
#             'q6': request.form.get('q6'),
#             'q7': request.form.get('q7'),
#         }

#         # Serializa para texto JSON
#         respostas_json_str = json.dumps(respostas, ensure_ascii=False)

#         payload = {
#             'aluno_nome': aluno_nome,
#             'disciplina_id': disciplina_id,
#             'respostas': respostas_json_str,  # ✅ como string para campo do tipo text
#             'created_at': datetime.now().isoformat()
#         }

#         print("📤 Enviando payload:", payload)

#         try:
#             xano_request('POST', 'respostas_prova_2', data=payload)
#             flash('Prova enviada com sucesso!', 'success')
#             return redirect(url_for('student_dashboard'))
#         except Exception as e:
#             print(f"Erro ao enviar prova: {str(e)}")
#             flash('Erro ao enviar prova', 'error')

#     return render_template('prova2.html', disciplina_id=disciplina_id, aluno_nome=aluno_nome)

def salvar_respostas(aluno_nome, respostas_dict):
    url = f"{XANO_BASE_URL}/respostas_provas_3"
    headers = {
        "Content-Type": "application/json"
    }

    payload = {
        "aluno_nome": aluno_nome,
        "respostas": respostas_dict
    }

    response = requests.post(url, headers=headers, json=payload)

    if response.status_code != 200:
        print("Erro ao salvar resposta:", response.text)


def verificar_resposta(aluno_nome, prova_nome):
    url = f"{XANO_BASE_URL}/respostas_provas"
    params = {
        "aluno_nome": aluno_nome,
        "prova_nome": prova_nome
    }
    headers = {
        "Content-Type": "application/json"
    }

    response = requests.get(url, params=params, headers=headers)

    if response.status_code == 200:
        data = response.json()
        return len(data) > 0  # se retornou alguma resposta, já respondeu
    else:
        print("Erro ao verificar resposta:", response.text)
        return False

    
@app.route('/update_grade', methods=['POST'])
@login_required
@admin_required
def update_grade():
    try:
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'message': 'Dados inválidos'}), 400

        print(f"Dados recebidos: {data}")

        # Validação dos campos
        try:
            aluno_id = int(data.get('aluno_id'))
            disciplina_id = int(data.get('disciplina_id'))
            nota = float(data.get('nota')) if data.get('nota') not in [None, ''] else None
            frequencia = int(data.get('frequencia')) if data.get('frequencia') not in [None, ''] else None
        except (ValueError, TypeError) as e:
            return jsonify({'success': False, 'message': 'Dados inválidos: ' + str(e)}), 400

        # Verificar se a nota já existe
        existing_grades = xano_request('GET', 'grades', params={
            'student_id': aluno_id,
            'discipline_id': disciplina_id
        })

        if existing_grades and isinstance(existing_grades, list) and len(existing_grades) > 0:
            # Atualizar nota existente
            grade_id = existing_grades[0]['id']
            update_data = {
                'grade': nota if nota is not None else existing_grades[0].get('grade'),
                'frequency': frequencia if frequencia is not None else existing_grades[0].get('frequency')
            }
            
            print(f"Tentando atualizar nota ID {grade_id} com dados: {update_data}")
            result = xano_request('PATCH', 'grades', data=update_data, id=grade_id)
            action = 'atualizada'
        else:
            # Criar nova nota
            if nota is None or frequencia is None:
                return jsonify({'success': False, 'message': 'Nota e frequência são obrigatórias para novo registro'}), 400
                
            new_data = {
                'student_id': aluno_id,
                'discipline_id': disciplina_id,
                'grade': nota,
                'frequency': frequencia,
                'created_at': datetime.now().isoformat()
            }
            
            print(f"Tentando criar nova nota com dados: {new_data}")
            result = xano_request('POST', 'grades', data=new_data)
            action = 'criada'

        if result:
            return jsonify({
                'success': True,
                'message': f'Nota {action} com sucesso!',
                'data': result
            })
        
        return jsonify({'success': False, 'message': 'Erro ao processar nota'}), 500

    except Exception as e:
        print(f"Erro completo: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'Erro no servidor: {str(e)}'
        }), 500

@app.route('/edit_user/<int:user_id>', methods=['GET', 'POST'])
@login_required
def edit_user(user_id):
    if current_user.role != 'admin':
        return redirect(url_for('home'))

    try:
        if request.method == 'GET':
            user = xano_request('GET', 'users', id=user_id)
            if user:
                return render_template('edit_user.html', user=user)
            flash('Usuário não encontrado.', 'error')
            return redirect(url_for('admin_dashboard'))

        if request.method == 'POST':
            username = request.form['username']
            password = request.form['password']
            role = request.form['role']
            
            # Novos campos
            email = request.form.get('email', '')
            cargo = request.form.get('cargo', '')
            area = request.form.get('area', '')
            gestor = request.form.get('gestor', '')
            telefone = request.form.get('telefone', '')

            update_data = {
                'username': username,
                'role': role,
                'email': email,
                'cargo_atual': cargo,
                'area': area,
                'gestor_imediato': gestor,
                'telefone': telefone
            }
            
            if password:
                update_data['password'] = password  
            
            xano_request('PATCH', 'users', update_data, id=user_id)
            flash('Usuário atualizado com sucesso!', 'success')
            return redirect(url_for('admin_dashboard'))

    except Exception as e:
        print(f"ERRO ao editar usuário: {str(e)}")
        flash('Erro ao editar usuário', 'error')
    
    return redirect(url_for('admin_dashboard'))

@app.route('/edit_discipline/<int:discipline_id>', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_discipline(discipline_id):
    discipline = xano_request('GET', 'disciplines', id=discipline_id)
    if not discipline:
        flash('Disciplina não encontrada', 'error')
        return redirect(url_for('admin_dashboard'))

    teachers = [u for u in xano_request('GET', 'users') or [] if u.get('role') == 'teacher']
    
    if request.method == 'POST':
        try:
            # Atualiza os dados básicos da disciplina
            updated_data = {
                'name': request.form['disciplina'].strip(),
                'updated_at': datetime.now().isoformat()
            }
            
            # Verifica se foi selecionado um novo professor
            new_professor_id = request.form.get('professor')
            if new_professor_id:
                updated_data['professor_id'] = int(new_professor_id)
                
                # Atualiza a tabela de relacionamento
                relations = xano_request('GET', 'professor_disciplines', 
                                      params={'discipline_id': discipline_id}) or []
                
                if relations:
                    # Atualiza relação existente
                    xano_request('PATCH', 'professor_disciplines', 
                              {'professor_id': new_professor_id}, 
                              id=relations[0]['id'])
                else:
                    # Cria nova relação
                    xano_request('POST', 'professor_disciplines', {
                        'professor_id': new_professor_id,
                        'discipline_id': discipline_id,
                        'created_at': datetime.now().isoformat()
                    })
            
            xano_request('PATCH', 'disciplines', updated_data, id=discipline_id)
            flash('Disciplina atualizada com sucesso!', 'success')
            return redirect(url_for('admin_dashboard'))
            
        except Exception as e:
            print(f"Erro ao atualizar disciplina: {str(e)}")
            flash('Erro ao atualizar disciplina', 'error')
    
    return render_template('edit_discipline.html', 
                         discipline=discipline, 
                         teachers=teachers,
                         current_professor_id=discipline.get('professor_id'))

@app.route('/edit_content/<int:content_id>', methods=['GET', 'POST'])
@login_required
def edit_content_route(content_id):
    if request.method == 'GET':
        # Buscar o conteúdo existente
        content = xano_request('GET', 'contents', id=content_id)
        if not content or content.get('professor_id') != current_user.id:
            flash('Conteúdo não encontrado ou não pertence a você', 'error')
            return redirect(url_for('professor_dashboard'))
        
        # Buscar disciplina associada
        discipline = xano_request('GET', 'disciplines', id=content.get('discipline_id'))
        
        return render_template('edit_content.html', 
                            content=content,
                            discipline=discipline)
    
    if request.method == 'POST':
        # Processar edição
        new_content = request.form.get('content')
        response = xano_request('PATCH', 'contents', 
                              {'content': new_content}, 
                              id=content_id)
        
        if response:
            flash('Conteúdo atualizado com sucesso!', 'success')
        else:
            flash('Erro ao atualizar conteúdo', 'error')
        
        return redirect(url_for('professor_dashboard'))
    


@app.route('/delete_content/<int:content_id>', methods=['POST'])
@login_required
def delete_content_route(content_id):
    # Verificar se o conteúdo pertence ao professor
    content = xano_request('GET', 'contents', id=content_id)
    
    if content and content.get('professor_id') == current_user.id:
        response = xano_request('DELETE', 'contents', id=content_id)
        if response:
            flash('Conteúdo removido com sucesso!', 'success')
        else:
            flash('Erro ao remover conteúdo', 'error')
    else:
        flash('Conteúdo não encontrado ou não pertence a você', 'error')
    
    return redirect(url_for('professor_dashboard'))




@app.route('/delete_user/<int:user_id>', methods=['POST'])
@login_required
def delete_user(user_id):
    if current_user.role != 'admin':
        return redirect(url_for('home'))

    try:
        xano_request('DELETE', 'users', id=user_id)
        flash('Usuário excluído com sucesso!', 'success')
    except Exception as e:
        print(f"ERRO ao excluir usuário: {str(e)}")
        flash('Erro ao excluir usuário', 'error')
    
    return redirect(url_for('admin_dashboard'))

@app.route('/remove_professor/<int:discipline_id>', methods=['POST'])
@login_required
@admin_required
def remove_professor(discipline_id):
    try:
        # Remove o professor da disciplina
        xano_request('PATCH', 'disciplines', {'professor_id': None}, id=discipline_id)
        
        # Remove também da tabela de relacionamento professor_disciplines
        professor_disciplines = xano_request('GET', 'professor_disciplines', 
                                           params={'discipline_id': discipline_id})
        
        if professor_disciplines and isinstance(professor_disciplines, list):
            for relation in professor_disciplines:
                xano_request('DELETE', 'professor_disciplines', id=relation['id'])
        
        flash('Professor removido da disciplina com sucesso!', 'success')
    except Exception as e:
        print(f"ERRO ao remover professor: {str(e)}")
        flash('Erro ao remover professor da disciplina', 'error')
    
    return redirect(url_for('admin_dashboard'))

@app.route('/delete_discipline/<int:discipline_id>', methods=['POST'])
@login_required
def delete_discipline(discipline_id):
    if current_user.role != 'admin':
        return redirect(url_for('home'))

    try:
        xano_request('DELETE', 'disciplines', id=discipline_id)
        flash('Disciplina excluída com sucesso!', 'success')
    except Exception as e:
        print(f"ERRO ao excluir disciplina: {str(e)}")
        flash('Erro ao excluir disciplina', 'error')
    
    return redirect(url_for('admin_dashboard'))

@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_server_error(e):
    return render_template('500.html'), 500

if __name__ == '__main__':
    app.run(debug=True)