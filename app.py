"""
主应用入口
中央财经大学经济学院 - 经济学大模型聊天助手
"""

import os
import logging
import threading
from datetime import datetime
from flask import Flask, request, jsonify, render_template, send_file
from flask_cors import CORS

from config import get_config, ensure_directories, validate_config
from models.chatbot import QwenChatBot
from models.report_generator import ReportGenerator
from utils.document_utils import create_word_document
from utils.text_utils import validate_input

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def create_app():
    """创建Flask应用"""
    ensure_directories()
    validate_config()

    app = Flask(__name__)
    config_class = get_config()
    app.config.from_object(config_class)

    CORS(app)

    chatbot = QwenChatBot()
    report_generator = ReportGenerator()

    setup_cleanup_scheduler(report_generator)

    @app.route('/')
    def index():
        """主页"""
        return render_template('index.html')

    @app.route('/api/chat', methods=['POST'])
    def chat():
        """聊天API端点"""
        try:
            data = request.get_json()

            if not data or 'message' not in data:
                return jsonify({"error": "消息内容不能为空"}), 400

            user_message = data.get('message', '').strip()
            if not user_message:
                return jsonify({"error": "消息内容不能为空"}), 400

            validation_error = validate_input(user_message, max_length=4000)
            if validation_error:
                return jsonify({"error": validation_error}), 400

            if not chatbot.is_ready():
                return jsonify({
                    "error": "模型正在加载中，请稍后再试...",
                    "loading": True
                }), 503

            max_new_tokens = min(data.get('max_new_tokens', 1024), 4096)
            temperature = max(0.1, min(data.get('temperature', 0.7), 2.0))
            enable_thinking = data.get('enable_thinking', True)

            response = chatbot.generate_response(
                user_message,
                max_new_tokens=max_new_tokens,
                temperature=temperature,
                enable_thinking=enable_thinking
            )

            return jsonify({
                "message": response["content"],
                "thinking": response.get("thinking"),
                "success": response["success"],
                "timestamp": datetime.now().isoformat()
            })

        except Exception as e:
            logger.error(f"处理聊天请求时发生错误: {str(e)}")
            return jsonify({"error": f"服务器错误: {str(e)}"}), 500

    @app.route('/api/report/generate', methods=['POST'])
    def generate_report():
        """生成报告API"""
        try:
            data = request.get_json()

            if not data or 'topic' not in data:
                return jsonify({"error": "报告主题不能为空"}), 400

            topic = data.get('topic', '').strip()
            requirements = data.get('requirements', '').strip()

            if not topic:
                return jsonify({"error": "报告主题不能为空"}), 400

            topic_error = validate_input(topic, max_length=200)
            if topic_error:
                return jsonify({"error": f"主题{topic_error}"}), 400

            if requirements:
                req_error = validate_input(requirements, max_length=2000)
                if req_error:
                    return jsonify({"error": f"要求{req_error}"}), 400

            if not chatbot.is_ready():
                return jsonify({
                    "error": "模型正在加载中，请稍后再试...",
                    "loading": True
                }), 503

            report_id = report_generator.create_report_session(topic, requirements)
            logger.info(f"创建报告生成会话 - Report ID: {report_id}, Topic: {topic}")

            generation_thread = threading.Thread(
                target=generate_report_async,
                args=(report_id, topic, requirements, chatbot, report_generator),
                daemon=True
            )
            generation_thread.start()

            return jsonify({
                "report_id": report_id,
                "status": "generating",
                "message": "报告生成已开始"
            })

        except Exception as e:
            logger.error(f"生成报告请求处理失败: {str(e)}")
            return jsonify({"error": f"服务器错误: {str(e)}"}), 500

    @app.route('/api/report/status/<report_id>', methods=['GET'])
    def get_report_status(report_id):
        """获取报告生成状态"""
        try:
            report_status = report_generator.get_report_status(report_id)

            if not report_status:
                return jsonify({"error": "报告不存在"}), 404

            return jsonify({
                "report_id": report_id,
                "status": report_status['status'],
                "progress": report_status['progress'],
                "outline": report_status.get('outline'),
                "error": report_status.get('error'),
                "sections_completed": len(report_status.get('sections', {})),
                "total_sections": len(report_status.get('outline', {}).get('sections', [])) if report_status.get(
                    'outline') else 0,
                "created_at": report_status.get('created_at').isoformat() if report_status.get('created_at') else None
            })

        except Exception as e:
            logger.error(f"获取报告状态失败: {str(e)}")
            return jsonify({"error": f"获取状态失败: {str(e)}"}), 500

    @app.route('/api/report/summary/<report_id>', methods=['GET'])
    def get_report_summary(report_id):
        """获取报告摘要信息"""
        try:
            summary = report_generator.get_report_summary(report_id)
            report_data = report_generator.get_report_status(report_id)

            if not report_data:
                return jsonify({"error": "报告不存在"}), 404

            return jsonify({
                "report_id": report_id,
                "topic": report_data.get('topic'),
                "status": report_data.get('status'),
                "created_at": report_data.get('created_at').isoformat() if report_data.get('created_at') else None,
                "completed_at": report_data.get('completed_at').isoformat() if report_data.get(
                    'completed_at') else None,
                "download_count": report_data.get('download_count', 0),
                "summary": summary
            })

        except Exception as e:
            logger.error(f"获取报告摘要失败: {str(e)}")
            return jsonify({"error": f"获取摘要失败: {str(e)}"}), 500

    @app.route('/api/report/download/<report_id>/docx', methods=['GET'])
    def download_report_word(report_id):
        """下载Word报告"""
        try:
            logger.info(f"收到下载请求 - Report ID: {report_id}")

            report_status = report_generator.get_report_status(report_id)

            if not report_status:
                logger.error(f"报告不存在: {report_id}")
                return jsonify({"error": "报告不存在"}), 404

            if report_status['status'] != 'completed':
                logger.error(f"报告未完成: {report_id}, status: {report_status['status']}")
                return jsonify({"error": "报告未完成"}), 400

            logger.info(f"报告状态验证通过 - Report ID: {report_id}")

            report_generator.increment_download_count(report_id)

            document = create_word_document(report_status)

            safe_topic = ''.join(
                c for c in report_status.get('topic', 'report') if c.isalnum() or c in (' ', '-', '_')).rstrip()
            safe_topic = safe_topic[:30]  # 限制长度
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"report_{safe_topic}_{timestamp}.docx"

            import tempfile
            with tempfile.NamedTemporaryFile(delete=False, suffix='.docx') as tmp_file:
                document.save(tmp_file.name)

                threading.Timer(10.0, lambda: cleanup_temp_file(tmp_file.name)).start()

                return send_file(
                    tmp_file.name,
                    as_attachment=True,
                    download_name=filename,
                    mimetype='application/vnd.openxmlformats-officedocument.wordprocessingml.document'
                )

        except Exception as e:
            logger.error(f"下载报告失败 - Report ID: {report_id}, Error: {str(e)}", exc_info=True)
            return jsonify({"error": f"下载失败: {str(e)}"}), 500

    @app.route('/api/report/list', methods=['GET'])
    def list_reports():
        """获取报告列表"""
        try:
            reports_data = report_generator.get_all_reports()

            reports = []
            for report_id, report_data in reports_data.items():
                try:
                    reports.append({
                        "id": report_id,
                        "topic": report_data.get('topic', '未命名报告'),
                        "status": report_data.get('status', 'unknown'),
                        "created_at": report_data.get('created_at').isoformat() if report_data.get(
                            'created_at') else None,
                        "completed_at": report_data.get('completed_at').isoformat() if report_data.get(
                            'completed_at') else None,
                        "download_count": report_data.get('download_count', 0),
                        "progress": report_data.get('progress', 0)
                    })
                except Exception as e:
                    logger.warning(f"处理报告数据失败 - Report ID: {report_id}, Error: {e}")

            reports.sort(key=lambda x: x['created_at'] or '', reverse=True)

            return jsonify({
                "reports": reports,
                "total": len(reports)
            })

        except Exception as e:
            logger.error(f"获取报告列表失败: {str(e)}")
            return jsonify({"error": f"获取报告列表失败: {str(e)}"}), 500

    @app.route('/api/status', methods=['GET'])
    def status():
        """获取服务状态"""
        return jsonify({
            "status": "ready" if chatbot.is_ready() else "loading",
            "model_name": chatbot.model_name,
            "device": getattr(chatbot, 'device', None),
            "loading": chatbot.is_loading,
            "active_reports": report_generator.get_active_count(),
            "completed_reports": report_generator.get_completed_count()
        })

    @app.route('/api/health', methods=['GET'])
    def health():
        """健康检查"""
        return jsonify({
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "model_ready": chatbot.is_ready()
        })

    @app.errorhandler(404)
    def not_found(error):
        return jsonify({"error": "API端点不存在"}), 404

    @app.errorhandler(500)
    def internal_error(error):
        logger.error(f"服务器内部错误: {str(error)}")
        return jsonify({"error": "服务器内部错误"}), 500

    return app


def generate_report_async(report_id, topic, requirements, chatbot, report_generator):
    """异步生成报告"""
    try:
        logger.info(f"开始生成报告 - Report ID: {report_id}")

        logger.info(f"开始生成报告大纲 - Report ID: {report_id}")
        report_generator.update_report_progress(report_id, 'generating_outline', 10)

        outline_response = chatbot.generate_report_outline(topic, requirements)
        if not outline_response['success']:
            raise Exception("生成大纲失败")

        try:
            import re
            import json
            content = outline_response['content']
            json_match = re.search(r'\{.*\}', content, re.DOTALL)
            if json_match:
                outline_data = json.loads(json_match.group())
            else:
                raise ValueError("无法解析大纲JSON")
        except (json.JSONDecodeError, ValueError) as e:
            logger.error(f"解析大纲失败: {e}")
            raise Exception("大纲格式解析失败")

        if not outline_data.get('sections'):
            raise Exception("大纲中缺少章节信息")

        report_generator.update_report_progress(report_id, 'generating_sections', 20, outline=outline_data)
        logger.info(f"大纲生成完成，共{len(outline_data['sections'])}个章节")

        sections = outline_data.get('sections', [])
        total_sections = len(sections)

        for i, section in enumerate(sections):
            logger.info(f"生成章节 {i + 1}/{total_sections} - {section.get('title', '')}")

            progress = 20 + int((i / total_sections) * 60)
            report_generator.update_report_progress(
                report_id,
                'generating_sections',
                progress,
                sections_completed=i,
                total_sections=total_sections
            )

            section_response = chatbot.generate_section_content(
                section.get('title', ''),
                section.get('description', ''),
                f"报告主题：{topic}\n报告要求：{requirements}"
            )

            if section_response['success']:
                report_generator.add_section_content(report_id, section['id'], {
                    'title': section['title'],
                    'content': section_response['content'],
                    'generated_at': datetime.now().isoformat()
                })
                logger.info(f"章节 {i + 1} 生成完成")
            else:
                logger.error(f"生成章节内容失败: {section.get('title', '')}")
                report_generator.add_section_content(report_id, section['id'], {
                    'title': section.get('title', ''),
                    'content': f"本章节内容生成时遇到技术问题，建议手动补充关于\"{section.get('title', '')}\"的相关内容。",
                    'generated_at': datetime.now().isoformat(),
                    'error': True
                })

        logger.info(f"完成报告生成 - Report ID: {report_id}")
        report_generator.update_report_progress(report_id, 'finalizing', 90)

        report_generator.complete_report(report_id)
        logger.info(f"报告生成完成 - Report ID: {report_id}")

    except Exception as e:
        logger.error(f"报告生成失败 - Report ID: {report_id}, Error: {str(e)}", exc_info=True)
        report_generator.update_report_progress(report_id, 'error', error=str(e))


def setup_cleanup_scheduler(report_generator):
    """设置定期清理任务"""

    def cleanup_worker():
        import time
        while True:
            try:
                time.sleep(3600)
                report_generator.cleanup_old_reports(hours=24)
            except Exception as e:
                logger.error(f"清理任务失败: {e}")

    cleanup_thread = threading.Thread(target=cleanup_worker, daemon=True)
    cleanup_thread.start()
    logger.info("启动定期清理任务")


def cleanup_temp_file(file_path):
    """清理临时文件"""
    try:
        if os.path.exists(file_path):
            os.remove(file_path)
            logger.info(f"临时文件已清理: {file_path}")
    except Exception as e:
        logger.warning(f"清理临时文件失败: {e}")


if __name__ == '__main__':
    print("=== CUFE经济学大模型聊天应用 ===")
    print("正在启动服务器...")

    app = create_app()
    config_class = get_config()

    try:
        app.run(
            host=config_class.HOST,
            port=config_class.PORT,
            debug=config_class.DEBUG,
            threaded=True,
            use_reloader=False
        )
    except Exception as e:
        logger.error(f"启动Flask应用失败: {e}")
        print(f"启动失败: {e}")