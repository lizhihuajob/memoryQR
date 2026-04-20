from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify, send_from_directory
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
import sqlite3
import os
import uuid
import qrcode
from qrcode.image.pil import PilImage
from PIL import Image, ImageDraw
import segno
import cv2
import numpy as np
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'memory_qr_secret_key_2024'

# 配置
UPLOAD_FOLDER = 'uploads'
QR_FOLDER = 'uploads/qrcodes'
MEMORY_FOLDER = 'uploads/memories'
ALLOWED_IMAGE_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'bmp'}
ALLOWED_VIDEO_EXTENSIONS = {'mp4', 'webm', 'ogg'}
ALLOWED_EXTENSIONS = ALLOWED_IMAGE_EXTENSIONS.union(ALLOWED_VIDEO_EXTENSIONS)

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024  # 50MB

# 确保目录存在
for folder in [UPLOAD_FOLDER, QR_FOLDER, MEMORY_FOLDER]:
    if not os.path.exists(folder):
        os.makedirs(folder)

def get_db_connection():
    conn = sqlite3.connect('memory_qr.db')
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # 用户表
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # 记忆表
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS memories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            memory_id TEXT UNIQUE NOT NULL,
            user_id INTEGER NOT NULL,
            title TEXT NOT NULL,
            content TEXT,
            media_path TEXT,
            media_type TEXT,
            qr_path TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')
    
    conn.commit()
    conn.close()

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def get_file_type(filename):
    ext = filename.rsplit('.', 1)[1].lower()
    if ext in ALLOWED_IMAGE_EXTENSIONS:
        return 'image'
    elif ext in ALLOWED_VIDEO_EXTENSIONS:
        return 'video'
    return None

def generate_memory_id():
    return str(uuid.uuid4())[:8].upper()

def login_required(f):
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('请先登录以访问此页面', 'warning')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    decorated_function.__name__ = f.__name__
    return decorated_function

def generate_qr_code(memory_id, options=None):
    if options is None:
        options = {}
    
    # 默认配置
    fg_color = options.get('fg_color', '#000000')
    bg_color = options.get('bg_color', '#FFFFFF')
    logo_path = options.get('logo_path')
    background_img_path = options.get('background_img_path')
    error_correction = options.get('error_correction', 'H')
    
    # 使用 segno 生成二维码
    qr = segno.make(memory_id, error=error_correction)
    
    # 创建基本二维码图像
    temp_qr_path = os.path.join(QR_FOLDER, f'temp_{uuid.uuid4().hex}.png')
    qr.save(temp_qr_path, scale=10, border=4, dark=fg_color, light=bg_color)
    
    # 打开生成的二维码
    qr_img = Image.open(temp_qr_path).convert('RGBA')
    qr_width, qr_height = qr_img.size
    
    # 处理背景图
    if background_img_path and os.path.exists(background_img_path):
        try:
            bg_img = Image.open(background_img_path).convert('RGBA')
            # 调整背景图大小以适应二维码
            bg_img = bg_img.resize((qr_width, qr_height), Image.Resampling.LANCZOS)
            
            # 创建一个半透明的遮罩让二维码更清晰
            overlay = Image.new('RGBA', (qr_width, qr_height), (255, 255, 255, 180))
            bg_img = Image.alpha_composite(bg_img, overlay)
            
            # 将二维码放在背景图上
            qr_img = Image.alpha_composite(bg_img, qr_img)
        except Exception as e:
            print(f"背景图处理错误: {e}")
    
    # 处理 Logo 嵌入
    if logo_path and os.path.exists(logo_path):
        try:
            logo = Image.open(logo_path).convert('RGBA')
            # 计算 Logo 大小（二维码的 20%）
            logo_size = int(qr_width * 0.2)
            logo = logo.resize((logo_size, logo_size), Image.Resampling.LANCZOS)
            
            # 计算位置（中心）
            logo_x = (qr_width - logo_size) // 2
            logo_y = (qr_height - logo_size) // 2
            
            # 创建白色背景圆
            draw = ImageDraw.Draw(qr_img)
            circle_radius = int(logo_size * 0.6)
            circle_x = logo_x + logo_size // 2
            circle_y = logo_y + logo_size // 2
            draw.ellipse(
                [circle_x - circle_radius, circle_y - circle_radius,
                 circle_x + circle_radius, circle_y + circle_radius],
                fill=bg_color if bg_color != '#FFFFFF' else 'white'
            )
            
            # 粘贴 Logo
            qr_img.paste(logo, (logo_x, logo_y), logo)
        except Exception as e:
            print(f"Logo 处理错误: {e}")
    
    # 保存最终二维码
    qr_filename = f'qr_{uuid.uuid4().hex}.png'
    qr_path = os.path.join(QR_FOLDER, qr_filename)
    
    # 转换为 RGB 保存为 PNG
    if qr_img.mode == 'RGBA':
        qr_img = qr_img.convert('RGB')
    qr_img.save(qr_path, 'PNG')
    
    # 删除临时文件
    if os.path.exists(temp_qr_path):
        os.remove(temp_qr_path)
    
    return qr_filename

def decode_qr_code(image_path):
    # 使用 OpenCV 解码二维码
    img = cv2.imread(image_path)
    if img is None:
        return None
    
    # 创建 QRCodeDetector
    qr_detector = cv2.QRCodeDetector()
    
    # 尝试解码
    try:
        data, bbox, straight_qrcode = qr_detector.detectAndDecode(img)
        if data:
            return data.strip()
    except Exception as e:
        print(f"OpenCV 解码失败: {e}")
    
    # 备用方法：使用 PIL 转换后再试
    try:
        pil_img = Image.open(image_path).convert('L')
        img_array = np.array(pil_img)
        data, bbox, _ = qr_detector.detectAndDecode(img_array)
        if data:
            return data.strip()
    except Exception as e:
        print(f"备用解码失败: {e}")
    
    return None

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        confirm_password = request.form.get('confirm_password', '')
        
        if not username or not password:
            flash('用户名和密码不能为空', 'danger')
            return redirect(url_for('register'))
        
        if password != confirm_password:
            flash('两次输入的密码不一致', 'danger')
            return redirect(url_for('register'))
        
        if len(password) < 6:
            flash('密码长度至少6位', 'danger')
            return redirect(url_for('register'))
        
        conn = get_db_connection()
        
        # 检查用户名是否已存在
        existing_user = conn.execute(
            'SELECT id FROM users WHERE username = ?', (username,)
        ).fetchone()
        
        if existing_user:
            conn.close()
            flash('用户名已存在，请选择其他用户名', 'danger')
            return redirect(url_for('register'))
        
        # 创建新用户
        hashed_password = generate_password_hash(password)
        conn.execute(
            'INSERT INTO users (username, password) VALUES (?, ?)',
            (username, hashed_password)
        )
        conn.commit()
        conn.close()
        
        flash('注册成功！请登录', 'success')
        return redirect(url_for('login'))
    
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        
        if not username or not password:
            flash('用户名和密码不能为空', 'danger')
            return redirect(url_for('login'))
        
        conn = get_db_connection()
        user = conn.execute(
            'SELECT * FROM users WHERE username = ?', (username,)
        ).fetchone()
        conn.close()
        
        if user and check_password_hash(user['password'], password):
            session['user_id'] = user['id']
            session['username'] = user['username']
            flash(f'欢迎回来，{username}！', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('用户名或密码错误', 'danger')
            return redirect(url_for('login'))
    
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    flash('已成功退出登录', 'info')
    return redirect(url_for('index'))

@app.route('/dashboard')
@login_required
def dashboard():
    conn = get_db_connection()
    memories = conn.execute(
        'SELECT * FROM memories WHERE user_id = ? ORDER BY created_at DESC',
        (session['user_id'],)
    ).fetchall()
    conn.close()
    return render_template('dashboard.html', memories=memories)

@app.route('/create', methods=['GET', 'POST'])
@login_required
def create_memory():
    if request.method == 'POST':
        title = request.form.get('title', '').strip()
        content = request.form.get('content', '').strip()
        
        if not title:
            flash('请输入记忆标题', 'danger')
            return redirect(url_for('create_memory'))
        
        # 处理媒体文件上传
        media_path = None
        media_type = None
        
        if 'media' in request.files:
            file = request.files['media']
            if file and file.filename:
                if allowed_file(file.filename):
                    filename = secure_filename(file.filename)
                    unique_filename = f'{uuid.uuid4().hex}_{filename}'
                    media_path = os.path.join(MEMORY_FOLDER, unique_filename)
                    file.save(media_path)
                    media_type = get_file_type(filename)
        
        # 生成唯一 MEMORY_ID
        memory_id = generate_memory_id()
        
        # 处理二维码定制选项
        qr_options = {
            'fg_color': request.form.get('fg_color', '#000000'),
            'bg_color': request.form.get('bg_color', '#FFFFFF'),
            'error_correction': request.form.get('error_correction', 'H')
        }
        
        # 处理背景图上传
        if 'background' in request.files:
            bg_file = request.files['background']
            if bg_file and bg_file.filename:
                if get_file_type(bg_file.filename) == 'image':
                    bg_filename = secure_filename(bg_file.filename)
                    bg_unique = f'{uuid.uuid4().hex}_{bg_filename}'
                    bg_path = os.path.join(MEMORY_FOLDER, bg_unique)
                    bg_file.save(bg_path)
                    qr_options['background_img_path'] = bg_path
        
        # 处理 Logo 上传
        if 'logo' in request.files:
            logo_file = request.files['logo']
            if logo_file and logo_file.filename:
                if get_file_type(logo_file.filename) == 'image':
                    logo_filename = secure_filename(logo_file.filename)
                    logo_unique = f'{uuid.uuid4().hex}_{logo_filename}'
                    logo_path = os.path.join(MEMORY_FOLDER, logo_unique)
                    logo_file.save(logo_path)
                    qr_options['logo_path'] = logo_path
        
        # 生成二维码
        qr_filename = generate_qr_code(memory_id, qr_options)
        qr_path = os.path.join(QR_FOLDER, qr_filename)
        
        # 保存到数据库
        conn = get_db_connection()
        conn.execute(
            '''INSERT INTO memories (memory_id, user_id, title, content, media_path, media_type, qr_path)
               VALUES (?, ?, ?, ?, ?, ?, ?)''',
            (memory_id, session['user_id'], title, content, media_path, media_type, qr_path)
        )
        conn.commit()
        conn.close()
        
        flash('记忆创建成功！', 'success')
        return redirect(url_for('view_memory', memory_id=memory_id))
    
    return render_template('create_memory.html')

@app.route('/memory/<memory_id>')
@login_required
def view_memory(memory_id):
    conn = get_db_connection()
    memory = conn.execute(
        'SELECT * FROM memories WHERE memory_id = ? AND user_id = ?',
        (memory_id, session['user_id'])
    ).fetchone()
    conn.close()
    
    if not memory:
        flash('记忆不存在或您无权访问', 'danger')
        return redirect(url_for('dashboard'))
    
    return render_template('view_memory.html', memory=memory)

@app.route('/decode', methods=['GET', 'POST'])
def decode_qr():
    if request.method == 'POST':
        if 'qr_image' not in request.files:
            flash('请上传二维码图片', 'danger')
            return redirect(url_for('decode_qr'))
        
        file = request.files['qr_image']
        if not file or not file.filename:
            flash('请选择有效的图片文件', 'danger')
            return redirect(url_for('decode_qr'))
        
        if get_file_type(file.filename) != 'image':
            flash('请上传有效的图片格式（PNG、JPG、GIF等）', 'danger')
            return redirect(url_for('decode_qr'))
        
        # 保存上传的图片
        filename = secure_filename(file.filename)
        temp_path = os.path.join(UPLOAD_FOLDER, f'temp_{uuid.uuid4().hex}_{filename}')
        file.save(temp_path)
        
        # 解码二维码
        decoded_data = decode_qr_code(temp_path)
        
        # 清理临时文件
        if os.path.exists(temp_path):
            os.remove(temp_path)
        
        if not decoded_data:
            flash('未能识别二维码，请确保图片清晰且包含有效的二维码', 'danger')
            return redirect(url_for('decode_qr'))
        
        # 检查是否登录
        if 'user_id' not in session:
            flash('检测到二维码！请先登录以解锁记忆内容', 'warning')
            session['pending_memory_id'] = decoded_data
            return redirect(url_for('login'))
        
        # 查找对应的记忆
        conn = get_db_connection()
        memory = conn.execute(
            'SELECT * FROM memories WHERE memory_id = ?',
            (decoded_data,)
        ).fetchone()
        
        if not memory:
            conn.close()
            flash(f'未找到与二维码 "{decoded_data}" 关联的记忆', 'danger')
            return redirect(url_for('decode_qr'))
        
        # 检查权限（只有创建者才能查看）
        if memory['user_id'] != session['user_id']:
            conn.close()
            flash('您无权访问此记忆，这是其他人的私密记忆', 'danger')
            return redirect(url_for('decode_qr'))
        
        conn.close()
        
        flash('记忆解锁成功！', 'success')
        return redirect(url_for('view_memory', memory_id=decoded_data))
    
    return render_template('decode_qr.html')

@app.route('/shop')
def shop():
    products = [
        {
            'id': 1,
            'name': '时光贴纸套装',
            'description': '10张高品质防水贴纸，包含专属记忆二维码',
            'price': '¥29.90',
            'image': 'sticker_pack'
        },
        {
            'id': 2,
            'name': '定制相框',
            'description': '木质相框，内置发光记忆二维码展示区',
            'price': '¥99.00',
            'image': 'photo_frame'
        },
        {
            'id': 3,
            'name': '时光胶囊礼盒',
            'description': '精美礼盒套装，包含定制二维码卡片、存储盒',
            'price': '¥199.00',
            'image': 'gift_box'
        },
        {
            'id': 4,
            'name': '专业打印服务',
            'description': '高清打印您的个性化二维码，支持多种材质',
            'price': '¥19.90起',
            'image': 'print_service'
        }
    ]
    return render_template('shop.html', products=products)

@app.route('/concepts')
def concepts():
    future_features = [
        {
            'title': '时光胶囊',
            'description': '将记忆封存，设定未来某个时间点才能解锁。可以是生日祝福、纪念日惊喜，让时间成为最好的礼物。',
            'icon': '⏰',
            'status': '开发中'
        },
        {
            'title': '多人共享',
            'description': '创建共同的记忆空间，与家人、朋友分享珍贵瞬间。每个人都可以添加内容，共同构建美好回忆。',
            'icon': '👥',
            'status': '规划中'
        },
        {
            'title': 'AR 体验',
            'description': '扫描二维码触发增强现实效果，让记忆以 3D 形式呈现。视频、图片、文字将在现实空间中展示。',
            'icon': '🕶️',
            'status': '概念阶段'
        },
        {
            'title': '离线存储',
            'description': '支持将记忆数据直接编码到二维码中，无需网络即可查看。适用于没有网络连接的特殊场景。',
            'icon': '📶',
            'status': '规划中'
        }
    ]
    return render_template('concepts.html', features=future_features)

@app.route('/uploads/<path:filename>')
def serve_upload(filename):
    return send_from_directory('uploads', filename)

@app.route('/api/preview_qr', methods=['POST'])
@login_required
def preview_qr():
    try:
        data = request.json
        memory_id = data.get('memory_id', 'PREVIEW')
        
        options = {
            'fg_color': data.get('fg_color', '#000000'),
            'bg_color': data.get('bg_color', '#FFFFFF'),
            'error_correction': data.get('error_correction', 'H')
        }
        
        # 生成预览二维码
        qr = segno.make(memory_id, error=options['error_correction'])
        preview_filename = f'preview_{uuid.uuid4().hex}.png'
        preview_path = os.path.join(QR_FOLDER, preview_filename)
        qr.save(preview_path, scale=5, border=2, dark=options['fg_color'], light=options['bg_color'])
        
        return jsonify({
            'success': True,
            'qr_url': url_for('serve_upload', filename=f'qrcodes/{preview_filename}')
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 400

if __name__ == '__main__':
    init_db()
    app.run(debug=True, host='0.0.0.0', port=5000)
