import os
import json
import matplotlib.pyplot as plt
import seaborn as sns

def save_json_metrics(metrics_dict, output_path):
    with open(output_path, 'w') as f:
        json.dump(metrics_dict, f, indent=4)

def save_classification_report(report_str, output_path):
    with open(output_path, 'w') as f:
        f.write(report_str)

def save_confusion_matrix_plot(cm, labels_names, output_path):
    plt.figure(figsize=(12, 10))
    sns.heatmap(cm, annot=False, cmap='Blues', xticklabels=labels_names, yticklabels=labels_names)
    plt.title('Confusion Matrix')
    plt.ylabel('True Label')
    plt.xlabel('Predicted Label')
    plt.tight_layout()
    plt.savefig(output_path)
    plt.close()

def generate_model_health_report(
    output_path,
    overall_accuracy,
    strongest_classes,
    weakest_classes,
    top_confused_pairs
):
    """Generates a Markdown model health report."""
    
    report_lines = [
        "# Model Health Report",
        "",
        f"**Overall Accuracy:** {overall_accuracy * 100:.2f}%",
        "",
        "## Strongest Classes (by F1-Score)",
    ]
    
    for cls, score in strongest_classes:
        report_lines.append(f"- {cls}: {score:.4f}")
        
    report_lines.extend([
        "",
        "## Weakest Classes (by F1-Score)"
    ])
    
    for cls, score in weakest_classes:
        report_lines.append(f"- {cls}: {score:.4f}")
        
    report_lines.extend([
        "",
        "## Top Confused Disease Pairs"
    ])
    
    for pair in top_confused_pairs:
        report_lines.append(f"- Actual **{pair['actual']}** predicted as **{pair['predicted']}** ({pair['count']} times)")
        
    report_lines.extend([
        "",
        "## Recommended Data Collection Areas",
        "Collect additional real-world images for these classes:"
    ])
    
    for cls, _ in weakest_classes:
        report_lines.append(f"- {cls}")
        
    # Also recommend collecting for top confusions
    confused_targets = set()
    for pair in top_confused_pairs:
        confused_targets.add(pair['actual'])
        confused_targets.add(pair['predicted'])
        
    if confused_targets:
        report_lines.extend([
            "",
            "To resolve confusion, also augment data for:"
        ])
        for target in confused_targets:
            report_lines.append(f"- {target}")
            
    with open(output_path, 'w') as f:
        f.write("\n".join(report_lines))
