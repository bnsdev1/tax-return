"""Rules log repository with specific CRUD operations."""

from typing import Optional, List
from sqlalchemy.orm import Session
from db.models import RulesLog
from .base import BaseRepository


class RulesLogRepository(BaseRepository[RulesLog]):
    """Repository for rules log operations."""
    
    def __init__(self, db: Session):
        super().__init__(RulesLog, db)
    
    def get_by_tax_return(self, tax_return_id: int) -> List[RulesLog]:
        """Get all rules logs for a tax return."""
        return (
            self.db.query(RulesLog)
            .filter(RulesLog.tax_return_id == tax_return_id)
            .order_by(RulesLog.created_at.desc())
            .all()
        )
    
    def get_by_rule_name(self, tax_return_id: int, rule_name: str) -> List[RulesLog]:
        """Get rules logs by rule name for a tax return."""
        return (
            self.db.query(RulesLog)
            .filter(
                RulesLog.tax_return_id == tax_return_id,
                RulesLog.rule_name == rule_name
            )
            .order_by(RulesLog.created_at.desc())
            .all()
        )
    
    def get_by_category(self, tax_return_id: int, category: str) -> List[RulesLog]:
        """Get rules logs by category for a tax return."""
        return (
            self.db.query(RulesLog)
            .filter(
                RulesLog.tax_return_id == tax_return_id,
                RulesLog.rule_category == category
            )
            .all()
        )
    
    def get_failed_executions(self, tax_return_id: int) -> List[RulesLog]:
        """Get all failed rule executions for a tax return."""
        return (
            self.db.query(RulesLog)
            .filter(
                RulesLog.tax_return_id == tax_return_id,
                RulesLog.success == False
            )
            .all()
        )
    
    def get_successful_executions(self, tax_return_id: int) -> List[RulesLog]:
        """Get all successful rule executions for a tax return."""
        return (
            self.db.query(RulesLog)
            .filter(
                RulesLog.tax_return_id == tax_return_id,
                RulesLog.success == True
            )
            .all()
        )
    
    def create_rules_log(
        self,
        tax_return_id: int,
        rule_name: str,
        success: bool,
        rule_version: Optional[str] = None,
        rule_category: Optional[str] = None,
        input_data: Optional[str] = None,
        output_data: Optional[str] = None,
        execution_time_ms: Optional[int] = None,
        error_message: Optional[str] = None,
        warnings: Optional[str] = None,
    ) -> RulesLog:
        """Create a new rules log entry."""
        rules_log_data = {
            "tax_return_id": tax_return_id,
            "rule_name": rule_name,
            "success": success,
            "rule_version": rule_version,
            "rule_category": rule_category,
            "input_data": input_data,
            "output_data": output_data,
            "execution_time_ms": execution_time_ms,
            "error_message": error_message,
            "warnings": warnings,
        }
        
        return self.create(rules_log_data)
    
    def get_execution_stats(self, tax_return_id: int) -> dict:
        """Get execution statistics for a tax return."""
        from sqlalchemy import func
        
        from sqlalchemy import case
        
        stats = (
            self.db.query(
                func.count(RulesLog.id).label('total_executions'),
                func.sum(case((RulesLog.success == True, 1), else_=0)).label('successful'),
                func.sum(case((RulesLog.success == False, 1), else_=0)).label('failed'),
                func.avg(RulesLog.execution_time_ms).label('avg_execution_time'),
            )
            .filter(RulesLog.tax_return_id == tax_return_id)
            .first()
        )
        
        return {
            'total_executions': stats.total_executions or 0,
            'successful': stats.successful or 0,
            'failed': stats.failed or 0,
            'avg_execution_time': float(stats.avg_execution_time or 0),
        }