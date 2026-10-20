# Evaluation environment on NCSA DeltaAI. `source eval/env.sh` before any eval command.
# PyTorch module 2.10.0 (CUDA 12.9). Compute nodes run driver 595, so 2.11/2.12 (CUDA 13)
# would also load there; 2.10.0 is pinned because the scores were produced with it.
module load python/miniforge3_pytorch/2.10.0 >/dev/null 2>&1
export FAIRDEEP_EVAL_ENV=/projects/bjej/rahamed/fairdeep_eval
export PATH="$FAIRDEEP_EVAL_ENV/venv/bin:$PATH"                  # venv on top of the module
export FAIRDEEP_FFMPEG="$FAIRDEEP_EVAL_ENV/ffmpeg/bin/ffmpeg"     # conda-forge ffmpeg 7.1.1, pinned
export FAIRDEEP_FFPROBE="$FAIRDEEP_EVAL_ENV/ffmpeg/bin/ffprobe"
export FAIRDEEP_EXT=/work/nvme/bjej/rahamed/fairdeep/eval_ext     # external code checkouts
export FAIRDEEP_WEIGHTS="$FAIRDEEP_EXT/weights"                   # DeCoF.tar, CLIP, YuNet
export FAIRDEEP_VIEWS_ROOT=/work/nvme/bjej/rahamed/fairdeep/eval_views
export HF_HOME=/work/nvme/bjej/rahamed/fairdeep/hf_home
export PYTHONNOUSERSITE=1
