# Standard Library
from enum import Enum

# Third Party
import tensorflow as tf
from tensorflow.python.distribute import values

# First Party
from tornasole.core.logger import get_logger

logger = get_logger()


def get_tf_names(arg):
    if isinstance(arg, tf.Variable):
        tf_names = [arg.name]
    elif isinstance(arg, tf.Tensor):
        tf_names = [arg.name]
    elif isinstance(arg, values.MirroredVariable):
        tf_names = [v.name for v in arg._values]
    else:
        raise NotImplementedError
    return tf_names


class TensorType(Enum):
    REGULAR = 1
    REDUCTION = 2
    SUMMARY = 3
    VARIABLE = 4
    NON_GRAPH = 5


class TensorRef:
    """
    This method allows us to save additional information for a tf.Tensor.

    Sometimes we want to save tensor with different name than the direct TF tensor.
    This happens when we save Variables for example, especially in Keras.
    The tensor we want to save in that case is variable.value(), whose name is weird and non descriptive.
    So we use the variable's name then.

    This also lets us identify the type of tensor, i.e.reduction or summary.
    While saving, we need to identify what the original tensor for these tensors are.
    This class encapsulates that info.

    The tensor_to_collections object in hook is a mapping from tf_name to tf.Tensor
    hook._get_tensor_ref() can be used to fetch the tornasole.Tensor object for that tensor.
    """

    def __init__(
        self, tf_obj, export_name=None, type=TensorType.REGULAR, original_tensor=None, mode=None
    ):
        self.tf_obj = tf_obj
        self.name = tf_obj.name if tf_obj is not None else None
        self.export_name = self.name if export_name is None else export_name

        # for non graph var tensor
        if tf_obj is None:
            self.name = self.export_name

        assert self.export_name is not None

        self.modes = {mode}

        self.type = type
        if self.type in [TensorType.REDUCTION, TensorType.SUMMARY, TensorType.VARIABLE]:
            assert original_tensor is not None
            self.original_tensor = original_tensor
        else:
            self.original_tensor = None

        # if self.type == TensorType.VARIABLE:
        #     self.variable_value = self.tf_obj.value()
        # else:
        #     self.variable_value = None

    def add_mode(self, mode):
        self.modes.add(mode)

    @classmethod
    def from_tensor(cls, tensor, export_name=None, mode=None):
        try:
            if export_name is None:
                export_name = tensor.name
            return TensorRef(tensor, export_name=export_name, mode=mode)
        except AttributeError:
            logger.debug(
                f"Could not create TensorRef from {tensor}. " "Perhaps eager mode is turned on"
            )
            return None

    @classmethod
    def from_variable(cls, variable, export_name=None, mode=None, original_tensor=None):
        try:
            if export_name is None:
                export_name = variable.name

            if original_tensor is None:
                # normal variable, this will be none.
                # for mirrored variable value this will be the mirrored variable
                original_tensor = variable

            return TensorRef(
                variable,  # .value(),
                export_name=export_name,
                type=TensorType.VARIABLE,
                original_tensor=original_tensor,
                mode=mode,
            )
        except AttributeError:
            logger.debug(
                f"Could not create TensorRef from {variable}. " "Perhaps eager mode is turned on"
            )
            return None

    @classmethod
    def from_non_graph_var(cls, export_name):
        # to create a tensor variable from non graph variables
        # such as losses, metrics in keras
        return TensorRef(None, type=TensorType.NON_GRAPH, export_name=export_name)

    @classmethod
    def create_reduction(cls, tensor, original_tensor, export_name=None):
        # only used by TF session/estimator
        try:
            if export_name is None:
                export_name = tensor.name
            return TensorRef(
                tf_obj=tensor,
                export_name=export_name,
                type=TensorType.REDUCTION,
                original_tensor=original_tensor,
            )
        except AttributeError:
            logger.debug(
                f"Could not create reduction {tensor} of {original_tensor}."
                "Perhaps eager mode is turned on"
            )
            return None