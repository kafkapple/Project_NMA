import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
from sklearn.decomposition import PCA
from sklearn.metrics import confusion_matrix
from sklearn.manifold import TSNE
import wandb
import torch
from scipy.stats import spearmanr
import pandas as pd
from tqdm import tqdm
import os

def get_logits_from_output(outputs):
    if isinstance(outputs, dict):
        return outputs.get('logits', outputs.get('last_hidden_state'))
    elif isinstance(outputs, torch.Tensor):
        return outputs  # 이미 로짓 텐서인 경우
    elif hasattr(outputs, 'logits'):
        return outputs.logits
    elif hasattr(outputs, 'last_hidden_state'):
        return outputs.last_hidden_state
    else:
        raise ValueError("Unexpected output format from the model")

# def visualize_metric(model, data_loader):
#     fig = plot_confusion_matrix(all_labels, all_preds, config.LABELS_EMOTION)
    
def save_and_log_figure(stage, fig, config, name, title):
    """Save figure to file and log to wandb"""
    path=os.path.join(config.MODEL_DIR, 'results')
    os.makedirs(path, exist_ok=True)
    fig.savefig(os.path.join(path, f"{name}_{config.global_epoch}.png"))
    wandb.log({f"{stage}":{f"{name}": wandb.Image(fig, caption=title)}}, step=config.global_epoch)
    
def visualize_results(config, model, data_loader, device, log_data, stage):
    print('\nVisualization of results starts.\n')
    if stage in ['train', 'val'] and log_data:
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 4))
        try:
            epochs = [entry['epoch'] for entry in log_data[stage]]
            losses = [entry['loss'] for entry in log_data[stage]]
            accuracies = [entry['accuracy'] for entry in log_data[stage]]
            
            ax1.plot(epochs, losses, 'bo-')
            ax1.set_title(f'{stage.capitalize()} Loss')
            ax1.set_xlabel('Epochs')
            ax1.set_ylabel('Loss')
            
            ax2.plot(epochs, accuracies, 'ro-')
            ax2.set_title(f'{stage.capitalize()} Accuracy')
            ax2.set_xlabel('Epochs')
            ax2.set_ylabel('Accuracy')
            
            save_and_log_figure(stage, fig, config, "learning_curves", f"{stage.capitalize()} Learning Curves")
            plt.close(fig)
        except:
            print('Err. no learning curve.')

    # Confusion Matrix and Embeddings visualization for all stages
    model.eval()
    all_preds = []
    all_labels = []
    all_embeddings = []

    with torch.no_grad():
        for batch in tqdm(data_loader, desc="Preparing data for Visualizing..."):
            inputs = batch['audio'].to(device)
            labels = batch['label'].to(device)
            outputs = model(inputs)
            logits = get_logits_from_output(outputs)
            _, preds = torch.max(logits, 1) 
            #_, preds = torch.max(outputs.logits, 1)
            
            all_preds.extend(preds.cpu().numpy())
            all_labels.extend(labels.cpu().numpy())
            all_embeddings.extend(outputs.logits.cpu().numpy())

    # Convert lists to numpy arrays
    all_preds = np.array(all_preds)
    all_labels = np.array(all_labels)
    all_embeddings = np.array(all_embeddings)

    # Confusion Matrix
    fig_cm = plot_confusion_matrix(all_labels, all_preds, config.LABELS_EMOTION)
    save_and_log_figure(stage, fig_cm, config, "confusion_matrix", f"{stage} Confusion Matrix")
    plt.close(fig_cm)

    # Embeddings visualization
    max_samples = config.N_EMBEDDINGS # to show
    
    if len(all_embeddings) > max_samples:
        indices = np.random.choice(len(all_embeddings), max_samples, replace=False)
        all_embeddings = all_embeddings[indices]
        all_labels = all_labels[indices]
    
    try:
        fig_embd = visualize_embeddings(config, all_embeddings, all_labels)
    
        save_and_log_figure(stage, fig_embd, config, "embeddings", f"{stage.capitalize()} Embeddings (t-SNE)")
        plt.close(fig_embd)
    except:
        print('No embedding.')    

    fig_rsa = perform_rsa(model, data_loader, config.device)
    save_and_log_figure(stage, fig_rsa, config, "Representation_similarity", f"{stage.capitalize()}")
    plt.close(fig_rsa)
def extract_embeddings_and_predictions(model, data_loader, device):
    model.eval()
    all_embeddings = []
    all_labels = []
    all_predictions = []
    
    with torch.no_grad():
        for inputs, labels in data_loader:
            inputs = inputs.to(device)
            outputs = model(inputs)
            
            hidden_states = outputs.last_hidden_state
            pooled_output = torch.mean(hidden_states, dim=1)
            
            logits = model.classifier(pooled_output)
            
            # predictions = outputs.argmax(dim=1).cpu().numpy()
            
            
            all_embeddings.extend(pooled_output.cpu().numpy())
            all_labels.extend(labels.numpy())
            all_predictions.extend(labels.cpu().numpy())
    
    return np.array(all_embeddings), np.array(all_labels), np.array(all_predictions)

def visualize_embeddings(config, embeddings, labels, method='tsne'):
    print('\nVisualization of embedding starts...\n')
    if method == 'pca':
        reducer = PCA(n_components=2)
    elif method == 'tsne':
        reducer = TSNE(n_components=2, random_state=42)
    else:
        raise ValueError("Invalid method. Use 'pca' or 'tsne'.")

    reduced_embeddings = reducer.fit_transform(embeddings)

    string_labels = [config.LABELS_EMOTION.get(int(label), f"Unknown_{label}") for label in labels]

    #string_labels = [config.LABELS_EMOTION.get(str(int(label)), f"Unknown_{label}") for label in labels]
    df = pd.DataFrame({
        'x': reduced_embeddings[:, 0],
        'y': reduced_embeddings[:, 1],
        'label': string_labels
    })

    fig, ax = plt.subplots(figsize=(10, 8))
    sns.scatterplot(data=df, x='x', y='y', hue='label', palette="deep", legend="full", ax=ax)
    ax.set_title(f"{method.upper()} of Emotion Recognition Embeddings")
    
    return fig


def plot_learning_curves(config):
    # Assuming we've saved loss and accuracy values during training
    train_losses = np.load(f"{config.MODEL_DIR}/train_losses.npy")
    val_losses = np.load(f"{config.MODEL_DIR}/val_losses.npy")
    train_accuracies = np.load(f"{config.MODEL_DIR}/train_accuracies.npy")
    val_accuracies = np.load(f"{config.MODEL_DIR}/val_accuracies.npy")
    
    epochs = range(1, len(train_losses) + 1)
    
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 10))
    
    ax1.plot(epochs, train_losses, 'bo-', label='Training Loss')
    ax1.plot(epochs, val_losses, 'ro-', label='Validation Loss')
    ax1.set_title('Training and Validation Loss')
    ax1.set_xlabel('Epochs')
    ax1.set_ylabel('Loss')
    ax1.legend()
    
    ax2.plot(epochs, train_accuracies, 'bo-', label='Training Accuracy')
    ax2.plot(epochs, val_accuracies, 'ro-', label='Validation Accuracy')
    ax2.set_title('Training and Validation Accuracy')
    ax2.set_xlabel('Epochs')
    ax2.set_ylabel('Accuracy')
    ax2.legend()
    
    #plt.tight_layout()
    plt.savefig(f"{config.MODEL_DIR}/learning_curves.png")
    wandb.log({"learning_curves": wandb.Image(plt)})
    
def plot_confusion_matrix(labels, preds, labels_emotion, normalize=True):
    cm = confusion_matrix(labels, preds)
    if normalize:
        cm = cm.astype('float') / cm.sum(axis=1)[:, np.newaxis]
        fmt = '.2f'
    else:
        fmt = 'd'
    
    fig, ax = plt.subplots(figsize=(10, 8))
    sns.heatmap(cm, annot=True, fmt=fmt, cmap='Blues', xticklabels=labels_emotion.values(), yticklabels=labels_emotion.values(), ax=ax)
    ax.set_xlabel('Predicted')
    ax.set_ylabel('True')
    ax.set_title('Confusion Matrix')
    
    # wandb.log({"confusion_matrix": wandb.Image(fig)})
    #plt.close(fig)
    return fig

def perform_rsa(model, data_loader, device):
    model.eval()
    representations = []
    labels = []

    with torch.no_grad():
        for batch in data_loader:
            inputs = batch['audio'].to(device)
            batch_labels = batch['label']
            outputs = model(inputs)
            representations.append(outputs.logits.cpu().numpy())
            labels.extend(batch_labels.numpy())

    representations = np.vstack(representations)
    labels = np.array(labels)

    corr_matrix = np.corrcoef(representations)

    # Calculate label correlation matrix
    label_matrix = np.equal.outer(labels, labels).astype(int)

    # Calculate RSA correlation
    rsa_corr, _ = spearmanr(corr_matrix.flatten(), label_matrix.flatten())

    # Plot the representation correlation matrix and the label correlation matrix
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(20, 8))

    sns.heatmap(corr_matrix, cmap='coolwarm', ax=ax1)
    ax1.set_title("Representation Correlation Matrix")

    sns.heatmap(label_matrix, cmap='coolwarm', ax=ax2)
    ax2.set_title("Label Correlation Matrix")

    plt.suptitle(f"RSA Correlation: {rsa_corr:.2f}", fontsize=16)
    return fig

def plot_learning_curves(history):
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 12))
    
    epochs = range(1, len(history['train']['loss']) + 1)
    
    ax1.plot(epochs, history['train']['loss'], 'bo-', label='Training Loss')
    ax1.plot(epochs, history['val']['loss'], 'ro-', label='Validation Loss')
    ax1.set_title('Training and Validation Loss')
    ax1.set_xlabel('Epochs')
    ax1.set_ylabel('Loss')
    ax1.legend()
    
    ax2.plot(epochs, history['train']['accuracy'], 'bo-', label='Training Accuracy')
    ax2.plot(epochs, history['val']['accuracy'], 'ro-', label='Validation Accuracy')
    ax2.set_title('Training and Validation Accuracy')
    ax2.set_xlabel('Epochs')
    ax2.set_ylabel('Accuracy')
    ax2.legend()
    
    #plt.tight_layout()
    return fig