# Defines the trained attention-based multiple-instance learning model architecture.

import torch


class AttentionMIL(torch.nn.Module):
    def __init__(
        self,
        input_dim: int,
        hidden_dim: int = 128,
        output_dim: int = 1,
        mode: str = "classification",
        case_feat_dim: int | None = None,
        fusion_type: str = "gated",
    ):
        super().__init__()
        self.mode = mode
        self.case_feat_dim = case_feat_dim
        self.fusion_type = fusion_type

        self.attention = torch.nn.Sequential(
            torch.nn.Linear(input_dim, hidden_dim),
            torch.nn.Tanh(),
            torch.nn.Linear(hidden_dim, 1),
        )
        self.sentence_proj = torch.nn.Linear(input_dim, hidden_dim)

        if case_feat_dim is not None:
            self.feature_gate = torch.nn.Sequential(
                torch.nn.Linear(case_feat_dim, hidden_dim),
                torch.nn.ReLU(),
                torch.nn.Linear(hidden_dim, case_feat_dim),
            )
            self.case_mlp = torch.nn.Sequential(
                torch.nn.Linear(case_feat_dim, hidden_dim),
                torch.nn.ReLU(),
                torch.nn.Dropout(0.2),
                torch.nn.Linear(hidden_dim, hidden_dim),
            )

        if case_feat_dim is None:
            self.classifier = torch.nn.Sequential(
                torch.nn.ReLU(),
                torch.nn.Linear(hidden_dim, output_dim),
            )
        elif fusion_type == "gated":
            self.gate = torch.nn.Sequential(
                torch.nn.Linear(hidden_dim * 2, hidden_dim),
                torch.nn.Sigmoid(),
            )
            self.classifier = torch.nn.Sequential(
                torch.nn.ReLU(),
                torch.nn.Linear(hidden_dim, output_dim),
            )
        else:
            self.classifier = torch.nn.Sequential(
                torch.nn.ReLU(),
                torch.nn.Linear(hidden_dim * 2, output_dim),
            )

    def encode_text(self, embeddings: torch.Tensor) -> tuple[torch.Tensor, torch.Tensor]:
        attention_scores = torch.softmax(self.attention(embeddings), dim=0)
        text_repr = torch.sum(attention_scores * embeddings, dim=0, keepdim=True)
        return self.sentence_proj(text_repr), attention_scores

    def encode_features(self, case_features: torch.Tensor) -> tuple[torch.Tensor, torch.Tensor]:
        gate_logits = self.feature_gate(case_features)
        feature_gates = torch.sigmoid(gate_logits)
        gated_features = feature_gates * case_features
        return self.case_mlp(gated_features), feature_gates

    def fuse(
        self,
        text_repr: torch.Tensor,
        feature_repr: torch.Tensor | None,
    ) -> torch.Tensor:
        if feature_repr is None:
            return text_repr

        if text_repr.dim() == 1:
            text_repr = text_repr.unsqueeze(0)
        if feature_repr.dim() == 1:
            feature_repr = feature_repr.unsqueeze(0)

        if self.fusion_type == "gated":
            fusion = torch.cat([text_repr, feature_repr], dim=-1)
            gate = self.gate(fusion)
            fused = gate * text_repr + (1 - gate) * feature_repr
        else:
            fused = torch.cat([text_repr, feature_repr], dim=-1)

        return fused.squeeze(0)

    def predict_from_repr(self, fused_repr: torch.Tensor) -> torch.Tensor:
        output = self.classifier(fused_repr)
        if self.mode == "classification":
            return torch.sigmoid(output)
        return output

    def forward(
        self,
        embeddings: torch.Tensor,
        case_features: torch.Tensor | None = None,
    ) -> tuple[torch.Tensor, torch.Tensor, torch.Tensor | None, torch.Tensor, torch.Tensor]:
        eps = 1e-8
        text_repr, attention_scores = self.encode_text(embeddings)

        if case_features is not None:
            feature_repr, feature_gates = self.encode_features(case_features)
        else:
            feature_repr = None
            feature_gates = None

        fused = self.fuse(text_repr, feature_repr)
        prediction = self.predict_from_repr(fused)

        if feature_repr is not None:
            zero_feature = torch.zeros_like(feature_repr)
            text_only = self.predict_from_repr(self.fuse(text_repr, zero_feature))

            zero_text = torch.zeros_like(text_repr)
            feature_only = self.predict_from_repr(self.fuse(zero_text, feature_repr))

            text_delta = torch.abs(prediction - feature_only)
            feature_delta = torch.abs(prediction - text_only)
            total_delta = torch.abs(text_delta) + torch.abs(feature_delta) + eps

            text_importance = (text_delta / total_delta).clamp(0, 1)
            feature_importance = (feature_delta / total_delta).clamp(0, 1)
        else:
            text_importance = torch.tensor(1.0, device=embeddings.device)
            feature_importance = torch.tensor(0.0, device=embeddings.device)

        return (
            prediction,
            attention_scores,
            feature_gates,
            text_importance,
            feature_importance,
        )
