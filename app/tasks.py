# app/tasks.py
from celery import Celery
from app import create_app
from app.models import File

celery = Celery(__name__)

@celery.task
def cleanup_trash(days=30):
    app = create_app()
    with app.app_context():
        old_files = File.query.filter(
            File.is_deleted == True,
            File.uploaded_at < datetime.utcnow() - timedelta(days=days)
        ).all()
        
        for file in old_files:
            try:
                os.remove(file.storage_path)
                db.session.delete(file)
            except Exception as e:
                db.session.rollback()
                current_app.logger.error(f"Cleanup error: {str(e)}")
        
        db.session.commit()