"""XCLIP_DeMamba, inference only.

Taken from our standalone evaluator for Ahsanz/DeMamba-GenVideo100K (eval_demamba_standalone.py),
which re-implements the authors' models/DeMamba.py + models/mamba_base.py + models/pscan.py
(github.com/chenhaoxing/DeMamba; pure-PyTorch Mamba from alxndrTL/mamba.py) with the training-only
parts removed. The X-CLIP-B/16 vision tower is built from its config; all weights, including the
fine-tuned encoder, come from the checkpoint.
"""
import math
from dataclasses import dataclass
from typing import Union

import torch
import torch.nn as nn
import torch.nn.functional as F

XCLIP_CFG = dict(
    hidden_size=768, intermediate_size=3072, num_hidden_layers=12, num_attention_heads=12,
    mit_hidden_size=512, mit_intermediate_size=2048, mit_num_hidden_layers=1,
    mit_num_attention_heads=8, image_size=224, patch_size=16, num_frames=8,
    hidden_act="quick_gelu", layer_norm_eps=1e-5, attention_dropout=0.0, dropout=0.0,
    drop_path_rate=0.0,
)


# ---------------------------------------------------------------- parallel scan (Blelloch)
def _npo2(n):
    return 2 ** math.ceil(math.log2(n))


def _pscan_inplace(A, X):
    # A, X: (B, D, L, N), L a power of two; computes H[t] = A[t] * H[t-1] + X[t] into X
    B, D, L, _ = A.size()
    num_steps = int(math.log2(L))

    Aa, Xa = A, X
    for _ in range(num_steps - 2):
        T = Xa.size(2)
        Aa = Aa.view(B, D, T // 2, 2, -1)
        Xa = Xa.view(B, D, T // 2, 2, -1)
        Xa[:, :, :, 1].add_(Aa[:, :, :, 1].mul(Xa[:, :, :, 0]))
        Aa[:, :, :, 1].mul_(Aa[:, :, :, 0])
        Aa = Aa[:, :, :, 1]
        Xa = Xa[:, :, :, 1]

    if Xa.size(2) == 4:
        Xa[:, :, 1].add_(Aa[:, :, 1].mul(Xa[:, :, 0]))
        Aa[:, :, 1].mul_(Aa[:, :, 0])
        Xa[:, :, 3].add_(Aa[:, :, 3].mul(Xa[:, :, 2] + Aa[:, :, 2].mul(Xa[:, :, 1])))
    elif Xa.size(2) == 2:
        Xa[:, :, 1].add_(Aa[:, :, 1].mul(Xa[:, :, 0]))
        return
    else:
        return

    Aa = A[:, :, 2 ** (num_steps - 2) - 1:L:2 ** (num_steps - 2)]
    Xa = X[:, :, 2 ** (num_steps - 2) - 1:L:2 ** (num_steps - 2)]
    Xa[:, :, 2].add_(Aa[:, :, 2].mul(Xa[:, :, 1]))
    Aa[:, :, 2].mul_(Aa[:, :, 1])

    for k in range(num_steps - 3, -1, -1):
        Aa = A[:, :, 2 ** k - 1:L:2 ** k]
        Xa = X[:, :, 2 ** k - 1:L:2 ** k]
        T = Xa.size(2)
        Aa = Aa.view(B, D, T // 2, 2, -1)
        Xa = Xa.view(B, D, T // 2, 2, -1)
        Xa[:, :, 1:, 0].add_(Aa[:, :, 1:, 0].mul(Xa[:, :, :-1, 1]))
        Aa[:, :, 1:, 0].mul_(Aa[:, :, :-1, 1])


def pscan(A_in, X_in):
    # (B, L, D, N) -> (B, L, D, N)
    L = X_in.size(1)
    if L == _npo2(L):
        A, X = A_in.clone(), X_in.clone()
    else:
        pad = (0, 0, 0, 0, 0, _npo2(L) - L)
        A, X = F.pad(A_in, pad), F.pad(X_in, pad)
    A, X = A.transpose(2, 1), X.transpose(2, 1)
    _pscan_inplace(A, X)
    return X.transpose(2, 1)[:, :L]


# ---------------------------------------------------------------- Mamba block
@dataclass
class MambaConfig:
    d_model: int = 768
    dt_rank: Union[int, str] = "auto"
    d_state: int = 16
    expand_factor: int = 2
    d_conv: int = 4
    lin_b: bool = False         # nn.Linear additive term in in/out projections
    conv_b: bool = True         # same for the depthwise convs
    bimamba: bool = True

    def __post_init__(self):
        self.d_inner = self.expand_factor * self.d_model
        if self.dt_rank == "auto":
            self.dt_rank = math.ceil(self.d_model / 16)


class RMSNorm(nn.Module):
    def __init__(self, d_model, eps=1e-5):
        super().__init__()
        self.eps = eps
        self.weight = nn.Parameter(torch.ones(d_model))

    def forward(self, x):
        return x * torch.rsqrt(x.pow(2).mean(-1, keepdim=True) + self.eps) * self.weight


class MambaBlock(nn.Module):
    def __init__(self, c: MambaConfig):
        super().__init__()
        self.config = c
        # Linear/Conv1d additive terms passed positionally (in, out, flag) /
        # (in, out, k, stride, padding, dilation, groups, flag)
        self.in_proj = nn.Linear(c.d_model, 2 * c.d_inner, c.lin_b)
        self.conv1d = nn.Conv1d(c.d_inner, c.d_inner, c.d_conv, 1, c.d_conv - 1, 1, c.d_inner, c.conv_b)
        self.x_proj = nn.Linear(c.d_inner, c.dt_rank + 2 * c.d_state, False)
        self.dt_proj = nn.Linear(c.dt_rank, c.d_inner, True)
        self.A_log = nn.Parameter(torch.zeros(c.d_inner, c.d_state))
        self.D = nn.Parameter(torch.ones(c.d_inner))
        self.out_proj = nn.Linear(c.d_inner, c.d_model, c.lin_b)
        self.bimamba = c.bimamba
        if self.bimamba:
            self.A_b_log = nn.Parameter(torch.zeros(c.d_inner, c.d_state))
            self.conv1d_b = nn.Conv1d(c.d_inner, c.d_inner, c.d_conv, 1, c.d_conv - 1, 1,
                                      c.d_inner, c.conv_b)
            self.x_proj_b = nn.Linear(c.d_inner, c.dt_rank + 2 * c.d_state, False)
            self.dt_proj_b = nn.Linear(c.dt_rank, c.d_inner, True)
            self.D_b = nn.Parameter(torch.ones(c.d_inner))

    def forward(self, x):
        _, L, _ = x.shape
        x, z = self.in_proj(x).chunk(2, dim=-1)
        x = self.conv1d(x.transpose(1, 2))[:, :, :L].transpose(1, 2)
        y = self.ssm(F.silu(x))
        return self.out_proj(y * F.silu(z))

    def _scan(self, x, x_proj, dt_proj, A_log, D):
        c = self.config
        A = -torch.exp(A_log.float())
        delta, B, C = torch.split(x_proj(x), [c.dt_rank, c.d_state, c.d_state], dim=-1)
        delta = F.softplus(dt_proj(delta))
        deltaA = torch.exp(delta.unsqueeze(-1) * A)
        BX = delta.unsqueeze(-1) * B.unsqueeze(2) * x.unsqueeze(-1)
        hs = pscan(deltaA, BX)
        return (hs @ C.unsqueeze(-1)).squeeze(3) + D.float() * x

    def ssm(self, x):
        y = self._scan(x, self.x_proj, self.dt_proj, self.A_log, self.D)
        if self.bimamba:
            # the original flips the channel dim (-1), not time; kept as trained
            x_b = x.flip([-1])
            y_b = self._scan(x_b, self.x_proj_b, self.dt_proj_b, self.A_b_log, self.D_b)
            y = y + y_b.flip([-1])
        return y


class ResidualBlock(nn.Module):
    def __init__(self, c: MambaConfig):
        super().__init__()
        self.mixer = MambaBlock(c)
        self.norm = RMSNorm(c.d_model)

    def forward(self, x):
        return self.mixer(self.norm(x)) + x      # DropPath is identity at eval


# ---------------------------------------------------------------- XCLIP_DeMamba
def reorder_data(data, N):
    new_order = []
    for col in range(N):
        if col % 2 == 0:
            new_order.extend(range(col, N * N, N))
        else:
            new_order.extend(range(col + N * (N - 1), col - 1, -N))
    new_order = torch.tensor(new_order, device=data.device)
    B, t, _, _ = data.shape
    index = new_order.repeat(B, t, 1).unsqueeze(-1)
    return torch.gather(data, 2, index.expand_as(data))


class XCLIP_DeMamba(nn.Module):
    def __init__(self, class_num=1):
        super().__init__()
        from transformers import XCLIPVisionConfig, XCLIPVisionModel
        self.encoder = XCLIPVisionModel(XCLIPVisionConfig(**XCLIP_CFG))
        channel = 768
        self.fusing_ratios = 1
        self.patch_nums = (14 // self.fusing_ratios) ** 2
        self.mamba = ResidualBlock(MambaConfig(d_model=channel))
        self.fc1 = nn.Linear((self.patch_nums + 1) * channel, class_num)
        self.fc_norm = nn.LayerNorm(self.patch_nums * channel)
        self.fc_norm2 = nn.LayerNorm(768)

    def forward(self, x):
        # (B, T, 3, H, W) -> logits (B, 1)
        b, t, _, h, w = x.shape
        outputs = self.encoder(x.view(b * t, 3, h, w), output_hidden_states=False)
        seq = outputs["last_hidden_state"][:, 1:, :]
        c = seq.shape[-1]

        global_feat = self.fc_norm2(outputs["pooler_output"].reshape(b, t, -1).mean(1))

        seq = seq.view(b, t, -1, c)
        s = int(math.sqrt(seq.shape[2])) // self.fusing_ratios
        seq = seq.view(b, t, self.fusing_ratios, s, self.fusing_ratios, s, c)
        x = seq.permute(0, 2, 4, 1, 3, 5, 6).contiguous().view(b * s * s, t, -1, c)
        x = reorder_data(x, self.fusing_ratios)
        x = x.permute(0, 2, 1, 3).contiguous().view(b * s * s, -1, c)
        res = self.mamba(x)

        feats = self.fc_norm(res.mean(1).view(b, -1))
        return self.fc1(torch.cat((global_feat, feats), dim=1))


def load_checkpoint(model, path):
    """Strict load: strips DataParallel's `module.` and maps between the transformers 4.x
    (`encoder.vision_model.*`) and 5.x (`encoder.*`) key layouts. Returns the epoch."""
    state = torch.load(path, map_location="cpu", weights_only=True)
    sd = state.get("model_state_dict", state)
    sd = {(k[len("module."):] if k.startswith("module.") else k): v for k, v in sd.items()}
    model_keys = set(model.state_dict())
    if not set(sd) <= model_keys:
        remapped = {}
        for k, v in sd.items():
            if k.startswith("encoder.vision_model."):
                k = "encoder." + k[len("encoder.vision_model."):]
            elif k.startswith("encoder."):
                k = "encoder.vision_model." + k[len("encoder."):]
            remapped[k] = v
        if set(remapped) <= model_keys:
            sd = remapped
    missing, unexpected = model.load_state_dict(sd, strict=False)
    missing = [k for k in missing if not k.endswith("position_ids")]
    if missing or unexpected:
        raise RuntimeError(f"checkpoint does not match model; missing {missing[:10]}, "
                           f"unexpected {unexpected[:10]}")
    return state.get("epoch")
