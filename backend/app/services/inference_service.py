import torch
import joblib
import numpy as np
from pathlib import Path
from typing import Dict, List, Optional

class AttentionMIL(torch.nn.Module):

    def __init__(self, input_dim, hidden_dim=128, output_dim=1, mode='classification', case_feat_dim=None, fusion_type='gated'):
        super().__init__()

        self.mode = mode
        self.case_feat_dim = case_feat_dim
        self.fusion_type = fusion_type
        self.hidden_dim = hidden_dim

        # ======================================
        # SENTENCE ATTENTION
        # ======================================
        self.attention = torch.nn.Sequential(
            torch.nn.Linear(input_dim, hidden_dim),
            torch.nn.Tanh(),
            torch.nn.Linear(hidden_dim, 1)
        )

        self.sentence_proj = torch.nn.Linear(input_dim, hidden_dim)

        # ======================================
        # GLOBAL TEXTUAL FEATURE BRANCH
        # ======================================
        if case_feat_dim is not None:
            self.feature_gate = torch.nn.Sequential(
                torch.nn.Linear(case_feat_dim, hidden_dim),
                torch.nn.ReLU(),
                torch.nn.Linear(hidden_dim, case_feat_dim)
            )

            self.case_mlp = torch.nn.Sequential(
                torch.nn.Linear(case_feat_dim, hidden_dim),
                torch.nn.ReLU(),
                torch.nn.Dropout(0.2),
                torch.nn.Linear(hidden_dim, hidden_dim)
            )

        # ======================================
        # FUSION OF TEXT EMBEDDINGS AND GLOBAL TEXTUAL FEATURES
        # ======================================

        if case_feat_dim is None:
            self.classifier = torch.nn.Sequential(
                torch.nn.ReLU(),
                torch.nn.Linear(hidden_dim, output_dim)
            )
        else:
            if fusion_type == 'gated':
                self.gate = torch.nn.Sequential(
                    torch.nn.Linear(hidden_dim * 2, hidden_dim),
                    torch.nn.Sigmoid()
                )

                self.classifier = torch.nn.Sequential(
                    torch.nn.ReLU(),
                    torch.nn.Linear(hidden_dim, output_dim)
                )
            else:
                self.classifier = torch.nn.Sequential(
                    torch.nn.ReLU(),
                    torch.nn.Linear(hidden_dim * 2, output_dim)
                )
    
    # ==========================================
    # ENCODE TEXT EMBEDDINGS WITH ATTENTION
    # ==========================================
    def encode_text(self, x):
        A = self.attention(x)
        A = torch.softmax(A, dim=0)
        M = torch.sum(A * x, dim=0, keepdim=True)
        #M = torch.sum(A * x, dim=0)
        M_proj = self.sentence_proj(M)

        return M_proj, A
           
    # ==========================================
    # ENCODE GLOBAL TEXTUAL FEATURES
    # ==========================================
    def encode_features(self, case_feats):
        gate_logits = self.feature_gate(case_feats)
        feature_gates = torch.sigmoid(gate_logits)
        gated_feats = feature_gates * case_feats
        case_proj = self.case_mlp(gated_feats)

        return case_proj, feature_gates

    # ==========================================
    # FUSION OF TEXT EMBEDDINGS AND GLOBAL TEXTUAL FEATURES
    # ==========================================
    def fuse(self, text_repr, feat_repr):
        if feat_repr is None:
            return text_repr

        # ensure 2D consistency
        if text_repr.dim() == 1:
            text_repr = text_repr.unsqueeze(0)

        if feat_repr.dim() == 1:
            feat_repr = feat_repr.unsqueeze(0)

        if self.fusion_type == 'gated':
            fusion = torch.cat([text_repr, feat_repr], dim=-1)
            gate = self.gate(fusion)
            fused = gate * text_repr + (1 - gate) * feat_repr

        else:
            fused = torch.cat([text_repr, feat_repr], dim=-1)

        return fused.squeeze(0)
    
    # ==========================================
    # CLASSIFIER
    # ==========================================
    def predict_from_repr(self, fused_repr):
        out = self.classifier(fused_repr)

        if self.mode == 'classification':
            pred = torch.sigmoid(out)
        else:
            pred = out
            # constrain to REF score range
            #pred = 4.0 * torch.sigmoid(out)

        return pred
    
    # ==========================================
    # FORWARD
    # ==========================================

    def forward(self, x, case_feats=None):
        eps = 1e-8

        # ======================================
        # TEXT BRANCH
        # ======================================
        text_repr, attention_scores = self.encode_text(x)

        # ======================================
        # GLOBAL TEXTUAL FEATURES BRANCH
        # ======================================

        if case_feats is not None:
            feat_repr, feature_gates = (self.encode_features(case_feats))
        else:
            feat_repr = None
            feature_gates = None

        # ======================================
        # FULL PREDICTION
        # ======================================
        fused = self.fuse(text_repr, feat_repr)
        pred = self.predict_from_repr(fused)

        # ======================================
        # BRANCH CONTRIBUTION VIA ABLATION
        # ======================================
        if feat_repr is not None:
            zero_feat = torch.zeros_like(feat_repr)
            fused_text_only = self.fuse(text_repr, zero_feat)
            pred_text_only = self.predict_from_repr(fused_text_only)

            zero_text = torch.zeros_like(text_repr)
            fused_feat_only = self.fuse(zero_text, feat_repr)
            pred_feat_only = self.predict_from_repr(fused_feat_only)

            text_delta = torch.abs(pred - pred_feat_only)
            feat_delta = torch.abs(pred - pred_text_only)
            total_delta = (torch.abs(text_delta) + torch.abs(feat_delta) + eps)

            text_importance = (text_delta / total_delta)
            handcrafted_importance = (feat_delta / total_delta)
            text_importance = text_importance.clamp(0, 1)
            handcrafted_importance = handcrafted_importance.clamp(0, 1)
        else:
            text_importance = torch.tensor(1.0, device=x.device)
            handcrafted_importance = torch.tensor(0.0, device=x.device)

        return (
            pred,
            attention_scores,
            feature_gates,
            text_importance,
            handcrafted_importance
        )

class ModelManager:
    def __init__(self):
        self.loaded_models = {}
        self.loaded_scalers = {}
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

    def get_assets(self, config):
        cfg_id = config['config_id']

        if cfg_id not in self.loaded_models:
            
            scaler = None
            if config.get('scaler_path'):
                scaler = joblib.load(config['scaler_path'])
            self.loaded_scalers[cfg_id] = scaler

            model = AttentionMIL(
                input_dim=config['input_dim'],
                case_feat_dim=32,
                fusion_type=config.get('fusion_type', 'gated'),
                mode=config.get('task', 'classification')
            )

            checkpoint = torch.load(config['checkpoint_path'], map_location=self.device)
            state_dict = checkpoint.get('model_state_dict', checkpoint)

            model.load_state_dict(state_dict)
            model.to(self.device).eval()
            self.loaded_models[cfg_id] = model
        
        return self.loaded_models[cfg_id], self.loaded_scalers[cfg_id]

    def run_inference(self, config, embeddings, ordered_features=None):
        model, scaler = self.get_assets(config)

        feat_tensor = None
        if scaler and ordered_features:
            print(f"RAW FEATURES: {ordered_features}")
            scaled = scaler.transform([ordered_features])
            print(f"SCALED FEATURES: {scaled[0]}")
            feat_tensor = torch.tensor(scaled[0], dtype=torch.float32).to(self.device)
            

        emb_tensor = torch.tensor(embeddings, dtype=torch.float32).to(self.device)
        print(f"EMBEDDING SHAPE: {emb_tensor.shape}")

        with torch.no_grad():
            pred, attn, gates, text_imp, feat_imp = model(emb_tensor, case_feats=feat_tensor)
        
        score = round(float(pred.item()), 4)

        print(f"FINAL SCORE: {score}")
        print(f"--- DEBUG: INFERENCE END ---\n")
        return {
            "score": score,
            "label": "High Impact" if score >= 0.5 else "Low Impact",
            
            "attention": attn.squeeze().cpu().numpy().tolist(),
            
            "feature_gates": gates.squeeze().cpu().numpy().tolist() if gates is not None else [],
            
            "narrative_contribution": round(float(text_imp.item()), 4),
            "feature_contribution": round(float(feat_imp.item()), 4)
        }

inference_engine = ModelManager()