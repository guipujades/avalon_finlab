"""
Test and visualize the constellation classification system.
"""

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
from matplotlib.patches import FancyBboxPatch
import matplotlib.patches as mpatches
import sys
sys.path.append('src')

from classification.constellation_classifier import (
    ConstellationClassifier, ConstellationShape, SegmentType
)


def load_sample_series(n_samples=50):
    """Load sample series for testing."""
    X_train = pd.read_parquet('database/X_train.parquet').reset_index()
    y_train = pd.read_parquet('database/y_train.parquet')
    y_train = y_train.rename(columns={'structural_breakpoint': 'label'})
    
    break_ids = y_train[y_train['label'] == True].index.values[:n_samples//2]
    no_break_ids = y_train[y_train['label'] == False].index.values[:n_samples//2]
    
    sample_ids = np.concatenate([break_ids, no_break_ids])
    
    return X_train, y_train, sample_ids


def visualize_constellation_3d(constellation, title="Constellation View"):
    """Visualize a single constellation in 3D."""
    fig = plt.figure(figsize=(12, 10))
    ax = fig.add_subplot(111, projection='3d')
    
    colors = {
        SegmentType.INITIAL: 'green',
        SegmentType.PRE_BOUNDARY_FAR: 'blue',
        SegmentType.PRE_BOUNDARY_NEAR: 'cyan',
        SegmentType.POST_BOUNDARY_NEAR: 'orange',
        SegmentType.POST_BOUNDARY_FAR: 'red',
        SegmentType.FINAL: 'darkred',
        SegmentType.TRANSITION: 'purple'
    }
    
    for seg_type, particle in constellation.items():
        trajectory = np.array(particle.trajectory)
        
        if len(trajectory) > 0:
            ax.plot(trajectory[:, 0], trajectory[:, 1], trajectory[:, 2],
                   color=colors[seg_type], alpha=0.5, linewidth=1)
            
            ax.scatter(particle.position[0], particle.position[1], particle.position[2],
                      color=colors[seg_type], s=100, marker='o',
                      edgecolor='black', linewidth=2,
                      label=seg_type.value)
            
            ax.scatter(0, 0, 0, color='black', s=200, marker='x', linewidth=3)
    
    ax.set_xlabel('Dimension 0')
    ax.set_ylabel('Dimension 1')
    ax.set_zlabel('Dimension 2')
    ax.set_title(title)
    ax.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
    
    return fig


def visualize_constellation_comparison(constellations_break, constellations_no_break):
    """Compare constellations between break and no-break series."""
    fig = plt.figure(figsize=(20, 12))
    
    ax1 = fig.add_subplot(231, projection='3d')
    ax2 = fig.add_subplot(232, projection='3d')
    ax3 = fig.add_subplot(233)
    ax4 = fig.add_subplot(234)
    ax5 = fig.add_subplot(235)
    ax6 = fig.add_subplot(236)
    
    def plot_average_constellation(constellations, ax, title):
        """Plot average positions for each segment type."""
        avg_positions = {}
        
        for seg_type in SegmentType:
            positions = []
            for const in constellations:
                if seg_type in const:
                    positions.append(const[seg_type].position[:3])
            
            if positions:
                avg_positions[seg_type] = np.mean(positions, axis=0)
        
        for seg_type, avg_pos in avg_positions.items():
            ax.scatter(avg_pos[0], avg_pos[1], avg_pos[2],
                      s=200, marker='o', alpha=0.7,
                      label=seg_type.value)
        
        ax.scatter(0, 0, 0, color='black', s=300, marker='x', linewidth=3)
        ax.set_title(title)
        ax.set_xlabel('Dim 0')
        ax.set_ylabel('Dim 1')
        ax.set_zlabel('Dim 2')
    
    plot_average_constellation(constellations_break, ax1, "Average Constellation (Break)")
    plot_average_constellation(constellations_no_break, ax2, "Average Constellation (No Break)")
    
    ax1.legend(bbox_to_anchor=(1.05, 1), loc='upper left', fontsize=8)
    
    def extract_shape_features(constellations):
        """Extract shape features from all constellations."""
        all_features = []
        for const in constellations:
            shape = ConstellationShape(const)
            features = shape.get_shape_features()
            all_features.append(features)
        return pd.DataFrame(all_features)
    
    features_break = extract_shape_features(constellations_break)
    features_no_break = extract_shape_features(constellations_no_break)
    
    feature_names = ['centroid_distance', 'dispersion', 'boundary_shift', 'mean_curvature']
    
    for idx, (ax, feature) in enumerate(zip([ax3, ax4, ax5, ax6], feature_names)):
        if feature in features_break.columns:
            ax.hist([features_no_break[feature].dropna(), 
                    features_break[feature].dropna()],
                   bins=20, alpha=0.7, label=['No Break', 'Break'])
            ax.set_xlabel(feature.replace('_', ' ').title())
            ax.set_ylabel('Count')
            ax.legend()
            
            from scipy import stats
            t_stat, p_val = stats.ttest_ind(
                features_no_break[feature].dropna(),
                features_break[feature].dropna()
            )
            ax.set_title(f'p-value: {p_val:.3f}')
    
    plt.tight_layout()
    return fig


def visualize_trajectory_patterns(constellations_break, constellations_no_break):
    """Visualize trajectory patterns for different segment types."""
    fig, axes = plt.subplots(2, 4, figsize=(20, 10))
    
    segment_types = [
        SegmentType.INITIAL, SegmentType.PRE_BOUNDARY_NEAR,
        SegmentType.POST_BOUNDARY_NEAR, SegmentType.FINAL
    ]
    
    for col, seg_type in enumerate(segment_types):
        for row, (constellations, label) in enumerate([
            (constellations_no_break, "No Break"),
            (constellations_break, "Break")
        ]):
            ax = axes[row, col]
            
            trajectories = []
            for const in constellations[:10]:
                if seg_type in const:
                    traj = np.array(const[seg_type].trajectory)
                    if len(traj) > 0:
                        ax.plot(traj[:, 0], traj[:, 1], alpha=0.3)
                        trajectories.append(traj)
            
            if trajectories:
                all_points = np.vstack([t[-1] for t in trajectories])
                ax.scatter(all_points[:, 0], all_points[:, 1], 
                          s=50, alpha=0.8, edgecolor='black')
            
            ax.scatter(0, 0, color='red', s=100, marker='x')
            ax.set_title(f'{seg_type.value} - {label}')
            ax.grid(True, alpha=0.3)
            ax.set_xlabel('Dim 0')
            ax.set_ylabel('Dim 1')
    
    plt.tight_layout()
    return fig


def analyze_classification_performance(constellations_break, constellations_no_break):
    """Analyze how well constellations separate classes."""
    print("\n" + "="*60)
    print("CONSTELLATION CLASSIFICATION ANALYSIS")
    print("="*60)
    
    signatures_break = []
    signatures_no_break = []
    
    for const in constellations_break:
        shape = ConstellationShape(const)
        signatures_break.append(shape.get_shape_signature())
    
    for const in constellations_no_break:
        shape = ConstellationShape(const)
        signatures_no_break.append(shape.get_shape_signature())
    
    signatures_break = np.array(signatures_break)
    signatures_no_break = np.array(signatures_no_break)
    
    from sklearn.discriminant_analysis import LinearDiscriminantAnalysis
    from sklearn.model_selection import cross_val_score
    
    X = np.vstack([signatures_no_break, signatures_break])
    y = np.array([0] * len(signatures_no_break) + [1] * len(signatures_break))
    
    lda = LinearDiscriminantAnalysis()
    scores = cross_val_score(lda, X, y, cv=5, scoring='roc_auc')
    
    print(f"\nCross-validated ROC AUC: {np.mean(scores):.3f} (+/- {np.std(scores):.3f})")
    
    shape_features_break = []
    shape_features_no_break = []
    
    for const in constellations_break:
        shape = ConstellationShape(const)
        shape_features_break.append(shape.get_shape_features())
    
    for const in constellations_no_break:
        shape = ConstellationShape(const)
        shape_features_no_break.append(shape.get_shape_features())
    
    df_break = pd.DataFrame(shape_features_break)
    df_no_break = pd.DataFrame(shape_features_no_break)
    
    print("\nFeature Importance (Cohen's d):")
    print("-" * 40)
    
    for feature in df_break.columns:
        if feature in df_no_break.columns:
            d = (df_break[feature].mean() - df_no_break[feature].mean()) / \
                np.sqrt((df_break[feature].var() + df_no_break[feature].var()) / 2)
            print(f"{feature:25s}: {d:6.3f}")
    
    print("\nSegment-wise Analysis:")
    print("-" * 40)
    
    for seg_type in SegmentType:
        displacements_break = []
        displacements_no_break = []
        
        for const in constellations_break:
            if seg_type in const:
                displacements_break.append(const[seg_type].get_displacement())
        
        for const in constellations_no_break:
            if seg_type in const:
                displacements_no_break.append(const[seg_type].get_displacement())
        
        if displacements_break and displacements_no_break:
            d = (np.mean(displacements_break) - np.mean(displacements_no_break)) / \
                np.sqrt((np.var(displacements_break) + np.var(displacements_no_break)) / 2)
            print(f"{seg_type.value:25s}: {d:6.3f}")


def main():
    """Run constellation classification test."""
    print("Loading data...")
    X_train, y_train, sample_ids = load_sample_series(n_samples=100)
    
    print("Creating constellation classifier...")
    classifier = ConstellationClassifier(n_dimensions=12)
    
    constellations_break = []
    constellations_no_break = []
    
    print("Processing series...")
    for i, series_id in enumerate(sample_ids):
        if i % 20 == 0:
            print(f"  {i}/{len(sample_ids)}")
        
        series_data = X_train[X_train['id'] == series_id]
        before = series_data[series_data['period'] == 0]['value'].values
        after = series_data[series_data['period'] == 1]['value'].values
        
        constellation = classifier.create_constellation(before, after)
        classifier.apply_classification_forces(constellation)
        
        label = y_train.loc[series_id, 'label']
        if label:
            constellations_break.append(constellation)
        else:
            constellations_no_break.append(constellation)
    
    print("\nVisualizing single constellation example...")
    example_const = constellations_break[0] if constellations_break else constellations_no_break[0]
    fig1 = visualize_constellation_3d(example_const, "Example Constellation (Break)")
    plt.savefig('constellation_example_3d.png', dpi=150, bbox_inches='tight')
    plt.close()
    
    print("Creating comparison visualizations...")
    fig2 = visualize_constellation_comparison(constellations_break, constellations_no_break)
    plt.savefig('constellation_comparison.png', dpi=150, bbox_inches='tight')
    plt.close()
    
    print("Visualizing trajectory patterns...")
    fig3 = visualize_trajectory_patterns(constellations_break, constellations_no_break)
    plt.savefig('constellation_trajectories.png', dpi=150, bbox_inches='tight')
    plt.close()
    
    analyze_classification_performance(constellations_break, constellations_no_break)
    
    print("\nVisualizations saved:")
    print("  - constellation_example_3d.png")
    print("  - constellation_comparison.png")
    print("  - constellation_trajectories.png")


if __name__ == '__main__':
    main()