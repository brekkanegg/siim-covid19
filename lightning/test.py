"""
1. pytorch naive reproduce [x]
3. apply Pytorch-Lightning
2. boilerplate.ipynb
4. apply mlflow
5. apply torch-serve
"""

import argparse
import numpy as np
import random
import torch
import pytorch_lightning as pl
import torch.multiprocessing

from lit_model import LitModel
from inputs.cxr_dm import CXRDataModule

# import mlflow.pytorch
from callbacks import froc, visualizer


def main(cfg):

    # tb_logger = pl.loggers.TensorBoardLogger(save_dir=cfg.weights_save_path)  # name=''

    trainer = pl.Trainer(
        logger=False,  # mlf_logger,  #
        default_root_dir=cfg.default_root_dir,
        num_nodes=cfg.num_nodes,
        num_processes=1,
        gpus=cfg.gpus,
        auto_select_gpus=False,
        track_grad_norm=cfg.track_grad_norm,
        limit_train_batches=1.0,  # FIXME:  epoch_division
        limit_val_batches=1.0,
        limit_test_batches=1.0,
        progress_bar_refresh_rate=1,  # FIXME:
        accelerator=cfg.accelerator,
        sync_batchnorm=cfg.sync_batchnorm,
        precision=cfg.precision,
        weights_summary="top",
        profiler=cfg.profiler,
        benchmark=cfg.benchmark,
        deterministic=cfg.deterministic,
        amp_backend="native",
        amp_level="O2",
    )

    cxrdm = CXRDataModule(cfg)
    # model = LitModel(cfg)
    model = LitModel.load_from_checkpoint(cfg.ckpt_path)
    trainer.test(model, datamodule=cxrdm)


if __name__ == "__main__":

    parser = argparse.ArgumentParser()

    # Path
    parser.add_argument("--ckpt_path", "--ckpt", type=str, required=True)
    parser.add_argument("--default_root_dir", "--root_dir", type=str, default=None)
    parser.add_argument("--data_dir", type=str, default="/nfs3/chestpa/png_1024")

    # Resource
    parser.add_argument("--gpus", "--g", type=str, default="0")
    parser.add_argument("--num_nodes", "--nn", type=int, default=1)
    parser.add_argument("--num_workers", "--nw", type=int, default=2)
    parser.add_argument("--benchmark", action="store_true")
    parser.add_argument("--deterministic", action="store_false")

    # Accelerator
    parser.add_argument("--precision", type=int, default=32)  # 32
    parser.add_argument("--accelerator", type=str, default=None)  # 'ddp'
    parser.add_argument("--sync_batchnorm", action="store_true")  # 'ddp'

    # Debug
    parser.add_argument("--debug", action="store_true")
    parser.add_argument("--fast_dev_run", type=int, default=0)
    parser.add_argument("--track_grad_norm", type=int, default=-1)
    parser.add_argument("--overfit_batches", type=float, default=0.0)  # 0.01
    parser.add_argument("--profiler", type=str, default=None)  # 'simple'

    # Data
    parser.add_argument("--fold_index", "--fold", type=int, default=1)
    parser.add_argument("--batch_size", "--batch", type=int, default=3)
    parser.add_argument("--auto_scale_batch_size", action="store_true")
    parser.add_argument("--image_size", type=int, default=768)
    parser.add_argument("--neg_ratio", "--neg", type=float, default=1.0)
    parser.add_argument("--label_smoothing", "--smooth", type=float, default=0.1)

    # Opts
    parser.add_argument("--auto_lr_find", action="store_true")
    parser.add_argument("--lr", type=float, default=7e-5)
    parser.add_argument("--weight_value", type=float, default=10.0)

    # Train
    parser.add_argument("--resume_from_checkpoint", "--resume", type=str, default=None)
    parser.add_argument("--max_epochs", "--max_ep", type=int, default=300)
    parser.add_argument("--stochastic_weight_avg", "--swa", action="store_true")
    parser.add_argument("--limit_train_batches", type=float, default=0.5)

    # Validation
    parser.add_argument("--check_val_every_n_epoch", type=int, default=1)

    # Etc
    parser.add_argument("--plugins", type=str, default=None)
    parser.add_argument("--logger", type=str, default=True)
    parser.add_argument("--logging_batch_interval", type=int, default=300)

    cfg = parser.parse_args()

    cfg.gpus = [int(g) for g in cfg.gpus.split(",")]  # right format: [0], [2,3,4]

    if cfg.data_dir != "/nfs3/chestpa/png_1024":
        print("Warning!: Data directory for test should be /nfs3/chestpa/png_1024!")

    # DEBUG:
    if cfg.debug:
        cfg.fast_dev_run = 20
        cfg.track_grad_norm = 2
        cfg.profiler = "simple"

    # DDP:
    if cfg.accelerator == "ddp":
        assert len(cfg.gpus) > 1
        cfg.sync_batchnorm = True
        cfg.plugins = "ddp_sharded"

    random.seed(52)
    np.random.seed(52)
    torch.random.manual_seed(52)

    torch.multiprocessing.set_sharing_strategy("file_system")

    main(cfg)
