import uuid
import logging
from datetime import datetime
from config import ReportConfig

logger = logging.getLogger(__name__)


class ReportGenerator:
    """报告生成管理器"""

    def __init__(self):
        self.active_reports = {}
        self.completed_reports = {}
        self.max_active_reports = ReportConfig.MAX_ACTIVE_REPORTS

    def create_report_session(self, topic, requirements):
        """创建报告生成会话"""
        if len(self.active_reports) >= self.max_active_reports:
            raise Exception(f"活跃报告数量已达上限({self.max_active_reports})")

        report_id = str(uuid.uuid4())
        self.active_reports[report_id] = {
            'id': report_id,
            'topic': topic,
            'requirements': requirements,
            'status': 'generating_outline',
            'outline': None,
            'sections': {},
            'progress': 0,
            'created_at': datetime.now(),
            'completed_at': None,
            'error': None,
            'download_count': 0,
            'file_paths': {}
        }

        logger.info(f"创建报告会话: {report_id}, 主题: {topic}")
        return report_id

    def get_report_status(self, report_id):
        """获取报告生成状态"""
        return self.active_reports.get(report_id) or self.completed_reports.get(report_id)

    def update_report_progress(self, report_id, status, progress=None, **kwargs):
        """更新报告进度"""
        if report_id in self.active_reports:
            self.active_reports[report_id]['status'] = status
            if progress is not None:
                self.active_reports[report_id]['progress'] = progress
            for key, value in kwargs.items():
                self.active_reports[report_id][key] = value

            logger.debug(f"更新报告进度: {report_id}, 状态: {status}, 进度: {progress}%")

    def add_section_content(self, report_id, section_id, section_data):
        """添加章节内容"""
        if report_id in self.active_reports:
            self.active_reports[report_id]['sections'][section_id] = section_data
            logger.debug(f"添加章节内容: {report_id}, 章节: {section_id}")

    def complete_report(self, report_id):
        """标记报告为完成状态"""
        if report_id in self.active_reports:
            report_data = self.active_reports[report_id]
            report_data['status'] = 'completed'
            report_data['completed_at'] = datetime.now()
            report_data['progress'] = 100

            self._generate_report_summary(report_id)

            self.completed_reports[report_id] = report_data
            del self.active_reports[report_id]

            logger.info(f"报告生成完成: {report_id}, 主题: {report_data['topic']}")
            return True
        return False

    def mark_report_error(self, report_id, error_message):
        """标记报告生成失败"""
        if report_id in self.active_reports:
            self.active_reports[report_id]['status'] = 'error'
            self.active_reports[report_id]['error'] = error_message
            logger.error(f"报告生成失败: {report_id}, 错误: {error_message}")

    def _generate_report_summary(self, report_id):
        """生成报告摘要统计"""
        report_data = self.active_reports[report_id]

        total_words = 0
        if report_data.get('outline', {}).get('abstract'):
            total_words += len(report_data['outline']['abstract'])

        for section_data in report_data.get('sections', {}).values():
            if section_data.get('content'):
                total_words += len(section_data['content'])

        duration = None
        if report_data.get('completed_at') and report_data.get('created_at'):
            duration = report_data['completed_at'] - report_data['created_at']

        report_data['summary'] = {
            'total_words': total_words,
            'total_sections': len(report_data.get('sections', {})),
            'generation_duration': duration.total_seconds() if duration else None,
            'generation_duration_formatted': str(duration).split('.')[0] if duration else None
        }

    def increment_download_count(self, report_id):
        """增加下载计数"""
        report_data = self.active_reports.get(report_id) or self.completed_reports.get(report_id)
        if report_data:
            report_data['download_count'] = report_data.get('download_count', 0) + 1
            logger.info(f"报告下载计数更新: {report_id}, 次数: {report_data['download_count']}")

    def get_report_summary(self, report_id):
        """获取报告摘要"""
        report_data = self.active_reports.get(report_id) or self.completed_reports.get(report_id)
        if report_data and report_data.get('summary'):
            return report_data['summary']
        return None

    def get_all_reports(self):
        """获取所有报告数据"""
        all_reports = {}
        all_reports.update(self.active_reports)
        all_reports.update(self.completed_reports)
        return all_reports

    def get_active_count(self):
        """获取活跃报告数量"""
        return len(self.active_reports)

    def get_completed_count(self):
        """获取已完成报告数量"""
        return len(self.completed_reports)

    def get_total_count(self):
        """获取总报告数量"""
        return len(self.active_reports) + len(self.completed_reports)

    def cleanup_old_reports(self, hours=None):
        """清理旧的报告数据"""
        hours = hours or ReportConfig.REPORT_CLEANUP_HOURS
        current_time = datetime.now()
        expired_reports = []

        for report_id, report_data in list(self.completed_reports.items()):
            if report_data.get('completed_at'):
                age = current_time - report_data['completed_at']
                if age.total_seconds() > hours * 3600:
                    expired_reports.append(report_id)

        timeout_minutes = ReportConfig.REPORT_TIMEOUT
        for report_id, report_data in list(self.active_reports.items()):
            if report_data.get('created_at'):
                age = current_time - report_data['created_at']
                if age.total_seconds() > timeout_minutes * 60:
                    expired_reports.append(report_id)
                    self.mark_report_error(report_id, "报告生成超时")

        cleaned_count = 0
        for report_id in expired_reports:
            try:
                if report_id in self.completed_reports:
                    report_data = self.completed_reports.pop(report_id)
                elif report_id in self.active_reports:
                    report_data = self.active_reports.pop(report_id)
                else:
                    continue

                self._cleanup_report_files(report_data)
                cleaned_count += 1
                logger.info(f"清理过期/超时报告: {report_id}")

            except Exception as e:
                logger.warning(f"清理报告失败 {report_id}: {e}")

        if cleaned_count > 0:
            logger.info(f"清理任务完成，共清理 {cleaned_count} 个报告")

        return cleaned_count

    def _cleanup_report_files(self, report_data):
        """清理报告相关文件"""
        import os

        for file_path in report_data.get('file_paths', {}).values():
            try:
                if os.path.exists(file_path):
                    os.remove(file_path)
                    logger.debug(f"删除文件: {file_path}")
            except Exception as e:
                logger.warning(f"删除文件失败 {file_path}: {e}")

    def delete_report(self, report_id):
        """删除指定报告"""
        report_data = None

        if report_id in self.active_reports:
            report_data = self.active_reports.pop(report_id)
        elif report_id in self.completed_reports:
            report_data = self.completed_reports.pop(report_id)

        if report_data:
            self._cleanup_report_files(report_data)
            logger.info(f"删除报告: {report_id}")
            return True

        return False

    def get_statistics(self):
        """获取统计信息"""
        total_completed = len(self.completed_reports)
        total_active = len(self.active_reports)
        total_downloads = sum(report.get('download_count', 0) for report in self.completed_reports.values())
        generation_times = []
        for report in self.completed_reports.values():
            if report.get('summary', {}).get('generation_duration'):
                generation_times.append(report['summary']['generation_duration'])

        avg_generation_time = sum(generation_times) / len(generation_times) if generation_times else 0

        return {
            'total_reports': total_completed + total_active,
            'completed_reports': total_completed,
            'active_reports': total_active,
            'total_downloads': total_downloads,
            'average_generation_time': avg_generation_time,
            'max_active_reports': self.max_active_reports
        }

    def export_report_list(self):
        """导出报告列表（用于备份或迁移）"""
        export_data = {
            'export_time': datetime.now().isoformat(),
            'active_reports': self.active_reports,
            'completed_reports': self.completed_reports,
            'statistics': self.get_statistics()
        }
        return export_data

    def import_report_list(self, import_data):
        """导入报告列表（用于恢复或迁移）"""
        try:
            if 'active_reports' in import_data:
                self.active_reports.update(import_data['active_reports'])

            if 'completed_reports' in import_data:
                self.completed_reports.update(import_data['completed_reports'])

            logger.info("报告列表导入成功")
            return True

        except Exception as e:
            logger.error(f"报告列表导入失败: {e}")
            return False