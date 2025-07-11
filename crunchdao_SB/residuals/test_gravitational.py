"""
Test gravitational classification system on structural break data.
"""

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
import sys
sys.path.append('src')

from classification.gravitational_classifier import GravitationalClassificationSystem


def load_sample_data(n_samples=100):
    """Load sample of training data."""
    X_train = pd.read_parquet('database/X_train.parquet').reset_index()
    y_train = pd.read_parquet('database/y_train.parquet')
    y_train = y_train.rename(columns={'structural_breakpoint': 'label'})
    
    unique_ids = X_train['id'].unique()[:n_samples]
    
    return X_train, y_train, unique_ids


def visualize_particle_positions(particles, labels):
    """Visualize particle positions in 3D space."""
    fig = plt.figure(figsize=(15, 10))
    
    ax1 = fig.add_subplot(221, projection='3d')
    ax2 = fig.add_subplot(222)
    ax3 = fig.add_subplot(223)
    ax4 = fig.add_subplot(224)
    
    positions_break = []
    positions_no_break = []
    
    for pid, particle in particles.items():
        pos = particle.get_center_of_mass()
        label = labels.loc[pid, 'label']
        
        if label:
            positions_break.append(pos)
        else:
            positions_no_break.append(pos)
    
    if positions_break:
        positions_break = np.array(positions_break)
        ax1.scatter(positions_break[:, 0], positions_break[:, 1], 
                   positions_break[:, 2], c='red', alpha=0.6, 
                   label='With Break', s=50)
    
    if positions_no_break:
        positions_no_break = np.array(positions_no_break)
        ax1.scatter(positions_no_break[:, 0], positions_no_break[:, 1], 
                   positions_no_break[:, 2], c='blue', alpha=0.6, 
                   label='No Break', s=50)
    
    ax1.set_xlabel('Dim 0 (Seismic)')
    ax1.set_ylabel('Dim 1 (Frequency)')
    ax1.set_zlabel('Dim 2 (Onset)')
    ax1.legend()
    ax1.set_title('3D Particle Positions')
    
    all_positions = list(particles.values())
    displacements_break = []
    displacements_no_break = []
    
    for pid, particle in particles.items():
        displacement = particle.get_displacement()
        label = labels.loc[pid, 'label']
        
        if label:
            displacements_break.append(displacement)
        else:
            displacements_no_break.append(displacement)
    
    ax2.hist([displacements_no_break, displacements_break], 
             bins=20, alpha=0.7, label=['No Break', 'With Break'])
    ax2.set_xlabel('Displacement from Origin')
    ax2.set_ylabel('Count')
    ax2.legend()
    ax2.set_title('Distribution of Displacements')
    
    force_counts = {}
    for particle in particles.values():
        for force in particle.forces_history:
            if force.name not in force_counts:
                force_counts[force.name] = {'break': 0, 'no_break': 0}
            
            label = labels.loc[particle.id, 'label']
            if label:
                force_counts[force.name]['break'] += force.magnitude * force.weight
            else:
                force_counts[force.name]['no_break'] += force.magnitude * force.weight
    
    force_names = list(force_counts.keys())
    break_strengths = [force_counts[f]['break'] for f in force_names]
    no_break_strengths = [force_counts[f]['no_break'] for f in force_names]
    
    x = np.arange(len(force_names))
    width = 0.35
    
    ax3.bar(x - width/2, no_break_strengths, width, label='No Break', alpha=0.7)
    ax3.bar(x + width/2, break_strengths, width, label='With Break', alpha=0.7)
    ax3.set_xlabel('Force Type')
    ax3.set_ylabel('Cumulative Strength')
    ax3.set_xticks(x)
    ax3.set_xticklabels(force_names, rotation=45, ha='right')
    ax3.legend()
    ax3.set_title('Force Contributions by Class')
    
    sample_particle = list(particles.values())[0]
    trajectory = sample_particle.get_trajectory()
    
    ax4.plot(trajectory[:, 0], trajectory[:, 1], 'o-', alpha=0.7)
    ax4.scatter(0, 0, c='green', s=100, marker='x', label='Origin')
    ax4.scatter(trajectory[-1, 0], trajectory[-1, 1], c='red', s=100, 
                marker='*', label='Final')
    ax4.set_xlabel('Dim 0')
    ax4.set_ylabel('Dim 1')
    ax4.legend()
    ax4.set_title(f'Sample Trajectory (Series {sample_particle.id})')
    ax4.grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig('gravitational_classification_results.png', dpi=150)
    plt.close()


def analyze_classification_performance(particles, labels):
    """Analyze how well displacement separates classes."""
    from scipy import stats
    
    displacements = {}
    positions = {}
    
    for pid, particle in particles.items():
        label = labels.loc[pid, 'label']
        displacement = particle.get_displacement()
        position = particle.get_center_of_mass()
        
        if label not in displacements:
            displacements[label] = []
            positions[label] = []
        
        displacements[label].append(displacement)
        positions[label].append(position)
    
    disp_no_break = displacements[False]
    disp_break = displacements[True]
    
    t_stat, p_value = stats.ttest_ind(disp_no_break, disp_break)
    
    mean_diff = np.mean(disp_break) - np.mean(disp_no_break)
    pooled_std = np.sqrt((np.var(disp_break) + np.var(disp_no_break)) / 2)
    cohen_d = mean_diff / pooled_std if pooled_std > 0 else 0
    
    print("\nClassification Performance:")
    print(f"Mean displacement (No Break): {np.mean(disp_no_break):.3f}")
    print(f"Mean displacement (Break): {np.mean(disp_break):.3f}")
    print(f"Cohen's d: {cohen_d:.3f}")
    print(f"P-value: {p_value:.3f}")
    
    print("\nDimensional Analysis:")
    pos_no_break = np.array(positions[False])
    pos_break = np.array(positions[True])
    
    for dim in range(min(5, pos_no_break.shape[1])):
        dim_no_break = pos_no_break[:, dim]
        dim_break = pos_break[:, dim]
        
        if np.std(dim_no_break) > 0 and np.std(dim_break) > 0:
            d = (np.mean(dim_break) - np.mean(dim_no_break)) / np.sqrt((np.var(dim_break) + np.var(dim_no_break)) / 2)
            print(f"  Dim {dim}: Cohen's d = {d:.3f}")


def main():
    """Run gravitational classification test."""
    print("Loading data...")
    X_train, y_train, unique_ids = load_sample_data(n_samples=200)
    
    print("Initializing gravitational classification system...")
    gcs = GravitationalClassificationSystem()
    
    print("Classifying series...")
    particles = {}
    
    for i, series_id in enumerate(unique_ids):
        if i % 50 == 0:
            print(f"  Processing {i}/{len(unique_ids)}")
        
        series_data = X_train[X_train['id'] == series_id]
        before = series_data[series_data['period'] == 0]['value'].values
        after = series_data[series_data['period'] == 1]['value'].values
        
        particle = gcs.classify_series(series_id, before, after)
        particles[series_id] = particle
    
    print("\nGenerating visualizations...")
    visualize_particle_positions(particles, y_train)
    
    analyze_classification_performance(particles, y_train)
    
    print("\nExample classification summaries:")
    for i, (pid, particle) in enumerate(list(particles.items())[:3]):
        summary = gcs.get_classification_summary(particle)
        label = y_train.loc[pid, 'label']
        print(f"\nSeries {pid} (Break: {label}):")
        print(f"  Displacement: {summary['displacement']:.3f}")
        print(f"  Dominant forces:")
        for force in summary['dominant_forces']:
            print(f"    - {force['name']}: {force['strength']:.3f}")
    
    print("\nResults saved to gravitational_classification_results.png")


if __name__ == '__main__':
    main()