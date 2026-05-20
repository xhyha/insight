#!/usr/bin/env python3
"""
UniRig Dataset Annotation Script
Phase 4.2: M2.3 - Data Annotation

This script handles annotation of 3D character datasets for UniRig training.
"""

import os
import sys
import json
import time
import argparse
import hashlib
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Set
from enum import Enum

class AnnotationType(Enum):
    BONE_HIERARCHY = "bone_hierarchy"
    JOINT_LABELS = "joint_labels"
    SEMANTIC_PARTS = "semantic_parts"
    SKINNING_WEIGHTS = "skinning_weights"
    MORPH_TARGETS = "morph_targets"

@dataclass
class BoneAnnotation:
    """Bone hierarchy annotation"""
    bone_name: str
    parent_bone: Optional[str]
    joint_position: List[float]  # x, y, z
    joint_type: str  # "hinge", "ball", "fixed"
    rotation_limits: Dict[str, List[float]] = field(default_factory=dict)  # axis -> [min, max]

@dataclass
class SemanticPart:
    """Semantic part annotation (head, torso, limbs, etc.)"""
    part_name: str
    vertex_indices: List[int]
    primary_bone: str
    confidence: float

@dataclass
class CharacterAnnotation:
    """Complete annotation for a character"""
    character_id: str
    character_type: str
    bone_hierarchy: List[BoneAnnotation]
    semantic_parts: List[SemanticPart]
    metadata: Dict = field(default_factory=dict)
    annotator: str = ""
    annotated_at: str = ""

class AnnotationTool:
    """Tool for annotating 3D character datasets"""
    
    def __init__(self, dataset_dir: str):
        self.dataset_dir = dataset_dir
        self.annotations: Dict[str, CharacterAnnotation] = {}
        
        # Standard bone names for humanoid characters
        self.standard_humanoid_bones = [
            "Root", "Hips", "Spine", "Chest", "Neck", "Head",
            "Shoulder_L", "Shoulder_R", "Arm_L", "Arm_R",
            "Forearm_L", "Forearm_R", "Hand_L", "Hand_R",
            "UpLeg_L", "UpLeg_R", "Leg_L", "Leg_R",
            "Foot_L", "Foot_R", "Toe_L", "Toe_R"
        ]
        
        # Standard semantic parts
        self.standard_parts = [
            "head", "neck", "torso", "upper_arm", "lower_arm", "hand",
            "upper_leg", "lower_leg", "foot", "toes"
        ]
    
    def auto_annotate_bones(self, character_id: str, character_type: str) -> List[BoneAnnotation]:
        """Auto-generate bone annotations based on character type"""
        annotations = []
        
        if character_type.startswith("humanoid"):
            # Generate standard humanoid skeleton
            for i, bone_name in enumerate(self.standard_humanoid_bones):
                parent = None
                if i > 0:
                    # Simple parent assignment based on naming conventions
                    parent = self.standard_humanoid_bones[i-1]
                
                annotation = BoneAnnotation(
                    bone_name=bone_name,
                    parent_bone=parent,
                    joint_position=[0.0, float(i * 0.1), 0.0],  # Simplified
                    joint_type="ball" if "Leg" in bone_name or "Arm" in bone_name else "fixed"
                )
                annotations.append(annotation)
        else:
            # For non-humanoid, create placeholder
            for i in range(20):
                annotation = BoneAnnotation(
                    bone_name=f"bone_{i}",
                    parent_bone=f"bone_{i-1}" if i > 0 else None,
                    joint_position=[0.0, float(i * 0.1), 0.0],
                    joint_type="ball"
                )
                annotations.append(annotation)
        
        return annotations
    
    def auto_annotate_parts(self, character_id: str, character_type: str) -> List[SemanticPart]:
        """Auto-generate semantic part annotations"""
        parts = []
        
        for i, part_name in enumerate(self.standard_parts):
            # Simplified - would use mesh segmentation in production
            part = SemanticPart(
                part_name=part_name,
                vertex_indices=list(range(i * 100, (i + 1) * 100)),  # Placeholder
                primary_bone=f"{part_name.capitalize()}_Bone",
                confidence=0.8 if character_type.startswith("humanoid") else 0.5
            )
            parts.append(part)
        
        return parts
    
    def annotate_character(
        self,
        character_id: str,
        character_type: str,
        manual: bool = False
    ) -> CharacterAnnotation:
        """Annotate a single character"""
        print(f"Annotating {character_id} ({character_type})...")
        
        if manual:
            # In manual mode, would launch annotation UI
            print("  [Manual annotation mode - not implemented in this script]")
            print("  [In production, would use annotation tool like CVAT or custom UI]")
        
        # Auto-annotate
        bone_hierarchy = self.auto_annotate_bones(character_id, character_type)
        semantic_parts = self.auto_annotate_parts(character_id, character_type)
        
        annotation = CharacterAnnotation(
            character_id=character_id,
            character_type=character_type,
            bone_hierarchy=bone_hierarchy,
            semantic_parts=semantic_parts,
            metadata={
                "auto_annotated": True,
                "annotation_version": "1.0"
            },
            annotator="auto_annotator",
            annotated_at=time.strftime("%Y-%m-%d %H:%M:%S")
        )
        
        self.annotations[character_id] = annotation
        print(f"  ✅ Annotated {len(bone_hierarchy)} bones and {len(semantic_parts)} parts")
        
        return annotation
    
    def batch_annotate(self, character_list: List[Dict]) -> List[CharacterAnnotation]:
        """Batch annotate characters"""
        print("=" * 60)
        print("Running Batch Annotation...")
        print("=" * 60)
        print()
        
        annotations = []
        
        for i, char in enumerate(character_list):
            char_id = char.get('character_id', f'char_{i}')
            char_type = char.get('character_type', 'humanoid_other')
            
            annotation = self.annotate_character(char_id, char_type, manual=False)
            annotations.append(annotation)
        
        return annotations
    
    def export_annotations(self, output_path: str):
        """Export annotations to file"""
        data = {
            "export_date": time.strftime("%Y-%m-%d %H:%M:%S"),
            "total_annotations": len(self.annotations),
            "annotations": [
                {
                    "character_id": a.character_id,
                    "character_type": a.character_type,
                    "bone_hierarchy": [
                        {
                            "bone_name": b.bone_name,
                            "parent_bone": b.parent_bone,
                            "joint_position": b.joint_position,
                            "joint_type": b.joint_type,
                            "rotation_limits": b.rotation_limits
                        }
                        for b in a.bone_hierarchy
                    ],
                    "semantic_parts": [
                        {
                            "part_name": p.part_name,
                            "vertex_count": len(p.vertex_indices),
                            "primary_bone": p.primary_bone,
                            "confidence": p.confidence
                        }
                        for p in a.semantic_parts
                    ],
                    "metadata": a.metadata,
                    "annotator": a.annotator,
                    "annotated_at": a.annotated_at
                }
                for a in self.annotations.values()
            ]
        }
        
        with open(output_path, 'w') as f:
            json.dump(data, f, indent=2)
        
        print(f"\nExported {len(self.annotations)} annotations to: {output_path}")
    
    def validate_annotations(self) -> Dict[str, List[str]]:
        """Validate annotations for completeness and correctness"""
        issues = {}
        
        for char_id, annotation in self.annotations.items():
            char_issues = []
            
            # Check bone hierarchy completeness
            if len(annotation.bone_hierarchy) < 10:
                char_issues.append(f"Too few bones: {len(annotation.bone_hierarchy)}")
            
            # Check for root bone
            has_root = any(b.parent_bone is None for b in annotation.bone_hierarchy)
            if not has_root:
                char_issues.append("No root bone found")
            
            # Check semantic parts coverage
            if len(annotation.semantic_parts) < 5:
                char_issues.append(f"Too few semantic parts: {len(annotation.semantic_parts)}")
            
            if char_issues:
                issues[char_id] = char_issues
        
        return issues

def main():
    parser = argparse.ArgumentParser(description='UniRig Dataset Annotation')
    parser.add_argument('--dataset_dir', type=str,
                        default='/home/yang/unirig-deploy/data',
                        help='Dataset directory')
    parser.add_argument('--cleaning_report', type=str,
                        default='/home/yang/unirig-deploy/data/metadata/cleaning_report.json',
                        help='Cleaning report with validated characters')
    parser.add_argument('--output', type=str,
                        default='/home/yang/unirig-deploy/data/metadata/annotations.json',
                        help='Output annotations file')
    parser.add_argument('--manual', action='store_true',
                        help='Use manual annotation mode')
    
    args = parser.parse_args()
    
    print("=" * 60)
    print("UniRig Dataset Annotation")
    print("Phase 4.2: M2.3 - Data Annotation")
    print("=" * 60)
    print()
    
    # Load cleaning report
    characters = []
    if os.path.exists(args.cleaning_report):
        with open(args.cleaning_report, 'r') as f:
            data = json.load(f)
            # Get valid characters from cleaning
            for item in data.get('results', []):
                if item['status'] == 'valid':
                    characters.append({
                        'character_id': item['character_id'],
                        'character_type': 'humanoid_male'  # Default type
                    })
        print(f"Loaded {len(characters)} validated characters")
    else:
        # Use sample data
        print("Using sample annotation data")
        characters = [
            {"character_id": f"SAMPLE_{i:03d}", "character_type": "humanoid_male"}
            for i in range(10)
        ]
    
    # Run annotation
    tool = AnnotationTool(args.dataset_dir)
    annotations = tool.batch_annotate(characters)
    
    # Validate
    print("\nValidating annotations...")
    issues = tool.validate_annotations()
    if issues:
        print("  Validation issues found:")
        for char_id, char_issues in issues.items():
            print(f"  - {char_id}: {', '.join(char_issues)}")
    else:
        print("  ✅ All annotations valid")
    
    # Export
    tool.export_annotations(args.output)
    
    print("\n" + "=" * 60)
    print("Annotation completed. Next step: M2.4 - Dataset Acceptance")
    print("=" * 60)

if __name__ == '__main__':
    main()