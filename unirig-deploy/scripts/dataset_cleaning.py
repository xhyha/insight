#!/usr/bin/env python3
"""
UniRig Dataset Cleaning Script
Phase 4.2: M2.2 - Data Cleaning

This script validates and cleans 3D character datasets.
"""

import os
import sys
import json
import time
import argparse
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Tuple
from enum import Enum

class ValidationStatus(Enum):
    VALID = "valid"
    INVALID_FORMAT = "invalid_format"
    CORRUPTED = "corrupted"
    LOW_QUALITY = "low_quality"
    MISSING_TEXTURE = "missing_texture"
    INVALID_TOPOLOGY = "invalid_topology"

@dataclass
class ValidationResult:
    """Validation result for a character"""
    character_id: str
    status: ValidationStatus
    message: str
    issues: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    fixes_applied: List[str] = field(default_factory=list)

@dataclass
class CleaningStats:
    """Cleaning statistics"""
    total_checked: int = 0
    valid: int = 0
    invalid: int = 0
    fixed: int = 0
    by_issue: Dict[str, int] = field(default_factory=dict)

class DatasetCleaner:
    """Clean and validate 3D character datasets"""
    
    def __init__(self, dataset_dir: str):
        self.dataset_dir = dataset_dir
        self.results: List[ValidationResult] = []
        
    def validate_file_format(self, file_path: str) -> Tuple[bool, str]:
        """Validate file format"""
        if not os.path.exists(file_path):
            return False, "File not found"
        
        ext = os.path.splitext(file_path)[1].lower()
        supported_formats = ['.glb', '.gltf', '.fbx', '.obj']
        
        if ext not in supported_formats:
            return False, f"Unsupported format: {ext}. Supported: {supported_formats}"
        
        # Check file size
        file_size_mb = os.path.getsize(file_path) / (1024 * 1024)
        if file_size_mb < 0.01:  # Less than 10KB
            return False, "File too small, likely corrupted"
        
        if file_size_mb > 500:  # Larger than 500MB
            return False, "File too large, may cause memory issues"
        
        return True, "Format OK"
    
    def validate_topology(self, file_path: str) -> Tuple[bool, List[str]]:
        """Validate mesh topology"""
        issues = []
        
        # Simulated validation
        # In production, would use trimesh or Open3D to check:
        # - Watertight mesh (no holes)
        # - Manifold edges
        # - No degenerate faces
        
        # For now, simulate some checks
        issues.append("Topology check simulated - requires GPU for full validation")
        
        return len(issues) == 0, issues
    
    def validate_texture(self, file_path: str) -> Tuple[bool, List[str]]:
        """Validate textures"""
        warnings = []
        
        # Check for texture files
        base_path = os.path.splitext(file_path)[0]
        texture_extensions = ['.png', '.jpg', '.jpeg', '.tga', '.bmp']
        
        has_texture = False
        for ext in texture_extensions:
            if os.path.exists(base_path + ext):
                has_texture = True
                break
        
        if not has_texture:
            warnings.append("No texture file found, model may appear untextured")
        
        return True, warnings  # Warning, not error
    
    def check_duplicates(self, file_list: List[str]) -> Dict[str, List[str]]:
        """Check for duplicate files"""
        duplicates = {}
        
        # Simple hash-based duplicate detection would go here
        # For now, return empty
        
        return duplicates
    
    def clean_character(self, character_id: str, file_path: str) -> ValidationResult:
        """Clean and validate a single character"""
        result = ValidationResult(
            character_id=character_id,
            status=ValidationStatus.VALID,
            message="Validation passed"
        )
        
        # Check 1: File format
        valid, msg = self.validate_file_format(file_path)
        if not valid:
            result.status = ValidationStatus.INVALID_FORMAT
            result.message = msg
            result.issues.append(msg)
            return result
        
        # Check 2: Topology
        valid, issues = self.validate_topology(file_path)
        if not valid:
            result.status = ValidationStatus.INVALID_TOPOLOGY
            result.issues.extend(issues)
            result.message = "Topology issues found"
        
        # Check 3: Textures
        _, warnings = self.validate_texture(file_path)
        result.warnings.extend(warnings)
        
        return result
    
    def run_cleaning(self, character_list: List[Dict]) -> List[ValidationResult]:
        """Run cleaning on all characters"""
        print("=" * 60)
        print("Running Dataset Cleaning...")
        print("=" * 60)
        print()
        
        self.results = []
        stats = CleaningStats()
        
        for i, char in enumerate(character_list):
            char_id = char.get('character_id', f'char_{i}')
            file_path = char.get('file_path', '')
            
            print(f"[{i+1}/{len(character_list)}] Validating {char_id}...")
            
            result = self.clean_character(char_id, file_path)
            self.results.append(result)
            
            stats.total_checked += 1
            
            if result.status == ValidationStatus.VALID:
                stats.valid += 1
                print(f"  ✅ {result.message}")
            else:
                stats.invalid += 1
                issue_type = result.status.value
                stats.by_issue[issue_type] = stats.by_issue.get(issue_type, 0) + 1
                print(f"  ❌ {result.message}")
            
            if result.warnings:
                for w in result.warnings:
                    print(f"  ⚠️ {w}")
        
        return self.results
    
    def generate_cleaning_report(self) -> str:
        """Generate cleaning report"""
        stats = CleaningStats()
        
        for r in self.results:
            stats.total_checked += 1
            if r.status == ValidationStatus.VALID:
                stats.valid += 1
            else:
                stats.invalid += 1
                issue_type = r.status.value
                stats.by_issue[issue_type] = stats.by_issue.get(issue_type, 0) + 1
        
        report = {
            "cleaning_stats": {
                "total_checked": stats.total_checked,
                "valid": stats.valid,
                "invalid": stats.invalid,
                "validity_rate": round(stats.valid / stats.total_checked * 100, 2) if stats.total_checked > 0 else 0,
                "by_issue": stats.by_issue
            },
            "results": [
                {
                    "character_id": r.character_id,
                    "status": r.status.value,
                    "message": r.message,
                    "issues": r.issues,
                    "warnings": r.warnings
                }
                for r in self.results
            ]
        }
        
        return json.dumps(report, indent=2)

def main():
    parser = argparse.ArgumentParser(description='UniRig Dataset Cleaning')
    parser.add_argument('--dataset_dir', type=str,
                        default='/home/yang/unirig-deploy/data/characters',
                        help='Dataset directory')
    parser.add_argument('--metadata_file', type=str,
                        default='/home/yang/unirig-deploy/data/metadata/collection_metadata.json',
                        help='Collection metadata file')
    parser.add_argument('--output_report', type=str,
                        default='/home/yang/unirig-deploy/data/metadata/cleaning_report.json',
                        help='Output report path')
    
    args = parser.parse_args()
    
    print("=" * 60)
    print("UniRig Dataset Cleaning")
    print("Phase 4.2: M2.2 - Data Cleaning")
    print("=" * 60)
    print()
    
    # Load metadata if exists
    characters = []
    if os.path.exists(args.metadata_file):
        with open(args.metadata_file, 'r') as f:
            data = json.load(f)
            characters = data.get('characters', [])
        print(f"Loaded {len(characters)} characters from metadata")
    else:
        print("No metadata file found, using sample test data")
        characters = [
            {"character_id": "TEST_001", "file_path": "/path/to/test.glb"},
            {"character_id": "TEST_002", "file_path": "/path/to/test2.glb"},
        ]
    
    # Run cleaning
    cleaner = DatasetCleaner(args.dataset_dir)
    results = cleaner.run_cleaning(characters)
    
    # Generate report
    print("\n" + "=" * 60)
    print("Cleaning Report")
    print("=" * 60)
    
    report = cleaner.generate_cleaning_report()
    report_data = json.loads(report)
    
    print(f"Total checked: {report_data['cleaning_stats']['total_checked']}")
    print(f"Valid: {report_data['cleaning_stats']['valid']}")
    print(f"Invalid: {report_data['cleaning_stats']['invalid']}")
    print(f"Validity rate: {report_data['cleaning_stats']['validity_rate']}%")
    
    if report_data['cleaning_stats']['by_issue']:
        print("\nIssues breakdown:")
        for issue, count in report_data['cleaning_stats']['by_issue'].items():
            print(f"  - {issue}: {count}")
    
    # Save report
    with open(args.output_report, 'w') as f:
        f.write(report)
    
    print(f"\nReport saved to: {args.output_report}")
    
    print("\n" + "=" * 60)
    print("Cleaning completed. Next step: M2.3 - Data Annotation")
    print("=" * 60)

if __name__ == '__main__':
    main()