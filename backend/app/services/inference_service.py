import torch
import joblib
import numpy as np
from pathlib import Path
from typing import Dict, List, Optional

class AttentionMIL(torch.nn.Module):
    def __init__(self, input_dim, hidden_dim=128, output_dim=1, mode='classification', case_feat_dim=None):
        super().__init__()
        self.mode = mode
        self.case_feat_dim = case_feat_dim

        self.attention = torch.nn.Sequential(
            torch.nn.Linear(input_dim, hidden_dim),
            torch.nn.Tanh(),
            torch.nn.Linear(hidden_dim, 1)
        )
        self.sentence_proj = torch.nn.Linear(input_dim, hidden_dim)
        
        if case_feat_dim == None:
            in_dim = input_dim
            self.classifier = torch.nn.Sequential(
                torch.nn.ReLU(),
                torch.nn.Linear(hidden_dim, output_dim)
            )
        else:
            in_dim = input_dim + case_feat_dim
            self.case_proj = torch.nn.Linear(case_feat_dim, hidden_dim)
            self.classifier = torch.nn.Sequential(
                torch.nn.ReLU(),
                torch.nn.Linear(hidden_dim*2, output_dim)
            )       

    def forward(self, x, case_feats=None):
        A = self.attention(x)
        A = torch.softmax(A, dim=0)
        M = torch.sum(A * x, dim=0)
        M_proj = self.sentence_proj(M)
        if case_feats is not None:
            # M_proj = torch.cat([M, case_feats], dim=-1)
            M_proj = torch.cat([M_proj, self.case_proj(case_feats)], dim=-1)
            # M_proj = M_proj + self.case_proj(case_feats)
        out = self.classifier(M_proj)
        if self.mode == 'classification':
            return torch.sigmoid(out), A
        else:
            return out, A

class ModelManager:
    def __init__(self):
        self.loaded_models = {}
        self.loaded_scalers = {}
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

    def get_assets(self, config):
        cfg_id = config['config_id']

        if cfg_id not in self.loaded_models:
            
            scaler = None
            if config['scaler_path']:
                scaler = joblib.load(config['scaler_path'])
            self.loaded_scalers[cfg_id] = scaler

            model = AttentionMIL(
                input_dim=config['input_dim'],
                case_feat_dim=33 if config['use_features'] else None,
            )

            checkpoint = torch.load(config['checkpoint_path'], map_location=self.device, weights_only=False)

            # 2. Extract ONLY the model weights
            # Depending on how you saved it, the key is likely 'model_state_dict'
            state_dict = checkpoint.get('model_state_dict', checkpoint)

            # 3. Load those weights into the model
            model.load_state_dict(state_dict)
            model.to(self.device).eval()
            self.loaded_models[cfg_id] = model
        
        return self.loaded_models[cfg_id], self.loaded_scalers[cfg_id]

    def run_inference(self, config, embeddings, ordered_features=None):
        model, scaler = self.get_assets(config)

        feat_tensor = None
        if scaler and ordered_features:
            print(f"\n--- DEBUG: INFERENCE START ---")
            print(f"RAW FEATURES: {ordered_features}")
            scaled = scaler.transform([ordered_features])
            print(f"SCALED FEATURES: {scaled[0]}")
            feat_tensor = torch.tensor(scaled[0], dtype=torch.float32).to(self.device)
            

        emb_tensor = torch.tensor(embeddings, dtype=torch.float32).to(self.device)
        print(f"EMBEDDING SHAPE: {emb_tensor.shape}")

        with torch.no_grad():
            score_tensor, attn_tensor = model(emb_tensor, case_feats=feat_tensor)
        
        score = round(float(score_tensor.item()), 4)
        print(f"FINAL SCORE: {score}")
        print(f"--- DEBUG: INFERENCE END ---\n")
        return {
            "score": score,
            "label": "High Impact" if score >= 0.5 else "Low Impact",
            "attention": attn_tensor.squeeze().cpu().numpy().tolist()
        }

inference_engine = ModelManager()