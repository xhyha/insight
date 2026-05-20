#!/usr/bin/env python3
"""
UniRig Dataset Acceptance Test
Phase 4.2: M2.4 - Dataset Acceptance

This script validates the dataset meets quality standards for UniRig training.
"""

import os
import sys
import json
import time
import argparse
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Tuple
from enum import Enum

class AcceptanceStatus(Enum):
    ACCEPTED = "accepted"
    CONDITIONALLY_ACCEPTED = "conditionally_accepted"
    REJECTED = "rejected"

class QualityLevel(Enum):
    EXCELLENT = "excellent"
    GOOD = "good"
    ACCEPTABLE = "acceptable"
    POOR = "poor"
    UNACCEPTABLE = "unacceptable"

@dataclass
class QualityMetric:
    """Quality metric result"""
    metric_name: str
    value: float
    threshold: float
    status: QualityLevel
    weight: float = 1.0

@dataclass
class DatasetRequirements:
    """Dataset requirements specification"""
    min_total_characters: int = 500
    min_humanoid_ratio: float = 0.5  # At least 50% humanoid
    min_rigged_ratio: float = 0.7  # At least 70% pre-rigged
    max_file_size_mb: float = 500
    min_annotation_completeness: float = 0.95
    min_avg_quality_score: float = 0.8

@dataclass
class AcceptanceReport:
    """Acceptance test report"""
    status: AcceptanceStatus
    quality_level: QualityLevel
    overall_score: float
    metrics: List[QualityMetric]
    issues: List[str] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)

class DatasetAcceptanceTester:
    """Test if dataset meets acceptance criteria"""
    
    def __init__(self, dataset_dir: str, requirements: DatasetRequirements = None):
        self.dataset_dir = dataset_dir
        self.requirements = requirements or DatasetRequirements()
        self.metrics: List[QualityMetric] = []
        self.issues: List[str] = []
        self.recommendations: List[str] = []
    
    def load_dataset_info(self) -> Dict:
        """Load dataset information from metadata files"""
        info = {
            "total_characters": 0,
            "by_type": {},
            "by_source": {},
            "rigged_count": 0,
            "annotated_count": 0,
            "total_size_gb": 0.0,
            "avg_quality_score": 0.0
        }
        
        # Load collection metadata
        collection_file = os.path.join(self.dataset_dir, "metadata", "collection_metadata.json")
        if os.path.exists(collection_file):
            with open(collection_file, 'r') as f:
                data = json.load(f)
                info["total_characters"] = len(data.get("characters", []))
        
        # Load cleaning report
        cleaning_file = os.path.join(self.dataset_dir, "metadata", "cleaning_report.json")
        if os.path.exists(cleaning_file):
            with open(cleaning_file, 'r') as f:
                data = json.load(f)
                stats = data.get("cleaning_stats", {})
                info["valid_count"] = stats.get("valid", 0)
                info["invalid_count"] = stats.get("invalid", 0)
        
        # Load annotations
        annotation_file = os.path.join(self.dataset_dir, "metadata", "annotations.json")
        if os.path.exists(annotation_file):
            with open(annotation_file, 'r') as f:
                data = json.load(f)
                info["annotated_count"] = len(data.get("annotations", []))
        
        return info
    
    def check_total_characters(self, info: Dict) -> QualityMetric:
        """Check if total character count meets minimum"""
        total = info.get("total_characters", 0)
        threshold = self.requirements.min_total_characters
        
        if total >= threshold:
            status = QualityLevel.EXCELLENT if total >= threshold * 1.2 else QualityLevel.GOOD
            self.recommendations.append(f"Character count excellent: {total} >= {threshold}")
        else:
            status = QualityLevel.UNACCEPTABLE if total < threshold * 0.5 else QualityLevel.POOR
            self.issues.append(f"Insufficient characters: {total} < {threshold}")
        
        return QualityMetric(
            metric_name="Total Characters",
            value=total,
            threshold=threshold,
            status=status,
            weight=2.0  # High weight for total count
        )
    
    def check_humanoid_ratio(self, info: Dict) -> QualityMetric:
        """Check humanoid character ratio"""
        by_type = info.get("by_type", {})
        humanoid = by_type.get("humanoid_male", 0) + by_type.get("humanoid_female", 0)
        total = info.get("total_characters", 1)
        ratio = humanoid / total if total > 0 else 0
        
        threshold = self.requirements.min_humanoid_ratio
        
        if ratio >= threshold:
            status = QualityLevel.GOOD
        else:
            status = QualityLevel.POOR
            self.issues.append(f"Low humanoid ratio: {ratio:.1%} < {threshold:.1%}")
        
        return QualityMetric(
            metric_name="Humanoid Ratio",
            value=ratio,
            threshold=threshold,
            status=status,
            weight=1.5
        )
    
    def check_rigged_ratio(self, info: Dict) -> QualityMetric:
        """Check pre-rigged character ratio"""
        rigged = info.get("rigged_count", 0)
        total = info.get("total_characters", 1)
        ratio = rigged / total if total > 0 else 0
        
        threshold = self.requirements.min_rigged_ratio
        
        if ratio >= threshold:
            status = QualityLevel.GOOD
            self.recommendations.append(f"Good pre-rigged ratio: {ratio:.1%}")
        else:
            status = QualityLevel.ACCEPTABLE if ratio >= 0.5 else QualityLevel.POOR
            self.recommendations.append(f"Consider increasing pre-rigged characters for better training")
        
        return QualityMetric(
            metric_name="Pre-rigged Ratio",
            value=ratio,
            threshold=threshold,
            status=status,
            weight=1.5
        )
    
    def check_annotation_completeness(self, info: Dict) -> QualityMetric:
        """Check annotation completeness"""
        annotated = info.get("annotated_count", 0)
        total = info.get("total_characters", 1)
        completeness = annotated / total if total > 0 else 0
        
        threshold = self.requirements.min_annotation_completeness
        
        if completeness >= threshold:
            status = QualityLevel.GOOD
        else:
            status = QualityLevel.POOR
            self.issues.append(f"Incomplete annotations: {completeness:.1%} < {threshold:.1%}")
        
        return QualityMetric(
            metric_name="Annotation Completeness",
            value=completeness,
            threshold=threshold,
            status=status,
            weight=2.0
        )
    
    def check_quality_score(self, info: Dict) -> QualityMetric:
        """Check average quality score"""
        avg_score = info.get("avg_quality_score", 0.0)
        threshold = self.requirements.min_avg_quality_score
        
        if avg_score >= threshold:
            status = QualityLevel.GOOD if avg_score >= 0.9 else QualityLevel.ACCEPTABLE
        else:
            status = QualityLevel.POOR
            self.issues.append(f"Low quality score: {avg_score:.2f} < {threshold:.2f}")
        
        return QualityMetric(
            metric_name="Average Quality Score",
            value=avg_score,
            threshold=threshold,
            status=status,
            weight=2.0
        )
    
    def run_acceptance_test(self) -> AcceptanceReport:
        """Run full acceptance test"""
        print("=" * 60)
        print("Running Dataset Acceptance Test...")
        print("=" * 60)
        print()
        
        # Load dataset info
        print("Loading dataset information...")
        info = self.load_dataset_info()
        print(f"  Total characters: {info.get('total_characters', 0)}")
        print(f"  Valid characters: {info.get('valid_count', 'N/A')}")
        print(f"  Annotated: {info.get('annotated_count', 0)}")
        print()
        
        # Run checks
        print("Running quality checks...")
        self.metrics = [
            self.check_total_characters(info),
            self.check_humanoid_ratio(info),
            self.check_rigged_ratio(info),
            self.check_annotation_completeness(info),
            self.check_quality_score(info),
        ]
        
        # Print results
        print("\nQuality Metrics:")
        for m in self.metrics:
            status_icon = {
                QualityLevel.EXCELLENT: "🌟",
                QualityLevel.GOOD: "✅",
                QualityLevel.ACCEPTABLE: "⚠️",
                QualityLevel.POOR: "❌",
                QualityLevel.UNACCEPTABLE: "🚫"
            }.get(m.status, "?")
            
            value_str = f"{m.value:.2f}" if isinstance(m.value, float) else str(m.value)
            threshold_str = f"{m.threshold:.2f}" if isinstance(m.threshold, float) else str(m.threshold)
            
            print(f"  {status_icon} {m.metric_name}: {value_str} (threshold: {threshold_str})")
        
        # Calculate overall score
        total_weight = sum(m.weight for m in self.metrics)
        weighted_score = sum(
            (1.0 if m.status in [QualityLevel.EXCELLENT, QualityLevel.GOOD] else
             0.5 if m.status == QualityLevel.ACCEPTABLE else 0.0) * m.weight
            for m in self.metrics
        ) / total_weight * 100
        
        # Determine quality level
        if weighted_score >= 90:
            quality_level = QualityLevel.EXCELLENT
        elif weighted_score >= 75:
            quality_level = QualityLevel.GOOD
        elif weighted_score >= 60:
            quality_level = QualityLevel.ACCEPTABLE
        elif weighted_score >= 40:
            quality_level = QualityLevel.POOR
        else:
            quality_level = QualityLevel.UNACCEPTABLE
        
        # Determine acceptance status
        has_critical_issues = any(
            m.status == QualityLevel.UNACCEPTABLE for m in self.metrics
        )
        has_major_issues = any(
            m.status == QualityLevel.POOR for m in self.metrics
        )
        
        if has_critical_issues:
            status = AcceptanceStatus.REJECTED
        elif has_major_issues:
            status = AcceptanceStatus.CONDITIONALLY_ACCEPTED
        else:
            status = AcceptanceStatus.ACCEPTED
        
        # Generate recommendations
        if status == AcceptanceStatus.REJECTED:
            self.recommendations.append("Dataset requires significant improvements before acceptance")
        elif status == AcceptanceStatus.CONDITIONALLY_ACCEPTED:
            self.recommendations.append("Dataset accepted with conditions - address issues in next sprint")
        else:
            self.recommendations.append("Dataset ready for Phase 4.3 model fine-tuning")
        
        return AcceptanceReport(
            status=status,
            quality_level=quality_level,
            overall_score=weighted_score,
            metrics=self.metrics,
            issues=self.issues,
            recommendations=self.recommendations
        )
    
    def generate_report(self, report: AcceptanceReport) -> str:
        """Generate acceptance report"""
        data = {
            "report_date": time.strftime("%Y-%m-%d %H:%M:%S"),
            "status": report.status.value,
            "quality_level": report.quality_level.value,
            "overall_score": round(report.overall_score, 2),
            "metrics": [
                {
                    "metric_name": m.metric_name,
                    "value": m.value,
                    "threshold": m.threshold,
                    "status": m.status.value,
                    "weight": m.weight
                }
                for m in report.metrics
            ],
            "issues": report.issues,
            "recommendations": report.recommendations
        }
        
        return json.dumps(data, indent=2)

def main():
    parser = argparse.ArgumentParser(description='UniRig Dataset Acceptance Test')
    parser.add_argument('--dataset_dir', type=str,
                        default='/home/yang/unirig-deploy/data',
                        help='Dataset directory')
    parser.add_argument('--output', type=str,
                        default='/home/yang/unirig-deploy/data/metadata/acceptance_report.json',
                        help='Output report path')
    parser.add_argument('--min_characters', type=int, default=500,
                        help='Minimum total characters')
    parser.add_argument('--min_rigged_ratio', type=float, default=0.7,
                        help='Minimum pre-rigged ratio')
    
    args = parser.parse_args()
    
    print("=" * 60)
    print("UniRig Dataset Acceptance Test")
    print("Phase 4.2: M2.4 - Dataset Acceptance")
    print("=" * 60)
    print()
    
    # Create requirements
    requirements = DatasetRequirements(
        min_total_characters=args.min_characters,
        min_rigged_ratio=args.min_rigged_ratio
    )
    
    # Run acceptance test
    tester = DatasetAcceptanceTester(args.dataset_dir, requirements)
    report = tester.run_acceptance_test()
    
    # Print summary
    print("\n" + "=" * 60)
    print("ACCEPTANCE RESULT")
    print("=" * 60)
    
    status_icon = {
        AcceptanceStatus.ACCEPTED: "✅",
        AcceptanceStatus.CONDITIONALLY_ACCEPTED: "⚠️",
        AcceptanceStatus.REJECTED: "❌"
    }.get(report.status, "?")
    
    print(f"Status: {status_icon} {report.status.value.upper()}")
    print(f"Quality Level: {report.quality_level.value}")
    print(f"Overall Score: {report.overall_score:.1f}%")
    
    if report.issues:
        print("\nIssues:")
        for issue in report.issues:
            print(f"  - {issue}")
    
    if report.recommendations:
        print("\nRecommendations:")
        for rec in report.recommendations:
            print(f"  - {rec}")
    
    # Save report
    report_json = tester.generate_report(report)
    with open(args.output, 'w') as f:
        f.write(report_json)
    
    print(f"\nReport saved to: {args.output}")
    
    print("\n" + "=" * 60)
    if report.status == AcceptanceStatus.ACCEPTED:
        print("🎉 Dataset accepted! Ready for Phase 4.3: Model Fine-tuning")
    elif report.status == AcceptanceStatus.CONDITIONALLY_ACCEPTED:
        print("⚠️ Dataset conditionally accepted. Please address issues.")
        print("   Then proceed to Phase 4.3 with monitoring.")
    else:
        print("❌ Dataset rejected. Please address critical issues.")
        print("   Re-run acceptance test after fixes.")
    print("=" * 60)
    
    # Return exit code based on status
    return 0 if report.status == AcceptanceStatus.ACCEPTED else 1

if __name__ == '__main__':
    sys.exit(main())