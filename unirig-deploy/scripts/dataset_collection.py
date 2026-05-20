#!/usr/bin/env python3
"""
UniRig Dataset Collection Script
Phase 4.2: M2.1 - Data Collection (500+ characters)

This script helps collect and organize 3D character datasets for UniRig training.
"""

import os
import sys
import json
import time
import argparse
import subprocess
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Tuple
from enum import Enum
from pathlib import Path

class CharacterType(Enum):
    HUMANOID_MALE = "humanoid_male"
    HUMANOID_FEMALE = "humanoid_female"
    HUMANOID_OTHER = "humanoid_other"  # non-standard
    QUADRUPED_DOG = "quadruped_dog"
    QUADRUPED_CAT = "quadruped_cat"
    QUADRUPED_HORSE = "quadruped_horse"
    QUADRUPED_OTHER = "quadruped_other"
    BIRD = "bird"
    MONSTER = "monster"
    MECHANICAL = "mechanical"
    OTHER = "other"

class DatasetSource(Enum):
    MIXAMO = "mixamo"
    TURBOSQUID = "turbosquid"
    CGTRADER = "cgtrader"
    HUMANS = "humans"
    SKETCHFAB = "sketchfab"
    CUSTOM = "custom"
    INTERNAL = "internal"

@dataclass
class CharacterInfo:
    """Information about a character"""
    character_id: str
    name: str
    character_type: CharacterType
    source: DatasetSource
    file_path: str
    file_size_mb: float
    vertex_count: int
    face_count: int
    has_texture: bool
    rig_status: str  # "rigged", "unrigged", "partial"
    quality_score: float = 0.0
    metadata: Dict = field(default_factory=dict)

@dataclass
class CollectionStats:
    """Collection statistics"""
    total_characters: int = 0
    by_type: Dict[str, int] = field(default_factory=dict)
    by_source: Dict[str, int] = field(default_factory=dict)
    total_size_gb: float = 0.0
    collection_time_hours: float = 0.0

class DatasetCollector:
    """Collect and organize 3D character datasets"""
    
    def __init__(self, output_dir: str):
        self.output_dir = Path(output_dir)
        self.dataset_dir = self.output_dir / "characters"
        self.metadata_dir = self.output_dir / "metadata"
        
        # Create directories
        self.dataset_dir.mkdir(parents=True, exist_ok=True)
        self.metadata_dir.mkdir(parents=True, exist_ok=True)
        
        # Collection list
        self.characters: List[CharacterInfo] = []
        
    def add_character(
        self,
        character_id: str,
        name: str,
        character_type: CharacterType,
        source: DatasetSource,
        file_path: str,
        rig_status: str = "unrigged"
    ) -> CharacterInfo:
        """Add a character to the collection"""
        # Get file size
        file_size_mb = os.path.getsize(file_path) / (1024 * 1024) if os.path.exists(file_path) else 0
        
        info = CharacterInfo(
            character_id=character_id,
            name=name,
            character_type=character_type,
            source=source,
            file_path=file_path,
            file_size_mb=file_size_mb,
            vertex_count=0,  # Would need to load mesh to get this
            face_count=0,
            has_texture=True,
            rig_status=rig_status,
            quality_score=0.0
        )
        
        self.characters.append(info)
        return info
    
    def add_public_datasets(self):
        """Add public dataset URLs and references"""
        # Mixamo dataset references
        mixamo_refs = [
            {"name": "Mixamo Characters", "url": "https://www.mixamo.com/categories/characters", "count": 100},
            {"name": "Mixamo Animations", "url": "https://www.mixamo.com/categories/animations", "count": 1000},
        ]
        
        # Sketchfab references
        sketchfab_refs = [
            {"name": "Sketchfab Rigged Characters", "url": "https://sketchfab.com/search?q=rigged+character", "count": 500},
            {"name": "Sketchfab Game Ready", "url": "https://sketchfab.com/search?q=game+ready+character", "count": 200},
        ]
        
        # HUMANS dataset reference
        humans_refs = [
            {"name": "HUMANS Dataset", "url": "https://tagin.github.io/humans/", "count": 1774},
        ]
        
        print("Public dataset references added:")
        print(f"  - Mixamo: {len(mixamo_refs)} datasets")
        print(f"  - Sketchfab: {len(sketchfab_refs)} datasets") 
        print(f"  - HUMANS: {len(humans_refs)} datasets")
    
    def generate_collection_plan(self) -> Dict:
        """Generate a data collection plan"""
        target_counts = {
            CharacterType.HUMANOID_MALE: 100,
            CharacterType.HUMANOID_FEMALE: 100,
            CharacterType.QUADRUPED_DOG: 30,
            CharacterType.QUADRUPED_CAT: 30,
            CharacterType.QUADRUPED_HORSE: 20,
            CharacterType.BIRD: 20,
            CharacterType.MONSTER: 80,
            CharacterType.MECHANICAL: 40,
            CharacterType.OTHER: 80,
        }
        
        return {
            "target_total": 500,
            "distribution": {k.value: v for k, v in target_counts.items()},
            "priority_order": [
                CharacterType.HUMANOID_MALE,
                CharacterType.HUMANOID_FEMALE,
                CharacterType.MONSTER,
                CharacterType.QUADRUPED_DOG,
                CharacterType.QUADRUPED_CAT,
                CharacterType.MECHANICAL,
                CharacterType.OTHER,
            ]
        }
    
    def create_collection_report(self) -> str:
        """Create collection status report"""
        stats = CollectionStats()
        stats.total_characters = len(self.characters)
        
        for char in self.characters:
            type_key = char.character_type.value
            source_key = char.source.value
            stats.by_type[type_key] = stats.by_type.get(type_key, 0) + 1
            stats.by_source[source_key] = stats.by_source.get(source_key, 0) + 1
            stats.total_size_gb += char.file_size_mb / 1024
        
        report = {
            "collection_stats": {
                "total_characters": stats.total_characters,
                "by_type": stats.by_type,
                "by_source": stats.by_source,
                "total_size_gb": round(stats.total_size_gb, 2)
            },
            "target": {
                "total": 500,
                "remaining": 500 - stats.total_characters
            },
            "plan": self.generate_collection_plan()
        }
        
        return json.dumps(report, indent=2)
    
    def save_metadata(self):
        """Save collection metadata to file"""
        metadata_path = self.metadata_dir / "collection_metadata.json"
        
        data = {
            "collection_date": time.strftime("%Y-%m-%d %H:%M:%S"),
            "total_characters": len(self.characters),
            "characters": [
                {
                    "character_id": c.character_id,
                    "name": c.name,
                    "type": c.character_type.value,
                    "source": c.source.value,
                    "file_path": c.file_path,
                    "rig_status": c.rig_status
                }
                for c in self.characters
            ]
        }
        
        with open(metadata_path, 'w') as f:
            json.dump(data, f, indent=2)
        
        print(f"Metadata saved to: {metadata_path}")

def main():
    parser = argparse.ArgumentParser(description='UniRig Dataset Collection')
    parser.add_argument('--output_dir', type=str, 
                        default='/home/yang/unirig-deploy/data',
                        help='Output directory for dataset')
    parser.add_argument('--add_samples', action='store_true',
                        help='Add sample dataset references')
    
    args = parser.parse_args()
    
    print("=" * 60)
    print("UniRig Dataset Collection")
    print("Phase 4.2: M2.1 - Data Collection")
    print("=" * 60)
    print()
    
    collector = DatasetCollector(args.output_dir)
    
    # Add sample entries if requested
    if args.add_samples:
        print("Adding sample dataset references...")
        
        # Sample Mixamo characters
        collector.add_character(
            character_id="MIXAMO_001",
            name="Mixamo Male Warrior",
            character_type=CharacterType.HUMANOID_MALE,
            source=DatasetSource.MIXAMO,
            file_path="/path/to/mixamo_warrior.fbx",
            rig_status="rigged"
        )
        
        collector.add_character(
            character_id="MIXAMO_002",
            name="Mixamo Female Archer",
            character_type=CharacterType.HUMANOID_FEMALE,
            source=DatasetSource.MIXAMO,
            file_path="/path/to/mixamo_archer.fbx",
            rig_status="rigged"
        )
        
        # Sample Sketchfab characters
        collector.add_character(
            character_id="SKETCHFAB_001",
            name="Fantasy Orc",
            character_type=CharacterType.MONSTER,
            source=DatasetSource.SKETCHFAB,
            file_path="/path/to/orc.glb",
            rig_status="unrigged"
        )
        
        # HUMANS dataset reference
        collector.add_character(
            character_id="HUMANS_001",
            name="Human Dataset Sample 1",
            character_type=CharacterType.HUMANOID_MALE,
            source=DatasetSource.HUMANS,
            file_path="/path/to/humans_sample.glb",
            rig_status="rigged"
        )
    
    # Add public dataset references
    print("\nAdding public dataset references...")
    collector.add_public_datasets()
    
    # Generate collection plan
    print("\nGenerating collection plan...")
    plan = collector.generate_collection_plan()
    print(f"Target total: {plan['target_total']} characters")
    print("Distribution:")
    for char_type, count in plan['distribution'].items():
        print(f"  - {char_type}: {count}")
    
    # Save metadata
    collector.save_metadata()
    
    # Generate and print report
    print("\nCollection Status Report:")
    print("-" * 40)
    report = collector.create_collection_report()
    print(report)
    
    print("\n" + "=" * 60)
    print("Collection plan saved. Next step: M2.2 - Data Cleaning")
    print("=" * 60)

if __name__ == '__main__':
    main()