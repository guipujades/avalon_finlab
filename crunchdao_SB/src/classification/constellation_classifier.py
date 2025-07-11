"""
Constellation Classification System for Time Series.

Each time series is represented as a constellation of particles,
where each particle represents a key segment of the series.
The shape formed by these particles and their trajectories
defines the unique signature of the series.

Author: Inspired by particle physics tracking systems (CERN)
        and astronomical classification methods
"""

import numpy as np
from typing import Dict, List, Tuple, Optional, Union
from dataclasses import dataclass
from enum import Enum
import pandas as pd


class SegmentType(Enum):
    """Types of segments in a time series."""
    INITIAL = "initial"
    PRE_BOUNDARY_FAR = "pre_boundary_far"
    PRE_BOUNDARY_NEAR = "pre_boundary_near"
    POST_BOUNDARY_NEAR = "post_boundary_near"
    POST_BOUNDARY_FAR = "post_boundary_far"
    FINAL = "final"
    TRANSITION = "transition"


@dataclass
class SegmentParticle:
    """
    Represents a segment of time series as a particle.
    
    Each particle tracks its own trajectory through classification space.
    """
    segment_type: SegmentType
    position: np.ndarray
    velocity: np.ndarray
    segment_data: np.ndarray
    time_range: Tuple[int, int]
    trajectory: List[np.ndarray]
    forces_applied: List[Dict]
    
    def __post_init__(self):
        """Initialize trajectory with starting position."""
        self.trajectory = [self.position.copy()]
        self.forces_applied = []
    
    def apply_force(self, force_vector: np.ndarray, force_name: str, 
                   damping: float = 0.85):
        """Apply force and update position."""
        self.velocity = damping * self.velocity + force_vector
        self.position += self.velocity
        
        self.trajectory.append(self.position.copy())
        self.forces_applied.append({
            'name': force_name,
            'vector': force_vector.copy(),
            'magnitude': np.linalg.norm(force_vector)
        })
    
    def get_displacement(self) -> float:
        """Total displacement from origin."""
        return np.linalg.norm(self.position)
    
    def get_trajectory_length(self) -> float:
        """Total path length traveled."""
        if len(self.trajectory) < 2:
            return 0.0
        
        total_length = 0
        for i in range(1, len(self.trajectory)):
            total_length += np.linalg.norm(
                self.trajectory[i] - self.trajectory[i-1]
            )
        return total_length
    
    def get_trajectory_curvature(self) -> float:
        """Measure how curved the path is."""
        if len(self.trajectory) < 3:
            return 0.0
        
        direct_distance = np.linalg.norm(
            self.trajectory[-1] - self.trajectory[0]
        )
        path_length = self.get_trajectory_length()
        
        if path_length == 0:
            return 0.0
        
        return (path_length - direct_distance) / path_length


class ConstellationClassifier:
    """
    Classifies time series by creating a constellation of particles.
    """
    
    def __init__(self, n_dimensions: int = 12):
        """
        Initialize classifier.
        
        Parameters
        ----------
        n_dimensions : int
            Number of dimensions in classification space
        """
        self.n_dimensions = n_dimensions
        self.segment_extractors = {
            SegmentType.INITIAL: self._extract_initial,
            SegmentType.PRE_BOUNDARY_FAR: self._extract_pre_far,
            SegmentType.PRE_BOUNDARY_NEAR: self._extract_pre_near,
            SegmentType.POST_BOUNDARY_NEAR: self._extract_post_near,
            SegmentType.POST_BOUNDARY_FAR: self._extract_post_far,
            SegmentType.FINAL: self._extract_final,
            SegmentType.TRANSITION: self._extract_transition
        }
    
    def _extract_initial(self, before: np.ndarray, after: np.ndarray) -> np.ndarray:
        """Extract initial segment of series."""
        n_points = min(20, len(before) // 10)
        return before[:n_points]
    
    def _extract_pre_far(self, before: np.ndarray, after: np.ndarray) -> np.ndarray:
        """Extract segment far before boundary."""
        start = len(before) // 4
        end = len(before) // 2
        return before[start:end]
    
    def _extract_pre_near(self, before: np.ndarray, after: np.ndarray) -> np.ndarray:
        """Extract segment near before boundary."""
        n_points = min(30, len(before) // 5)
        return before[-n_points:]
    
    def _extract_post_near(self, before: np.ndarray, after: np.ndarray) -> np.ndarray:
        """Extract segment near after boundary."""
        n_points = min(30, len(after) // 5)
        return after[:n_points]
    
    def _extract_post_far(self, before: np.ndarray, after: np.ndarray) -> np.ndarray:
        """Extract segment far after boundary."""
        start = len(after) // 2
        end = 3 * len(after) // 4
        return after[start:end]
    
    def _extract_final(self, before: np.ndarray, after: np.ndarray) -> np.ndarray:
        """Extract final segment of series."""
        n_points = min(20, len(after) // 10)
        return after[-n_points:]
    
    def _extract_transition(self, before: np.ndarray, after: np.ndarray) -> np.ndarray:
        """Extract transition region around boundary."""
        n_before = min(10, len(before) // 10)
        n_after = min(10, len(after) // 10)
        return np.concatenate([before[-n_before:], after[:n_after]])
    
    def create_constellation(self, before: np.ndarray, 
                           after: np.ndarray) -> Dict[SegmentType, SegmentParticle]:
        """
        Create constellation of particles for the time series.
        
        Parameters
        ----------
        before : np.ndarray
            Values before boundary
        after : np.ndarray
            Values after boundary
            
        Returns
        -------
        Dict[SegmentType, SegmentParticle]
            Constellation of particles
        """
        constellation = {}
        
        for seg_type, extractor in self.segment_extractors.items():
            segment_data = extractor(before, after)
            
            if len(segment_data) > 0:
                particle = SegmentParticle(
                    segment_type=seg_type,
                    position=np.zeros(self.n_dimensions),
                    velocity=np.zeros(self.n_dimensions),
                    segment_data=segment_data,
                    time_range=(0, len(segment_data)),
                    trajectory=[]
                )
                constellation[seg_type] = particle
        
        return constellation
    
    def apply_classification_forces(self, constellation: Dict[SegmentType, SegmentParticle]):
        """
        Apply various classification forces to all particles.
        
        Each force can affect particles differently based on their segment type.
        """
        for seg_type, particle in constellation.items():
            self._apply_statistical_forces(particle, seg_type)
            self._apply_spectral_forces(particle, seg_type)
            self._apply_dynamic_forces(particle, seg_type)
            self._apply_morphological_forces(particle, seg_type)
    
    def _apply_statistical_forces(self, particle: SegmentParticle, 
                                 seg_type: SegmentType):
        """Apply forces based on statistical properties."""
        data = particle.segment_data
        
        mean_val = np.mean(data)
        std_val = np.std(data)
        skew_val = np.mean(((data - mean_val) / (std_val + 1e-8))**3)
        
        force = np.zeros(self.n_dimensions)
        
        force[0] = mean_val / (np.abs(mean_val) + 1)
        force[1] = np.log1p(std_val) / 5
        force[2] = skew_val / 5
        
        if seg_type in [SegmentType.PRE_BOUNDARY_NEAR, SegmentType.POST_BOUNDARY_NEAR]:
            force *= 1.5
        
        particle.apply_force(force, "statistical")
    
    def _apply_spectral_forces(self, particle: SegmentParticle, 
                              seg_type: SegmentType):
        """Apply forces based on frequency domain properties."""
        data = particle.segment_data
        
        if len(data) < 4:
            return
        
        fft_vals = np.abs(np.fft.fft(data))[:len(data)//2]
        
        if len(fft_vals) > 0:
            dominant_freq = np.argmax(fft_vals) / len(fft_vals)
            spectral_entropy = -np.sum(
                fft_vals/np.sum(fft_vals) * np.log(fft_vals/np.sum(fft_vals) + 1e-8)
            )
            
            force = np.zeros(self.n_dimensions)
            force[3] = dominant_freq - 0.5
            force[4] = (spectral_entropy - 1) / 2
            
            if seg_type == SegmentType.TRANSITION:
                force *= 2.0
            
            particle.apply_force(force, "spectral")
    
    def _apply_dynamic_forces(self, particle: SegmentParticle, 
                             seg_type: SegmentType):
        """Apply forces based on dynamic properties."""
        data = particle.segment_data
        
        if len(data) < 2:
            return
        
        diff1 = np.diff(data)
        volatility = np.std(diff1)
        
        if len(data) > 2:
            acf1 = np.corrcoef(data[:-1], data[1:])[0, 1]
        else:
            acf1 = 0
        
        force = np.zeros(self.n_dimensions)
        force[5] = volatility / (volatility + 1)
        force[6] = acf1
        
        if seg_type in [SegmentType.INITIAL, SegmentType.FINAL]:
            force *= 0.7
        
        particle.apply_force(force, "dynamic")
    
    def _apply_morphological_forces(self, particle: SegmentParticle, 
                                   seg_type: SegmentType):
        """Apply forces based on shape characteristics."""
        data = particle.segment_data
        
        if len(data) < 5:
            return
        
        t = np.arange(len(data))
        slope, intercept = np.polyfit(t, data, 1)
        detrended = data - (slope * t + intercept)
        
        peaks = len(np.where(np.diff(np.sign(np.diff(data))) < 0)[0])
        roughness = np.mean(np.abs(np.diff(detrended)))
        
        force = np.zeros(self.n_dimensions)
        force[7] = np.tanh(slope * 10)
        force[8] = (peaks / len(data) - 0.1) * 5
        force[9] = roughness / (roughness + 1)
        
        particle.apply_force(force, "morphological")


class ConstellationShape:
    """
    Analyzes the shape formed by a constellation of particles.
    """
    
    def __init__(self, constellation: Dict[SegmentType, SegmentParticle]):
        """Initialize with a constellation."""
        self.constellation = constellation
        self.positions = self._extract_positions()
        self.trajectories = self._extract_trajectories()
    
    def _extract_positions(self) -> Dict[SegmentType, np.ndarray]:
        """Extract final positions of all particles."""
        return {
            seg_type: particle.position.copy()
            for seg_type, particle in self.constellation.items()
        }
    
    def _extract_trajectories(self) -> Dict[SegmentType, List[np.ndarray]]:
        """Extract full trajectories of all particles."""
        return {
            seg_type: particle.trajectory.copy()
            for seg_type, particle in self.constellation.items()
        }
    
    def get_shape_features(self) -> Dict[str, float]:
        """
        Extract features describing the constellation shape.
        
        Returns
        -------
        Dict[str, float]
            Shape features
        """
        features = {}
        
        positions_array = np.array(list(self.positions.values()))
        centroid = np.mean(positions_array, axis=0)
        
        features['centroid_distance'] = np.linalg.norm(centroid)
        
        dispersion = np.mean([
            np.linalg.norm(pos - centroid) 
            for pos in positions_array
        ])
        features['dispersion'] = dispersion
        
        if SegmentType.PRE_BOUNDARY_NEAR in self.positions and \
           SegmentType.POST_BOUNDARY_NEAR in self.positions:
            boundary_shift = np.linalg.norm(
                self.positions[SegmentType.POST_BOUNDARY_NEAR] - 
                self.positions[SegmentType.PRE_BOUNDARY_NEAR]
            )
            features['boundary_shift'] = boundary_shift
        
        coherence_scores = []
        particle_list = list(self.constellation.values())
        for i in range(len(particle_list)):
            for j in range(i+1, len(particle_list)):
                traj1 = np.array(particle_list[i].trajectory)
                traj2 = np.array(particle_list[j].trajectory)
                
                min_len = min(len(traj1), len(traj2))
                if min_len > 1:
                    corr = np.mean([
                        np.corrcoef(traj1[:min_len, d], 
                                   traj2[:min_len, d])[0, 1]
                        for d in range(min(3, traj1.shape[1]))
                        if np.std(traj1[:min_len, d]) > 0 and 
                           np.std(traj2[:min_len, d]) > 0
                    ])
                    coherence_scores.append(corr)
        
        if coherence_scores:
            features['trajectory_coherence'] = np.nanmean(coherence_scores)
        
        curvatures = [
            p.get_trajectory_curvature() 
            for p in self.constellation.values()
        ]
        features['mean_curvature'] = np.mean(curvatures)
        features['max_curvature'] = np.max(curvatures)
        
        return features
    
    def get_shape_signature(self) -> np.ndarray:
        """
        Get a fixed-size signature vector representing the constellation.
        
        Returns
        -------
        np.ndarray
            Signature vector
        """
        signature_parts = []
        
        for seg_type in SegmentType:
            if seg_type in self.positions:
                signature_parts.append(self.positions[seg_type])
            else:
                signature_parts.append(np.zeros(self.positions[SegmentType.INITIAL].shape))
        
        shape_features = self.get_shape_features()
        feature_vector = np.array(list(shape_features.values()))
        
        signature_parts.append(feature_vector)
        
        return np.concatenate(signature_parts)