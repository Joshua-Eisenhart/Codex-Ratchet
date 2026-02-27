"""
Autonomous A1: Self-generating strategy from constraint exploration.

This module provides the core mechanism for A1 to operate without
external fuel input by mining the graveyard and applying constraint
ratchet mechanics.
"""

import json
import re
from collections import Counter, defaultdict
from pathlib import Path
from typing import List, Dict, Set, Tuple

# Configuration
MIN_GRAVEYARD_FOR_AUTONOMY = 5
MAX_CANDIDATES = 100
ATTRACTOR_THRESHOLD = 3


class HeatBathMiner:
    """Mine graveyard for potential - what almost worked."""
    
    def __init__(self, state):
        self.state = state
        self.graveyard = state.get('graveyard', {})
        
    def extract_near_misses(self) -> List[Dict]:
        """Extract items that almost worked but had specific flaws."""
        near_misses = []
        
        for gid, entry in self.graveyard.items():
            item_text = entry.get('item_text', '')
            detail = entry.get('detail', '')
            entry_class = entry.get('class', '')
            
            # Try multiple extraction strategies
            objects = self._extract_field(item_text, 'OBJECTS')
            operations = self._extract_field(item_text, 'OPERATIONS')
            probe_term = self._extract_field(item_text, 'PROBE_TERM')
            neg_class = self._extract_field(item_text, 'NEGATIVE_CLASS')
            target_class = self._extract_field(item_text, 'TARGET_CLASS')
            
            # For SIM_SPEC entries, extract from PROBE_TERM
            if entry_class == 'SPEC_HYP' and 'SIM' in gid:
                if probe_term:
                    objects = probe_term
                if neg_class:
                    operations = neg_class
            
            # Build meaningful near-miss
            if objects or operations or probe_term:
                near_misses.append({
                    'id': gid,
                    'detail': detail,
                    'objects': objects or probe_term or '',
                    'operations': operations or neg_class or '',
                    'neg_class': neg_class,
                    'target_class': target_class,
                    'raw': item_text
                })
        
        return near_misses
    
    def _extract_field(self, text: str, field: str) -> str:
        pattern = f'DEF_FIELD\\s+\\S+\\s+CORR\\s+{field}\\s+(.+?)(?:\\n|$)'
        match = re.search(pattern, text)
        return match.group(1).strip() if match else ''


class ConstraintRatchet:
    """Apply constraint ratchet to generate candidate space."""
    
    FINITUDE_TERMS = {'finite', 'discrete', 'bounded', 'dimensional'}
    NONCOMMUTATION_TERMS = {'commutator', 'ordering', 'product', 'operator'}
    
    def __init__(self):
        self.explored = set()
        
    def generate_candidates(self, near_misses: List[Dict], 
                           admitted_terms: Set[str]) -> List[Dict]:
        candidates = []
        
        for nm in near_misses:
            objects = nm.get('objects', '').split()
            operations = nm.get('operations', '').split()
            
            finite_variants = self._apply_finitude(objects)
            ordered_variants = self._apply_noncommutation(objects, operations)
            
            for variant in finite_variants + ordered_variants:
                candidate_id = f"CAND_{variant.upper().replace(' ', '_')[:40]}"
                if candidate_id not in self.explored:
                    self.explored.add(candidate_id)
                    candidates.append({
                        'source': nm['id'],
                        'variant': variant,
                        'candidate_id': candidate_id
                    })
                    
                    if len(candidates) >= MAX_CANDIDATES:
                        return candidates
        
        return candidates
    
    def _apply_finitude(self, objects: List[str]) -> List[str]:
        variants = []
        for obj in objects:
            for fin_term in self.FINITUDE_TERMS:
                variants.append(f"{fin_term}_{obj}")
        return variants[:20]
    
    def _apply_noncommutation(self, objects: List[str], 
                              operations: List[str]) -> List[str]:
        variants = []
        for i, obj1 in enumerate(objects):
            for obj2 in objects[i+1:]:
                variants.append(f"{obj1}_{obj2}_commutator")
                variants.append(f"{obj1}_{obj2}_product")
        return variants[:20]


class AttractorDetector:
    """Detect attractor basins - convergence points."""
    
    def __init__(self):
        self.occurrence_counts = Counter()
        self.source_map = defaultdict(list)
        
    def find_attractors(self, candidates: List[Dict]) -> List[Dict]:
        for cand in candidates:
            variant = cand.get('variant', '')
            root = self._extract_root(variant)
            self.occurrence_counts[root] += 1
            self.source_map[root].append(cand)
        
        attractors = []
        for root, count in self.occurrence_counts.items():
            if count >= ATTRACTOR_THRESHOLD:
                sources = self.source_map[root]
                attractors.append({
                    'root': root,
                    'count': count,
                    'sources': sources,
                    'stability': count / len(candidates)
                })
        
        attractors.sort(key=lambda a: a['stability'], reverse=True)
        return attractors[:20]
    
    def _extract_root(self, variant: str) -> str:
        for suffix in ['_commutator', '_product', '_finite', '_bounded']:
            if variant.endswith(suffix):
                return variant[:-len(suffix)]
        return variant


class AutonomousStrategyGenerator:
    """Generate strategy from attractor basins."""
    
    def __init__(self, state):
        self.state = state
        self.miner = HeatBathMiner(state)
        self.ratchet = ConstraintRatchet()
        self.detector = AttractorDetector()
        
    def can_run_autonomously(self) -> bool:
        graveyard = self.state.get('graveyard', {})
        return len(graveyard) >= MIN_GRAVEYARD_FOR_AUTONOMY
    
    def generate_strategy(self) -> Dict:
        if not self.can_run_autonomously():
            return {
                'autonomous': False,
                'reason': f'Insufficient graveyard'
            }
        
        near_misses = self.miner.extract_near_misses()
        
        if not near_misses:
            return {'autonomous': False, 'reason': 'No near-misses'}
        
        admitted = set(self.state.get('terms', {}).keys())
        candidates = self.ratchet.generate_candidates(near_misses, admitted)
        
        if not candidates:
            return {'autonomous': False, 'reason': 'No candidates'}
        
        attractors = self.detector.find_attractors(candidates)
        
        if not attractors:
            return {'autonomous': False, 'reason': 'No attractors'}
        
        strategy = self._attractors_to_strategy(attractors)
        
        return {
            'autonomous': True,
            'near_misses': len(near_misses),
            'candidates': len(candidates),
            'attractors': len(attractors),
            'strategy': strategy
        }
    
    def _attractors_to_strategy(self, attractors: List[Dict]) -> Dict:
        terms_to_admit = []
        math_defs = []
        
        for attr in attractors:
            root = attr['root']
            
            if len(root) >= 3 and '_' not in root[:5]:
                terms_to_admit.append({
                    'term': root,
                    'source': 'autonomous_attractor',
                    'alternatives': []
                })
            else:
                math_defs.append({
                    'id': f"S_AUTO_{root[:20].upper()}",
                    'objects': root.replace('_', ' ')[:60],
                    'alternatives': []
                })
        
        return {
            'terms_to_admit': terms_to_admit[:30],
            'compounds_to_try': [],
            'math_defs': math_defs[:30],
            '_autonomous_meta': {
                'attractor_count': len(attractors),
                'generation_method': 'constraint_ratchet_attractor_detection'
            }
        }


def run_autonomous_a1(state_dict: Dict) -> Dict:
    """Main entry point for autonomous A1."""
    generator = AutonomousStrategyGenerator(state_dict)
    return generator.generate_strategy()
