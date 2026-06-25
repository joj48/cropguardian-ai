import numpy as np
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, classification_report, confusion_matrix

def calculate_basic_metrics(y_true, y_pred):
    """Calculates Accuracy, Precision, Recall, and F1."""
    return {
        "accuracy": accuracy_score(y_true, y_pred),
        "precision": precision_score(y_true, y_pred, average='weighted', zero_division=0),
        "recall": recall_score(y_true, y_pred, average='weighted', zero_division=0),
        "f1_score": f1_score(y_true, y_pred, average='weighted', zero_division=0)
    }

def generate_classification_report(y_true, y_pred, target_names):
    """Generates a text classification report."""
    # Only include target names that actually appear in y_true or y_pred
    labels = list(set(y_true).union(set(y_pred)))
    label_names = [target_names[i] for i in labels]
    return classification_report(y_true, y_pred, labels=labels, target_names=label_names, zero_division=0)

def generate_confusion_matrix(y_true, y_pred, labels=None):
    """Generates the confusion matrix array."""
    return confusion_matrix(y_true, y_pred, labels=labels)

def get_class_performance(y_true, y_pred, target_names):
    """Finds strongest and weakest classes based on F1-score."""
    labels = list(set(y_true).union(set(y_pred)))
    label_names = [target_names[i] for i in labels]
    
    report_dict = classification_report(y_true, y_pred, labels=labels, target_names=label_names, output_dict=True, zero_division=0)
    
    class_metrics = []
    for label in label_names:
        if label in report_dict:
            class_metrics.append((label, report_dict[label]['f1-score']))
            
    class_metrics.sort(key=lambda x: x[1], reverse=True)
    
    strongest = class_metrics[:3]
    weakest = class_metrics[-3:] if len(class_metrics) >= 3 else class_metrics
    weakest.reverse() # lowest first
    
    return strongest, weakest

def get_top_confused_pairs(y_true, y_pred, target_names, top_n=5):
    """Finds pairs of classes that are most frequently confused."""
    labels = list(set(y_true).union(set(y_pred)))
    cm = confusion_matrix(y_true, y_pred, labels=labels)
    
    confusions = []
    for i in range(len(labels)):
        for j in range(len(labels)):
            if i != j and cm[i, j] > 0:
                confusions.append({
                    "actual": target_names[labels[i]],
                    "predicted": target_names[labels[j]],
                    "count": int(cm[i, j])
                })
                
    confusions.sort(key=lambda x: x["count"], reverse=True)
    return confusions[:top_n]
