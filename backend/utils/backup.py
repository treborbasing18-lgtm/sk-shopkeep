import os
import shutil
from datetime import datetime
from flask import Blueprint, send_file, jsonify
from backend.auth.auth_service import AuthService
from backend.config import Config

backup_bp = Blueprint('backup', __name__, url_prefix='/api/backup')


class BackupService:

    @staticmethod
    def get_db_path():
        if os.environ.get('RENDER'):
            return '/tmp/shopkeep.db'
        return Config.DATABASE_PATH

    @staticmethod
    def get_backup_dir():
        if os.environ.get('RENDER'):
            return '/tmp/backups'
        return Config.BACKUP_PATH

    @staticmethod
    def create_dated_backup():
        """Copy the live DB to backups/shopkeep_YYYYMMDD_HHMMSS.db"""
        db_path     = BackupService.get_db_path()
        backup_dir  = BackupService.get_backup_dir()

        if not os.path.exists(db_path):
            raise FileNotFoundError("Database file not found")

        os.makedirs(backup_dir, exist_ok=True)

        timestamp   = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_name = f"shopkeep_{timestamp}.db"
        backup_path = os.path.join(backup_dir, backup_name)

        shutil.copy2(db_path, backup_path)
        return backup_path, backup_name

    @staticmethod
    def list_backups():
        backup_dir = BackupService.get_backup_dir()
        if not os.path.exists(backup_dir):
            return []
        files = []
        for fname in sorted(os.listdir(backup_dir), reverse=True):
            if fname.endswith('.db'):
                fpath = os.path.join(backup_dir, fname)
                files.append({
                    'filename': fname,
                    'size_kb':  round(os.path.getsize(fpath) / 1024, 1),
                    'created':  datetime.fromtimestamp(
                                    os.path.getmtime(fpath)
                                ).strftime('%Y-%m-%d %H:%M:%S')
                })
        return files


# ── Routes ────────────────────────────────────────────────────────────────────

@backup_bp.route('/download', methods=['GET'])
@AuthService.require_admin
def download_backup():
    """Download the live database file directly."""
    try:
        db_path = BackupService.get_db_path()
        if not os.path.exists(db_path):
            return jsonify({'success': False, 'error': 'Database file not found'}), 404

        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        return send_file(
            db_path,
            as_attachment=True,
            download_name=f"shopkeep_backup_{timestamp}.db",
            mimetype='application/octet-stream'
        )
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@backup_bp.route('/create', methods=['POST'])
@AuthService.require_admin
def create_backup():
    """Save a dated copy to the backups folder."""
    try:
        from backend.models.log_model import LogModel
        backup_path, backup_name = BackupService.create_dated_backup()
        user = AuthService.get_current_user()
        LogModel.create(user['id'], 'BACKUP_CREATED', f"Backup saved: {backup_name}")
        return jsonify({'success': True, 'filename': backup_name})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@backup_bp.route('/list', methods=['GET'])
@AuthService.require_admin
def list_backups():
    """List all saved backup files."""
    try:
        return jsonify({'backups': BackupService.list_backups()})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500
