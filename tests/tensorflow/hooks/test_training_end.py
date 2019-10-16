from .utils import *
from tornasole.tensorflow import reset_collections
import tensorflow as tf
from tornasole.core.access_layer.utils import has_training_ended
import shutil
import os
import sys
import subprocess
import pytest


@pytest.mark.slow  # 0:03 to run
def test_training_job_has_ended():
    tf.reset_default_graph()
    reset_collections()
    run_id = "trial_" + datetime.now().strftime("%Y%m%d-%H%M%S%f")
    trial_dir = os.path.join(TORNASOLE_TF_HOOK_TESTS_DIR, run_id)
    subprocess.check_call(
        [
            sys.executable,
            "examples/tensorflow/scripts/simple.py",
            "--tornasole_path",
            trial_dir,
            "--steps",
            "10",
            "--tornasole_frequency",
            "5",
        ],
        env={"CUDA_VISIBLE_DEVICES": "-1", "TORNASOLE_LOG_LEVEL": "debug"},
    )
    assert has_training_ended(trial_dir) == True
    shutil.rmtree(trial_dir)
