from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, session
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
import os
import requests
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
import json


app = Flask(__name__)
app.secret_key = os.getenv('FLASK_SECRET_KEY', 'sua_chave_secreta_aqui')

# Configurações do Xano
XANO_BASE_URL = os.getenv('XANO_BASE_URL', "https://xidg-u2cu-sa8e.n7c.xano.io/api:loOqZbWF")
XANO_API_KEY = os.getenv('XANO_API_KEY', "eyJhbGciOiJBMjU2S1ciLCJlbmMiOiJBMjU2Q0JDLUhTNTEyIiwiemlwIjoiREVGIn0._No4U4JFrLixFsdBbseZqmNw7lF71W9s7HreN8mAJzMxqfFkCKcKiRFglWWqqhFDbCq-0H2x--Ngq1CERO_1-fcX8pHDa-Fr.xnQTJvtUEQ1kTql8BTouvQ.p_N3CAuueIcvLuoEsFgLM4CyezTn8ahPGZu1-vJCwLqY1lBy-rthXYcG8347gaX8678PNI1POKNwmM6RK5YQ2QQ1jqL7AMwOJoD403e7eSpbk815QtAtAXTLavmJ5gdIB78aIn3Ft-wPjFJfBeJyfQ.kM1lAOe0P3KnkgWBJdvtk0N3rFxI5HPH6eay55cwNmA")
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
    'respostas_prova_2':'respostas_prova_2',
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

        # Criar lista de disciplinas com nome (evita duplicados)
        discipline_ids = set()
        disciplines = []
        for d in raw_disciplines:
            discipline_id = int(d['discipline_id'])
            if discipline_id not in discipline_ids:
                disciplines.append({
                    'id': discipline_id,
                    'name': discipline_map.get(discipline_id, 'Desconhecida')
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

                content["discipline_name"] = discipline_map.get(discipline_id, "Desconhecida")
                contents.append(content)
                conteudos_ids_adicionados.add(content["id"])

        return render_template('student_dashboard.html',
                               disciplines=disciplines,
                               grades=processed_grades,
                               messages=messages,
                               contents=contents)

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
    print("⚡ Método recebido:", request.method)
    aluno_nome = current_user.username

    # 🚀 Submissão da prova
    if request.method == 'POST':
        respostas = {
            'q1': request.form.get('q1'),
            'q2': request.form.get('q2'),
            'q3': request.form.get('q3'),
            'q4': request.form.get('q4'),
            'q5': request.form.get('q5'),
            'q6': request.form.get('q6'),
            'q7': request.form.get('q7'),
        }

        # Serializa para texto JSON
        respostas_json_str = json.dumps(respostas, ensure_ascii=False)

        payload = {
            'aluno_nome': aluno_nome,
            'disciplina_id': disciplina_id,
            'respostas': respostas_json_str,  # ✅ como string para campo do tipo text
            'created_at': datetime.now().isoformat()
        }

        print("📤 Enviando payload:", payload)

        try:
            xano_request('POST', 'respostas_prova_1', data=payload)
            flash('Prova enviada com sucesso!', 'success')
            return redirect(url_for('student_dashboard'))
        except Exception as e:
            print(f"Erro ao enviar prova: {str(e)}")
            flash('Erro ao enviar prova', 'error')

    return render_template('prova.html', disciplina_id=disciplina_id, aluno_nome=aluno_nome)

@app.route('/prova3/<int:disciplina_id>', methods=['GET', 'POST'])
@login_required
def prova3(disciplina_id):
    print("⚡ Método recebido:", request.method)
    aluno_nome = current_user.username

    # 🚀 Submissão da prova
    if request.method == 'POST':
        respostas = {
            'q1': request.form.get('q1'),
            'q2': request.form.get('q2'),
            'q3': request.form.get('q3'),
            'q4': request.form.get('q4'),
            'q5': request.form.get('q5'),
            'q6': request.form.get('q6'),
            'q7': request.form.get('q7'),
        }

        # Serializa para texto JSON
        respostas_json_str = json.dumps(respostas, ensure_ascii=False)

        payload = {
            'aluno_nome': aluno_nome,
            'disciplina_id': disciplina_id,
            'respostas': respostas_json_str,  # ✅ como string para campo do tipo text
            'created_at': datetime.now().isoformat()
        }

        print("📤 Enviando payload:", payload)

        try:
            xano_request('POST', 'respostas_prova', data=payload)
            flash('Prova enviada com sucesso!', 'success')
            return redirect(url_for('student_dashboard'))
        except Exception as e:
            print(f"Erro ao enviar prova: {str(e)}")
            flash('Erro ao enviar prova', 'error')

    return render_template('prova3.html', disciplina_id=disciplina_id, aluno_nome=aluno_nome)

@app.route('/prova2/<int:disciplina_id>', methods=['GET', 'POST'])
@login_required
def prova2(disciplina_id):
    print("⚡ Método recebido:", request.method)
    aluno_nome = current_user.username

    # 🚀 Submissão da prova
    if request.method == 'POST':
        respostas = {
            'q1': request.form.get('q1'),
            'q2': request.form.get('q2'),
            'q3': request.form.get('q3'),
            'q4': request.form.get('q4'),
            'q5': request.form.get('q5'),
            'q6': request.form.get('q6'),
            'q7': request.form.get('q7'),
        }

        # Serializa para texto JSON
        respostas_json_str = json.dumps(respostas, ensure_ascii=False)

        payload = {
            'aluno_nome': aluno_nome,
            'disciplina_id': disciplina_id,
            'respostas': respostas_json_str,  # ✅ como string para campo do tipo text
            'created_at': datetime.now().isoformat()
        }

        print("📤 Enviando payload:", payload)

        try:
            xano_request('POST', 'respostas_prova_2', data=payload)
            flash('Prova enviada com sucesso!', 'success')
            return redirect(url_for('student_dashboard'))
        except Exception as e:
            print(f"Erro ao enviar prova: {str(e)}")
            flash('Erro ao enviar prova', 'error')

    return render_template('prova2.html', disciplina_id=disciplina_id, aluno_nome=aluno_nome)



    
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