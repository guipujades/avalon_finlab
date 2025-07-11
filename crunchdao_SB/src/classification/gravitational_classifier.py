"""
Gravitational Classification System for Time Series.

Each series starts as a particle at origin and moves through 
multi-dimensional space based on classification forces.

References:
- Inspired by particle physics classification (CERN experiments)
- Gravitational clustering methods (Wright, 1977)
- Force-directed graph layouts (Fruchterman & Reingold, 1991)
"""

import numpy as np
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
import pandas as pd


@dataclass
class ClassificationForce:
    """
    Represents a classification force that moves the particle.
    
    Attributes
    ----------
    name : str
        Name of the classification dimension
    direction : np.ndarray
        Unit vector in n-dimensional space
    magnitude : float
        Force magnitude (0-1)
    weight : float
        Importance weight of this force
    """
    name: str
    direction: np.ndarray
    magnitude: float
    weight: float = 1.0
    
    @property
    def force_vector(self) -> np.ndarray:
        """Calculate actual force vector."""
        return self.direction * self.magnitude * self.weight


class TimeSeriesParticle:
    """
    Represents a time series as a particle in classification space.
    
    The particle starts at origin and moves based on classification forces.
    """
    
    def __init__(self, series_id: str, n_dimensions: int = 10):
        """
        Initialize particle at origin.
        
        Parameters
        ----------
        series_id : str
            Unique identifier for the series
        n_dimensions : int
            Number of dimensions in classification space
        """
        self.id = series_id
        self.position = np.zeros(n_dimensions)
        self.velocity = np.zeros(n_dimensions)
        self.mass = 1.0
        self.forces_history = []
        self.position_history = [self.position.copy()]
        
    def apply_force(self, force: ClassificationForce, damping: float = 0.8):
        """
        Apply a classification force to move the particle.
        
        Uses physics-inspired dynamics with damping.
        
        Parameters
        ----------
        force : ClassificationForce
            Force to apply
        damping : float
            Damping factor to prevent oscillations
        """
        force_vector = force.force_vector
        
        if len(force_vector) != len(self.position):
            force_vector = np.pad(force_vector, 
                                (0, len(self.position) - len(force_vector)), 
                                'constant')
        
        acceleration = force_vector / self.mass
        
        self.velocity = damping * self.velocity + acceleration
        
        self.position += self.velocity
        
        self.forces_history.append(force)
        self.position_history.append(self.position.copy())
    
    def get_center_of_mass(self) -> np.ndarray:
        """Get current center of mass (position)."""
        return self.position.copy()
    
    def get_displacement(self) -> float:
        """Get total displacement from origin."""
        return np.linalg.norm(self.position)
    
    def get_trajectory(self) -> np.ndarray:
        """Get full trajectory history."""
        return np.array(self.position_history)


class DomainSpecificClassifiers:
    """
    Classification forces based on specific physical domains.
    """
    
    @staticmethod
    def seismic_classifier(before: np.ndarray, after: np.ndarray) -> List[ClassificationForce]:
        """
        Seismic-inspired classification based on P/S wave characteristics.
        
        References:
        - Earthquake or blast classification (Oxford Academic, 2024)
        - Seismic phase detection using CNN (ResearchGate, 2019)
        """
        forces = []
        
        energy_before = np.sum(before**2)
        energy_after = np.sum(after**2)
        energy_ratio = energy_after / (energy_before + 1e-8)
        
        if energy_ratio > 1.5:
            forces.append(ClassificationForce(
                "seismic_energy_release",
                np.array([1, 0, 0, 0, 0, 0, 0, 0, 0, 0]),
                magnitude=min(1, (energy_ratio - 1) / 5),
                weight=1.2
            ))
        
        freq_before = np.abs(np.fft.fft(before))[:len(before)//2]
        freq_after = np.abs(np.fft.fft(after))[:len(after)//2]
        
        dominant_freq_before = np.argmax(freq_before) / len(freq_before)
        dominant_freq_after = np.argmax(freq_after) / len(freq_after)
        freq_shift = dominant_freq_after - dominant_freq_before
        
        if abs(freq_shift) > 0.1:
            forces.append(ClassificationForce(
                "frequency_shift",
                np.array([0, 1, 0, 0, 0, 0, 0, 0, 0, 0]),
                magnitude=min(1, abs(freq_shift) * 5),
                weight=0.8
            ))
        
        onset_sharpness = np.max(np.abs(np.diff(after[:20]))) / (np.std(before) + 1e-8)
        
        if onset_sharpness > 3:
            forces.append(ClassificationForce(
                "sharp_onset",
                np.array([0, 0, 1, 0, 0, 0, 0, 0, 0, 0]),
                magnitude=min(1, onset_sharpness / 10),
                weight=1.0
            ))
        
        return forces
    
    @staticmethod
    def chemical_reaction_classifier(before: np.ndarray, after: np.ndarray) -> List[ClassificationForce]:
        """
        Chemical reaction-inspired classification.
        
        Based on:
        - Reaction kinetics (exponential decay/growth)
        - Equilibrium shifts
        - Autocatalytic patterns
        """
        forces = []
        
        t = np.arange(len(after))
        try:
            coeffs = np.polyfit(t, np.log(np.abs(after) + 1e-8), 1)
            exp_rate = coeffs[0]
            
            if abs(exp_rate) > 0.01:
                forces.append(ClassificationForce(
                    "exponential_kinetics",
                    np.array([0, 0, 0, 1, 0, 0, 0, 0, 0, 0]),
                    magnitude=min(1, abs(exp_rate) * 50),
                    weight=1.1
                ))
        except:
            pass
        
        equilibrium_before = np.mean(before[-len(before)//4:])
        equilibrium_after = np.mean(after[-len(after)//4:])
        eq_shift = (equilibrium_after - equilibrium_before) / (np.std(before) + 1e-8)
        
        if abs(eq_shift) > 1:
            forces.append(ClassificationForce(
                "equilibrium_shift",
                np.array([0, 0, 0, 0, 1, 0, 0, 0, 0, 0]),
                magnitude=min(1, abs(eq_shift) / 5),
                weight=0.9
            ))
        
        autocorr_change = np.corrcoef(after[:-1], after[1:])[0,1] - np.corrcoef(before[:-1], before[1:])[0,1]
        
        if abs(autocorr_change) > 0.3:
            forces.append(ClassificationForce(
                "autocatalytic_pattern",
                np.array([0, 0, 0, 0, 0, 1, 0, 0, 0, 0]),
                magnitude=abs(autocorr_change),
                weight=0.7
            ))
        
        return forces
    
    @staticmethod
    def particle_physics_classifier(before: np.ndarray, after: np.ndarray) -> List[ClassificationForce]:
        """
        Particle physics-inspired classification.
        
        Based on:
        - Event detection patterns (CERN)
        - Decay signatures
        - Conservation law violations
        """
        forces = []
        
        total_before = np.sum(np.abs(before))
        total_after = np.sum(np.abs(after))
        conservation_violation = abs(total_after - total_before) / (total_before + 1e-8)
        
        if conservation_violation > 0.1:
            forces.append(ClassificationForce(
                "conservation_violation",
                np.array([0, 0, 0, 0, 0, 0, 1, 0, 0, 0]),
                magnitude=min(1, conservation_violation * 2),
                weight=1.3
            ))
        
        peaks_before = len(np.where(np.diff(np.sign(np.diff(before))) < 0)[0])
        peaks_after = len(np.where(np.diff(np.sign(np.diff(after))) < 0)[0])
        peak_ratio = peaks_after / (peaks_before + 1)
        
        if peak_ratio > 2 or peak_ratio < 0.5:
            forces.append(ClassificationForce(
                "decay_signature",
                np.array([0, 0, 0, 0, 0, 0, 0, 1, 0, 0]),
                magnitude=min(1, abs(np.log(peak_ratio))),
                weight=0.8
            ))
        
        return forces
    
    @staticmethod
    def climate_classifier(before: np.ndarray, after: np.ndarray) -> List[ClassificationForce]:
        """
        Climate/weather-inspired classification.
        
        Based on:
        - Regime shifts
        - Oscillation pattern changes
        - Extreme event frequency
        """
        forces = []
        
        var_ratio = np.var(after) / (np.var(before) + 1e-8)
        
        if var_ratio > 1.5 or var_ratio < 0.67:
            forces.append(ClassificationForce(
                "variance_regime_shift",
                np.array([0, 0, 0, 0, 0, 0, 0, 0, 1, 0]),
                magnitude=min(1, abs(np.log(var_ratio))),
                weight=1.0
            ))
        
        def count_extremes(x, threshold=2):
            return np.sum(np.abs(x - np.mean(x)) > threshold * np.std(x))
        
        extremes_before = count_extremes(before) / len(before)
        extremes_after = count_extremes(after) / len(after)
        extreme_change = extremes_after - extremes_before
        
        if abs(extreme_change) > 0.05:
            forces.append(ClassificationForce(
                "extreme_event_frequency",
                np.array([0, 0, 0, 0, 0, 0, 0, 0, 0, 1]),
                magnitude=min(1, abs(extreme_change) * 10),
                weight=0.9
            ))
        
        return forces


class GravitationalClassificationSystem:
    """
    Main system that orchestrates the gravitational classification.
    """
    
    def __init__(self):
        """Initialize the classification system."""
        self.particles = {}
        self.domain_classifiers = DomainSpecificClassifiers()
        
    def classify_series(self, series_id: str, before: np.ndarray, 
                       after: np.ndarray) -> TimeSeriesParticle:
        """
        Classify a time series using gravitational model.
        
        Parameters
        ----------
        series_id : str
            Unique identifier
        before : np.ndarray
            Values before boundary
        after : np.ndarray
            Values after boundary
            
        Returns
        -------
        TimeSeriesParticle
            Particle with final position
        """
        particle = TimeSeriesParticle(series_id)
        
        all_forces = []
        all_forces.extend(self.domain_classifiers.seismic_classifier(before, after))
        all_forces.extend(self.domain_classifiers.chemical_reaction_classifier(before, after))
        all_forces.extend(self.domain_classifiers.particle_physics_classifier(before, after))
        all_forces.extend(self.domain_classifiers.climate_classifier(before, after))
        
        for force in all_forces:
            particle.apply_force(force)
        
        self.particles[series_id] = particle
        
        return particle
    
    def get_classification_summary(self, particle: TimeSeriesParticle) -> Dict:
        """
        Get summary of particle classification.
        
        Returns
        -------
        Dict
            Summary including position, displacement, and dominant forces
        """
        dominant_forces = sorted(
            particle.forces_history, 
            key=lambda f: f.magnitude * f.weight, 
            reverse=True
        )[:3]
        
        return {
            'id': particle.id,
            'final_position': particle.get_center_of_mass(),
            'displacement': particle.get_displacement(),
            'dominant_forces': [
                {
                    'name': f.name,
                    'strength': f.magnitude * f.weight
                } for f in dominant_forces
            ],
            'trajectory_length': len(particle.position_history)
        }