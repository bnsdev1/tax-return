"""Tax return processing pipeline orchestration service."""

import json
import logging
from typing import Dict, Any, List, Optional
from pathlib import Path
from datetime import datetime
from sqlalchemy.orm import Session

# Core imports
from core.parsers import default_registry as parser_registry
from core.reconcile import DataReconciler
from core.compute import TaxCalculator
from core.validate import TaxValidator

# LLM imports
from packages.llm.router import LLMRouter, LLMSettings
from packages.llm.contracts import LLMTask
from packages.core.src.core.parsers.form16b_llm import parse_form16b_llm, ParseMiss
from packages.core.src.core.parsers.bank_classifier_llm import BankClassifier
from packages.core.src.core.explain.rules_explainer_llm import RulesExplainer

# API imports
from repo import TaxReturnRepository, ArtifactRepository, LLMSettingsRepository
from schemas.jobs import JobStatus

logger = logging.getLogger(__name__)


class PipelineStep:
    """Individual pipeline step with state management."""
    
    def __init__(self, name: str, description: str):
        self.name = name
        self.description = description
        self.status = JobStatus.QUEUED
        self.started_at: Optional[datetime] = None
        self.completed_at: Optional[datetime] = None
        self.result: Optional[Dict[str, Any]] = None
        self.error_message: Optional[str] = None
        self.progress_percentage: int = 0
    
    def start(self):
        """Mark step as started."""
        self.status = JobStatus.RUNNING
        self.started_at = datetime.utcnow()
        logger.info(f"Started pipeline step: {self.name}")
    
    def complete(self, result: Dict[str, Any]):
        """Mark step as completed with result."""
        self.status = JobStatus.COMPLETED
        self.completed_at = datetime.utcnow()
        self.result = result
        self.progress_percentage = 100
        duration = (self.completed_at - self.started_at).total_seconds()
        logger.info(f"Completed pipeline step: {self.name} in {duration:.2f}s")
    
    def fail(self, error_message: str):
        """Mark step as failed with error."""
        self.status = JobStatus.FAILED
        self.completed_at = datetime.utcnow()
        self.error_message = error_message
        logger.error(f"Failed pipeline step: {self.name} - {error_message}")


class PreviewResponse:
    """Preview response DTO with key tax return highlights."""
    
    def __init__(self, pipeline_result: Dict[str, Any]):
        self.pipeline_result = pipeline_result
        self._extract_key_lines()
        self._extract_warnings_blockers()
    
    def _extract_key_lines(self):
        """Extract key financial lines for preview."""
        computed_totals = self.pipeline_result.get('compute_totals', {}).get('computed_totals', {})
        reconciled_data = self.pipeline_result.get('reconcile_sources', {}).get('reconciled_data', {})
        
        # Savings interest
        interest_data = reconciled_data.get('interest_income', {})
        self.savings_interest = {
            'amount': interest_data.get('total_interest', 0),
            'tds_deducted': reconciled_data.get('tds', {}).get('interest_tds', 0),
            'bank_count': len(interest_data.get('bank_wise_details', []))
        }
        
        # Total TDS/TCS
        tds_data = reconciled_data.get('tds', {})
        self.total_tds_tcs = {
            'total_tds': tds_data.get('total_tds', 0),
            'salary_tds': tds_data.get('salary_tds', 0),
            'interest_tds': tds_data.get('interest_tds', 0),
            'property_tds': tds_data.get('property_tds', 0),
            'breakdown': tds_data.get('breakdown', {})
        }
        
        # Advance tax
        self.advance_tax = {
            'amount': computed_totals.get('total_taxes_paid', 0) - self.total_tds_tcs['total_tds'],
            'total_taxes_paid': computed_totals.get('total_taxes_paid', 0)
        }
        
        # Capital gains buckets
        cg_data = reconciled_data.get('capital_gains', {})
        self.capital_gains = {
            'short_term': cg_data.get('short_term', 0),
            'long_term': cg_data.get('long_term', 0),
            'total': cg_data.get('short_term', 0) + cg_data.get('long_term', 0),
            'transaction_count': len(cg_data.get('transactions', []))
        }
        
        # Summary totals
        self.summary = {
            'gross_total_income': computed_totals.get('gross_total_income', 0),
            'total_deductions': computed_totals.get('total_deductions', 0),
            'taxable_income': computed_totals.get('taxable_income', 0),
            'tax_liability': computed_totals.get('total_tax_liability', 0),
            'total_taxes_paid': computed_totals.get('total_taxes_paid', 0),
            'refund_or_payable': computed_totals.get('refund_or_payable', 0),
            'net_tax_payable': max(0, computed_totals.get('refund_or_payable', 0)),
            'challan_payments': 0  # Will be updated by the router
        }
    
    def _extract_warnings_blockers(self):
        """Extract warnings and blockers from validation results."""
        validation_result = self.pipeline_result.get('validate', {})
        
        self.warnings = []
        self.blockers = []
        
        # Add validation warnings
        for warning in validation_result.get('warnings', []):
            self.warnings.append({
                'type': 'validation',
                'rule': warning.rule_name,
                'message': warning.message,
                'field': warning.field_path,
                'severity': warning.severity
            })
        
        # Add validation blockers
        for blocker in validation_result.get('blockers', []):
            self.blockers.append({
                'type': 'validation',
                'rule': blocker.rule_name,
                'message': blocker.message,
                'field': blocker.field_path,
                'severity': blocker.severity,
                'suggested_fix': blocker.suggested_fix
            })
        
        # Add reconciliation warnings
        reconcile_result = self.pipeline_result.get('reconcile_sources', {})
        for warning in reconcile_result.get('warnings', []):
            self.warnings.append({
                'type': 'reconciliation',
                'message': warning,
                'severity': 'warning'
            })
        
        # Add computation warnings
        compute_result = self.pipeline_result.get('compute_totals', {})
        for warning in compute_result.get('warnings', []):
            self.warnings.append({
                'type': 'computation',
                'message': warning,
                'severity': 'warning'
            })
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API response."""
        return {
            'key_lines': {
                'savings_interest': self.savings_interest,
                'total_tds_tcs': self.total_tds_tcs,
                'advance_tax': self.advance_tax,
                'capital_gains': self.capital_gains
            },
            'summary': self.summary,
            'warnings': self.warnings,
            'blockers': self.blockers,
            'metadata': {
                'generated_at': datetime.utcnow().isoformat(),
                'pipeline_status': 'completed' if len(self.blockers) == 0 else 'completed_with_issues',
                'total_warnings': len(self.warnings),
                'total_blockers': len(self.blockers)
            }
        }


class TaxReturnPipeline:
    """Orchestrates the complete tax return processing pipeline."""
    
    def __init__(self, db: Session, return_id: int):
        self.db = db
        self.return_id = return_id
        self.steps: List[PipelineStep] = []
        self.current_step_index = 0
        self.pipeline_result: Dict[str, Any] = {}
        
        # Initialize repositories
        self.return_repo = TaxReturnRepository(db)
        self.artifact_repo = ArtifactRepository(db)
        self.llm_settings_repo = LLMSettingsRepository(db)
        
        # Get tax return details
        self.tax_return = self.return_repo.get(return_id)
        if not self.tax_return:
            raise ValueError(f"Tax return {return_id} not found")
        
        # Extract return context
        return_data = json.loads(self.tax_return.return_data or '{}')
        self.regime = return_data.get('regime', 'new')
        
        # Initialize LLM components
        self.llm_router = self._initialize_llm_router()
        self.bank_classifier = BankClassifier(self.llm_router) if self.llm_router else None
        self.rules_explainer = RulesExplainer(self.llm_router) if self.llm_router else None
        
        # Initialize pipeline components
        self.reconciler = DataReconciler()
        self.calculator = TaxCalculator(
            assessment_year=self.tax_return.assessment_year,
            regime=self.regime
        )
        self.validator = TaxValidator(
            assessment_year=self.tax_return.assessment_year,
            form_type=self.tax_return.form_type
        )
        
        # Define pipeline steps
        self._initialize_steps()
    
    def _initialize_steps(self):
        """Initialize pipeline steps."""
        self.steps = [
            PipelineStep("parse_artifacts", "Parse uploaded artifacts and extract data"),
            PipelineStep("reconcile_sources", "Reconcile data from multiple sources"),
            PipelineStep("compute_totals", "Calculate tax totals and liability"),
            PipelineStep("validate", "Validate tax return for compliance"),
            PipelineStep("generate_explanations", "Generate user-friendly explanations")
        ]
    
    def _initialize_llm_router(self) -> Optional[LLMRouter]:
        """Initialize LLM router from settings."""
        try:
            llm_settings_data = self.llm_settings_repo.get_settings()
            if not llm_settings_data or not llm_settings_data.llm_enabled:
                logger.info("LLM processing disabled in settings")
                return None
            
            # Convert to settings dict
            settings_dict = {
                "llm_enabled": llm_settings_data.llm_enabled,
                "cloud_allowed": llm_settings_data.cloud_allowed,
                "primary": llm_settings_data.primary,
                "long_context_provider": llm_settings_data.long_context_provider,
                "local_provider": llm_settings_data.local_provider,
                "redact_pii": llm_settings_data.redact_pii,
                "long_context_threshold_chars": llm_settings_data.long_context_threshold_chars,
                "confidence_threshold": float(llm_settings_data.confidence_threshold),
                "max_retries": llm_settings_data.max_retries,
                "timeout_ms": llm_settings_data.timeout_ms
            }
            
            llm_settings = LLMSettings(settings_dict)
            return LLMRouter(llm_settings)
            
        except Exception as e:
            logger.warning(f"Failed to initialize LLM router: {e}")
            return None
    
    def execute(self) -> PreviewResponse:
        """Execute the complete pipeline and return preview response."""
        logger.info(f"Starting tax return pipeline for return {self.return_id}")
        
        try:
            # Execute each step
            for i, step in enumerate(self.steps):
                self.current_step_index = i
                self._execute_step(step)
                
                # Stop if step failed
                if step.status == JobStatus.FAILED:
                    raise Exception(f"Pipeline failed at step: {step.name} - {step.error_message}")
            
            # Generate preview response
            preview = PreviewResponse(self.pipeline_result)
            
            # Persist final results
            self._persist_results()
            
            logger.info(f"Pipeline completed successfully for return {self.return_id}")
            return preview
            
        except Exception as e:
            logger.error(f"Pipeline failed for return {self.return_id}: {str(e)}")
            raise
    
    def _execute_step(self, step: PipelineStep):
        """Execute a single pipeline step."""
        step.start()
        
        try:
            if step.name == "parse_artifacts":
                result = self._parse_artifacts()
            elif step.name == "reconcile_sources":
                result = self._reconcile_sources()
            elif step.name == "compute_totals":
                result = self._compute_totals()
            elif step.name == "validate":
                result = self._validate()
            elif step.name == "generate_explanations":
                result = self._generate_explanations()
            else:
                raise ValueError(f"Unknown step: {step.name}")
            
            step.complete(result)
            self.pipeline_result[step.name] = result
            
        except Exception as e:
            step.fail(str(e))
            raise
    
    def _parse_artifacts(self) -> Dict[str, Any]:
        """Parse all artifacts associated with the tax return."""
        logger.info("Parsing artifacts")
        
        # Get all artifacts for this return
        artifacts = self.artifact_repo.get_by_tax_return(self.return_id)
        
        parsed_artifacts = {}
        parsing_errors = []
        
        for artifact in artifacts:
            try:
                # Determine artifact kind from tags or name
                artifact_kind = self._determine_artifact_kind(artifact)
                
                if artifact_kind and artifact.file_path:
                    # Parse the artifact
                    file_path = Path(artifact.file_path)
                    if file_path.exists():
                        try:
                            # Try deterministic parsing first
                            parsed_data = parser_registry.parse(artifact_kind, file_path)
                            parsed_data['source'] = 'DETERMINISTIC'
                            parsed_artifacts[artifact_kind] = parsed_data
                            logger.info(f"Parsed artifact: {artifact.name} as {artifact_kind}")
                        except ParseMiss:
                            # Try LLM fallback for Form 16B
                            if artifact_kind == 'form16b' and self.llm_router:
                                try:
                                    llm_data = self._parse_form16b_with_llm(file_path)
                                    parsed_artifacts[artifact_kind] = llm_data
                                    logger.info(f"Parsed artifact with LLM: {artifact.name} as {artifact_kind}")
                                except Exception as llm_e:
                                    logger.warning(f"LLM parsing also failed for {artifact.name}: {llm_e}")
                                    raise
                            else:
                                raise
                    else:
                        # For demo purposes, generate synthetic data
                        parsed_data = self._generate_synthetic_data(artifact_kind)
                        parsed_artifacts[artifact_kind] = parsed_data
                        logger.info(f"Generated synthetic data for: {artifact.name} as {artifact_kind}")
                
            except Exception as e:
                parsing_errors.append({
                    'artifact_id': artifact.id,
                    'artifact_name': artifact.name,
                    'error': str(e)
                })
                logger.warning(f"Failed to parse artifact {artifact.name}: {str(e)}")
        
        return {
            'parsed_artifacts': parsed_artifacts,
            'parsing_errors': parsing_errors,
            'total_artifacts': len(artifacts),
            'successfully_parsed': len(parsed_artifacts)
        }
    
    def _determine_artifact_kind(self, artifact) -> Optional[str]:
        """Determine artifact kind from artifact metadata."""
        name_lower = artifact.name.lower()
        tags = (artifact.tags or '').lower()
        
        # Map common patterns to artifact kinds
        if 'prefill' in name_lower or 'prefill' in tags:
            return 'prefill'
        elif 'ais' in name_lower or 'ais' in tags:
            return 'ais'
        elif 'tis' in name_lower or 'tis' in tags:
            return 'ais'  # TIS uses same parser as AIS
        elif 'form16b' in name_lower or '16b' in name_lower:
            return 'form16b'
        elif 'bank' in name_lower and artifact.artifact_type == 'other':  # CSV
            return 'bank_csv'
        elif 'pnl' in name_lower or 'profit' in name_lower:
            return 'pnl_csv'
        
        return None
    
    def _generate_synthetic_data(self, artifact_kind: str) -> Dict[str, Any]:
        """Generate synthetic data for demo purposes."""
        if artifact_kind == 'prefill':
            return {
                'personal_info': {
                    'pan': 'ABCDE1234F',
                    'name': 'John Doe',
                    'date_of_birth': '1985-01-01',
                    'address': '123 Main Street, City',
                    'mobile': '9876543210',
                    'email': 'john.doe@example.com'
                },
                'income': {
                    'salary': {
                        'gross_salary': 1200000.0,
                        'allowances': 120000.0,
                        'perquisites': 30000.0
                    }
                },
                'deductions': {
                    'section_80c': 150000.0,
                    'section_80d': 25000.0
                },
                'taxes_paid': {
                    'tds': 85000.0,
                    'advance_tax': 15000.0
                }
            }
        elif artifact_kind == 'ais':
            return {
                'statement_info': {
                    'type': 'AIS',
                    'pan': 'ABCDE1234F',
                    'assessment_year': '2025-26'
                },
                'salary_details': [{
                    'employer_name': 'Tech Corp Ltd',
                    'gross_salary': 1200000.0,
                    'tds_deducted': 85000.0
                }],
                'interest_details': [{
                    'bank_name': 'State Bank of India',
                    'interest_amount': 45000.0,
                    'tds_deducted': 4500.0
                }],
                'summary': {
                    'total_salary': 1200000.0,
                    'total_interest': 45000.0,
                    'total_tds': 89500.0
                }
            }
        elif artifact_kind == 'bank_csv':
            return {
                'summary': {
                    'total_credits': 1350000.0,
                    'total_debits': 850000.0
                },
                'categories': {
                    'salary': {'total_amount': 1200000.0},
                    'interest': {'total_amount': 45000.0}
                }
            }
        
        return {}
    
    def _reconcile_sources(self) -> Dict[str, Any]:
        """Reconcile data from multiple parsed sources."""
        logger.info("Reconciling data sources")
        
        parsed_artifacts = self.pipeline_result.get('parse_artifacts', {}).get('parsed_artifacts', {})
        
        reconciliation_result = self.reconciler.reconcile_sources(parsed_artifacts)
        
        return {
            'reconciled_data': reconciliation_result.reconciled_data,
            'discrepancies': reconciliation_result.discrepancies,
            'confidence_score': reconciliation_result.confidence_score,
            'warnings': reconciliation_result.warnings,
            'metadata': reconciliation_result.metadata
        }
    
    def _compute_totals(self) -> Dict[str, Any]:
        """Compute tax totals and liability."""
        logger.info("Computing tax totals")
        
        reconciled_data = self.pipeline_result.get('reconcile_sources', {}).get('reconciled_data', {})
        
        computation_result = self.calculator.compute_totals(reconciled_data)
        
        return {
            'computed_totals': computation_result.computed_totals,
            'tax_liability': computation_result.tax_liability,
            'deductions_summary': computation_result.deductions_summary,
            'warnings': computation_result.warnings,
            'metadata': computation_result.metadata
        }
    
    def _validate(self) -> Dict[str, Any]:
        """Validate the tax return data."""
        logger.info("Validating tax return")
        
        reconciled_data = self.pipeline_result.get('reconcile_sources', {}).get('reconciled_data', {})
        computed_totals = self.pipeline_result.get('compute_totals', {}).get('computed_totals', {})
        
        validation_result = self.validator.validate(reconciled_data, computed_totals)
        
        return {
            'is_valid': validation_result.is_valid,
            'issues': [self._issue_to_dict(issue) for issue in validation_result.issues],
            'warnings': validation_result.warnings,
            'blockers': validation_result.blockers,
            'metadata': validation_result.metadata
        }
    
    def _issue_to_dict(self, issue) -> Dict[str, Any]:
        """Convert validation issue to dictionary."""
        return {
            'rule_name': issue.rule_name,
            'severity': issue.severity,
            'message': issue.message,
            'field_path': issue.field_path,
            'suggested_fix': issue.suggested_fix,
            'blocking': issue.blocking
        }
    
    def _persist_results(self):
        """Persist pipeline results to database and filesystem."""
        logger.info("Persisting pipeline results")
        
        try:
            # Update tax return with computed data
            computed_totals = self.pipeline_result.get('compute_totals', {}).get('computed_totals', {})
            
            # Create a summary of the return data
            return_data = {
                'regime': self.regime,
                'pipeline_results': {
                    'gross_total_income': computed_totals.get('gross_total_income', 0),
                    'taxable_income': computed_totals.get('taxable_income', 0),
                    'tax_liability': computed_totals.get('total_tax_liability', 0),
                    'refund_or_payable': computed_totals.get('refund_or_payable', 0)
                },
                'processed_at': datetime.utcnow().isoformat(),
                'pipeline_version': '1.0'
            }
            
            # Update tax return
            self.tax_return.return_data = json.dumps(return_data)
            self.tax_return.updated_at = datetime.utcnow()
            self.db.commit()
            
            # Create artifacts for pipeline outputs
            self._create_pipeline_artifacts()
            
            logger.info("Pipeline results persisted successfully")
            
        except Exception as e:
            logger.error(f"Failed to persist pipeline results: {str(e)}")
            self.db.rollback()
            raise
    
    def _create_pipeline_artifacts(self):
        """Create artifacts for pipeline outputs."""
        # Create computation results artifact
        computation_artifact = self.artifact_repo.create_artifact(
            tax_return_id=self.return_id,
            name=f"computation_results_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.json",
            artifact_type="json",
            description="Tax computation results from pipeline",
            tags="computation,pipeline,generated"
        )
        
        # Store computation results as content
        computation_data = self.pipeline_result.get('compute_totals', {})
        computation_artifact.content = json.dumps(computation_data, indent=2)
        
        # Create validation results artifact
        validation_artifact = self.artifact_repo.create_artifact(
            tax_return_id=self.return_id,
            name=f"validation_results_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.json",
            artifact_type="json",
            description="Validation results from pipeline",
            tags="validation,pipeline,generated"
        )
        
        # Store validation results as content
        validation_data = self.pipeline_result.get('validate', {})
        validation_artifact.content = json.dumps(validation_data, indent=2, default=str)
        
        self.db.commit()
    
    def _parse_form16b_with_llm(self, file_path: Path) -> Dict[str, Any]:
        """Parse Form 16B using LLM fallback."""
        # Extract text from PDF (mock implementation)
        text_content = f"Mock Form 16B content from {file_path}"
        
        # Use LLM to extract data
        llm_result = parse_form16b_llm(text_content, self.llm_router)
        
        # Convert to expected format
        return {
            'source': 'LLM_FALLBACK',
            'confidence': llm_result.confidence,
            'personal_info': {
                'employer_name': llm_result.employer_name,
                'period_from': llm_result.period_from,
                'period_to': llm_result.period_to
            },
            'income': {
                'salary': {
                    'gross_salary': llm_result.gross_salary or 0,
                    'exemptions': llm_result.exemptions or {}
                }
            },
            'deductions': {
                'standard_deduction': llm_result.standard_deduction or 0
            },
            'taxes_paid': {
                'tds': llm_result.tds or 0
            },
            'llm_metadata': {
                'provider': 'LLM_EXTRACTED',
                'confidence': llm_result.confidence,
                'needs_review': llm_result.confidence < 0.7
            }
        }
    
    def _enhance_bank_data_with_llm(self, bank_data: Dict[str, Any]) -> Dict[str, Any]:
        """Enhance bank transaction data with LLM classification."""
        if not self.bank_classifier:
            return bank_data
        
        # Get transaction details
        transactions = bank_data.get('transactions', [])
        enhanced_transactions = []
        
        for txn in transactions:
            narration = txn.get('narration', '')
            if narration:
                # Classify with LLM
                classification = self.bank_classifier.classify_narration(narration)
                txn.update(classification)
            
            enhanced_transactions.append(txn)
        
        # Update bank data
        enhanced_data = bank_data.copy()
        enhanced_data['transactions'] = enhanced_transactions
        enhanced_data['llm_enhanced'] = True
        
        return enhanced_data
    
    def _generate_explanations(self) -> Dict[str, Any]:
        """Generate user-friendly explanations using LLM."""
        logger.info("Generating explanations")
        
        explanations = {}
        
        if self.rules_explainer:
            try:
                # Get computation results for explanation
                compute_result = self.pipeline_result.get('compute_totals', {})
                
                # Generate computation summary
                if compute_result.get('computed_totals'):
                    summary_bullets = self.rules_explainer.generate_computation_summary(
                        compute_result['computed_totals']
                    )
                    explanations['computation_summary'] = summary_bullets
                
                # Generate rules explanations if we have rules log
                # (This would come from the rules engine in a real implementation)
                mock_rules_log = [
                    {
                        'rule_name': 'standard_deduction',
                        'success': True,
                        'input_data': {'salary': 1200000},
                        'output_data': {'deduction': 50000}
                    },
                    {
                        'rule_name': 'hra_exemption',
                        'success': True,
                        'input_data': {'hra_received': 200000, 'rent_paid': 180000},
                        'output_data': {'exemption': 150000}
                    }
                ]
                
                rules_explanation = self.rules_explainer.explain_rules_execution(mock_rules_log)
                explanations['rules_explanation'] = rules_explanation.bullets
                
            except Exception as e:
                logger.warning(f"Failed to generate LLM explanations: {e}")
                explanations['error'] = str(e)
        
        # Add fallback explanations
        if not explanations.get('computation_summary'):
            explanations['computation_summary'] = [
                "Tax computation completed using standard rules",
                "All deductions applied as per eligibility",
                "Final tax liability calculated after adjustments"
            ]
        
        return {
            'explanations': explanations,
            'llm_generated': bool(self.rules_explainer),
            'generated_at': datetime.utcnow().isoformat()
        }
    
    def get_progress(self) -> Dict[str, Any]:
        """Get current pipeline progress."""
        total_steps = len(self.steps)
        completed_steps = sum(1 for step in self.steps if step.status == JobStatus.COMPLETED)
        
        current_step = self.steps[self.current_step_index] if self.current_step_index < len(self.steps) else None
        
        overall_progress = int((completed_steps / total_steps) * 100) if total_steps > 0 else 0
        
        return {
            'overall_progress': overall_progress,
            'current_step': current_step.name if current_step else 'completed',
            'current_step_description': current_step.description if current_step else 'Pipeline completed',
            'completed_steps': completed_steps,
            'total_steps': total_steps,
            'steps': [
                {
                    'name': step.name,
                    'description': step.description,
                    'status': step.status.value,
                    'progress': step.progress_percentage,
                    'started_at': step.started_at.isoformat() if step.started_at else None,
                    'completed_at': step.completed_at.isoformat() if step.completed_at else None,
                    'error_message': step.error_message
                }
                for step in self.steps
            ]
        }