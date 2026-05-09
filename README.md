# Memory QR (记忆二维码)

一个基于 Flask 的全栈 Web 应用，旨在将二维码转化为通往私密记忆的"加密钥匙"，支持用户通过自定义颜色与背景图设计个性化二维码，并集成了解码校验与权限拦截机制，确保只有授权用户才能解锁并查看背后的图文或视频内容。

## 项目特性

### 🎯 核心功能
- **用户安全系统**：注册、登录、权限控制，未登录用户无法访问解码和查看记忆接口
- **记忆存储与可视化设计器**：支持文字、图片、视频上传，生成唯一 MEMORY_ID
- **个性化二维码生成**：自定义前景色/背景色、背景图嵌入、Logo 中心嵌入
- **Web 端解码器**：上传二维码图片，自动识别并校验权限后展示记忆内容
- **实时预览**：二维码设计器支持颜色调整的实时预览

### 🛠 技术栈
- **后端核心**：Python Flask 3.1.3
- **前端技术**：HTML5 + CSS3 + JavaScript（原生开发，响应式设计）
- **数据存储**：SQLite（用户与权限管理）+ 本地文件系统（媒体资源）
- **二维码处理**：
  - `qrcode` + `segno`：基础生成与颜色定制
  - `Pillow`：图像处理、Logo 嵌入
  - `opencv-python`：二维码解码识别

## 项目结构

```
memoryQR/
├── app.py                    # Flask 主应用（路由、数据库模型、图像处理逻辑）
├── requirements.txt          # Python 依赖包列表
├── .gitignore               # Git 忽略文件配置
├── LICENSE                  # 许可证文件
├── README.md                # 项目说明文档
├── templates/               # HTML 模板目录
│   ├── base.html           # 基础模板（导航栏、页脚）
│   ├── index.html          # 首页
│   ├── login.html          # 登录页面
│   ├── register.html       # 注册页面
│   ├── dashboard.html      # 用户仪表盘（记忆列表）
│   ├── create_memory.html  # 创建记忆（设计器）
│   ├── view_memory.html    # 查看记忆详情
│   ├── decode_qr.html      # 二维码解码页面
│   ├── shop.html           # 商城页面
│   └── concepts.html       # 概念页
├── static/                  # 静态资源目录
│   ├── css/
│   │   └── style.css       # 主样式文件
│   └── js/
│       └── main.js         # 主 JavaScript 文件
├── uploads/                 # 上传文件目录
│   ├── qrcodes/            # 生成的二维码图片
│   └── memories/           # 用户上传的媒体文件
└── .venv/                  # Python 虚拟环境（已忽略）
```

## 快速开始

### 环境要求
- Python 3.8+
- pip 包管理器

### 安装步骤

#### 1. 克隆/进入项目目录
```bash
cd d:\WorkCode\codeLabel\SoloCoder\0028\memoryQR
```

#### 2. 创建虚拟环境（已完成）
```bash
python -m venv .venv
```

#### 3. 激活虚拟环境

**Windows PowerShell:**
```powershell
.venv\Scripts\activate
```

**Windows CMD:**
```cmd
.venv\Scripts\activate.bat
```

**macOS/Linux:**
```bash
source .venv/bin/activate
```

#### 4. 安装依赖（已完成）
```bash
pip install -r requirements.txt
```

#### 5. 运行应用
```bash
python app.py
```

#### 6. 访问应用
打开浏览器访问：
- 本地地址：http://127.0.0.1:5000
- 局域网地址：http://<你的IP>:5000

## 功能模块详解

### 1. 用户安全系统

#### 注册功能 (`/register`)
- 用户名唯一性校验
- 密码加密存储（使用 Werkzeug security）
- 密码长度校验（至少6位）
- 确认密码一致性校验

#### 登录功能 (`/login`)
- 用户名密码校验
- Session 会话管理
- 登录后自动跳转

#### 权限控制
- 使用 `@login_required` 装饰器保护敏感路由
- 未登录用户访问受限页面会被重定向到登录页
- 解码功能：未登录用户只能检测二维码，无法解锁记忆内容

### 2. 记忆存储与可视化设计器

#### 内容录入 (`/create`)
- 标题（必填）
- 文字内容（可选）
- 媒体文件上传（图片/视频，可选）
- 自动生成唯一 MEMORY_ID（8位大写字符）

#### 二维码定制选项
- **色彩定义**：取色器选择前景色和背景色
- **Logo 嵌入**：上传 Logo 图片，自动居中放置
- **背景图**：上传背景图片，二维码半透明叠加
- **纠错级别**：L(7%) / M(15%) / Q(25%) / H(30%)

#### 实时预览
- 颜色调整后自动刷新预览
- API 接口 `/api/preview_qr` 提供预览服务

### 3. Web 端解码器 (`/decode`)

#### 功能流程
1. 用户上传二维码图片
2. 后端使用 OpenCV 解码识别 MEMORY_ID
3. 校验当前会话登录状态
   - 未登录：提示登录，保存 pending_memory_id
   - 已登录：查找对应的记忆记录
4. 权限校验（只有创建者才能查看）
5. 有权限：渲染记忆详情页
6. 无权限：拦截并提示

### 4. 扩展板块

#### 商城 (`/shop`)
- 静态展示实体产品
- 包含：时光贴纸套装、定制相框、时光胶囊礼盒、专业打印服务
- "即将上线"状态提示

#### 概念页 (`/concepts`)
- 未来功能规划展示
- 包含：时光胶囊、多人共享、AR 体验、离线存储
- 发展路线时间线

## 数据库设计

### 用户表 (users)
| 字段 | 类型 | 说明 |
|------|------|------|
| id | INTEGER | 主键，自增 |
| username | TEXT | 用户名，唯一 |
| password | TEXT | 加密后的密码 |
| created_at | TIMESTAMP | 创建时间 |

### 记忆表 (memories)
| 字段 | 类型 | 说明 |
|------|------|------|
| id | INTEGER | 主键，自增 |
| memory_id | TEXT | 唯一记忆ID，8位 |
| user_id | INTEGER | 所属用户ID，外键 |
| title | TEXT | 记忆标题 |
| content | TEXT | 文字内容 |
| media_path | TEXT | 媒体文件路径 |
| media_type | TEXT | 媒体类型（image/video） |
| qr_path | TEXT | 二维码图片路径 |
| created_at | TIMESTAMP | 创建时间 |

## 关键代码说明

### 二维码生成 (`app.py:132`)
```python
def generate_qr_code(memory_id, options=None):
    # 使用 segno 生成二维码
    qr = segno.make(memory_id, error=error_correction)
    
    # 支持背景图、Logo 嵌入
    # 使用 Pillow 进行图像处理
    # 最终保存为 PNG 格式
```

### 二维码解码 (`app.py:224`)
```python
def decode_qr_code(image_path):
    # 使用 OpenCV QRCodeDetector
    qr_detector = cv2.QRCodeDetector()
    data, bbox, straight_qrcode = qr_detector.detectAndDecode(img)
    
    # 备用方案：PIL 转换后重试
    # 返回解码的 MEMORY_ID
```

### 权限装饰器 (`app.py:105`)
```python
def login_required(f):
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('请先登录以访问此页面', 'warning')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function
```

## API 接口

### POST `/api/preview_qr`
二维码预览接口，用于设计器实时预览

**请求参数：**
```json
{
    "memory_id": "PREVIEW",
    "fg_color": "#000000",
    "bg_color": "#FFFFFF",
    "error_correction": "H"
}
```

**响应：**
```json
{
    "success": true,
    "qr_url": "/uploads/qrcodes/preview_xxx.png"
}
```

## 支持的文件格式

### 图片格式
- PNG, JPG, JPEG, GIF, BMP

### 视频格式
- MP4, WebM, OGG

### 文件大小限制
- 最大 50MB

## 注意事项

1. **开发模式**：当前运行在 debug 模式，仅用于开发测试，生产环境需关闭
2. **Secret Key**：生产环境应修改 `app.secret_key` 为安全随机值
3. **数据库**：首次运行自动创建 SQLite 数据库 `memory_qr.db`
4. **上传目录**：`uploads/` 目录需要写入权限

## 开发计划

- [x] 基础框架搭建
- [x] 用户注册登录系统
- [x] 记忆存储功能
- [x] 二维码生成与定制
- [x] 二维码解码功能
- [x] 权限控制机制
- [x] 响应式前端界面
- [ ] 时光胶囊功能（定时解锁）
- [ ] 多人共享记忆空间
- [ ] AR 体验集成
- [ ] 移动端适配优化

## 许可证

本项目仅供学习和演示使用。
