# 🌐 CUFE-ECON 经济学大模型助手

中央财经大学经济学院研发的 CUFE-ECON 经济学大模型助手，基于 Qwen3 模型，专注于经济学研究、教学与实践，提供智能问答、报告生成及专业辅助工具。

## ✨ 功能特色

- 💬 **智能对话**：支持经济学领域的专业问答与逻辑推理
- 📑 **报告生成**：自动生成结构化的经济学研究报告
- 📄 **文档导出**：一键导出 Word 格式的专业报告
- ⚡ **实时交互**：展示思维过程，支持实时进度追踪
- 🖥️ **用户友好**：现代化 Web 界面，支持 Markdown 渲染

## 🚀 快速开始

### 环境要求

- **Python**：3.8 或更高版本
- **GPU**：支持 CUDA（推荐）


### 安装步骤

1. **克隆项目**

```bash
git clone https://github.com/kikiwx/CUFE-ECON-Model.git
cd cufe-economics-chatbot
```

2. **创建虚拟环境**

```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows
```

3. **安装依赖**

```bash
pip install -r requirements.txt
```

4. **运行应用**

```bash
python app.py
```

5. **访问应用**

打开浏览器，访问：http://127.0.0.1:5000

## ⚙️ 配置说明

### 模型配置

在 `config.py` 文件中设置模型路径和服务参数：

```python
# 模型路径
MODEL_PATH = os.environ.get('MODEL_PATH', r"/model")

# 设备配置
DEVICE = os.environ.get('DEVICE', 'auto')
```

## 📜 许可证

本项目采用 MIT 许可证，详情请查看 LICENSE 文件。
