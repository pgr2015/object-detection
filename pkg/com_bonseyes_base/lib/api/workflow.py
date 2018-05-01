"""

Workflow definition objects.

This module contains classes that can be used to represent a parsed YAML
workflow file in memory. The classes represent what has been written by
the workflow author and do not try to evaluate the dynamic expressions
the author has written in the workflow.

"""

from typing import Dict, Union

from . import expressions

from .manifest import Parameter
from .storage import StorableObject
from .utils import NamedDataView, NamedObjectMap, create_data_views_from_dict, \
    create_data_views_from_list, OrderedNamedObjectList, OrderedNamedDataView


class OutputDescription(NamedDataView):
    """
    Description of outputs of a workflow

    This is declares what the yield steps in the workflow can return
    """

    @property
    def label(self) -> str:
        """
        Human readable text describing the output

        :returns: a string describing the output
        """
        return self._data.get('label')


class OutputAssignment(NamedDataView):
    """
    Used in a yield step to assign an artifact to an output
    """

    @property
    def worker_name(self) -> str:
        """
        Name of the worker that contains the output or none if the step_name points to
        a step

        :returns: the name of the worker
        """
        return self._data.get('worker')

    @property
    def artifact_name(self) -> Union[str, None]:
        """
        Name of the artifact that contains the output or none if the output points to the worker
        or the step name points to a step

        :returns: the name of the artifact or None
        """
        return self._data.get('artifact')

    @property
    def step_name(self) -> Union[str, None]:
        """
        Name of the step that contains the output or none if the output points to the worker
        or the worker and artifact names are not null.

        :returns: the name of the artifact or None
        """
        return self._data.get('artifact')


class ArgumentDescription(NamedDataView):
    """
    Description on what to pass as argument to a worker.

    This is used in the workflow steps that instruct the executor to
    create an artifact to describe what should be passed as argument.
    """

    @property
    def expression(self) -> 'expressions.Expression':
        """
        Expression that once evaluated returns the value of the argument.

        This expression can be evaluated to obtain the actual value that should
        be sent to the worker when executing a step.

        :returns: expression that once evaluated is the value of the argument
                  that need to be passed to the worker.
        """
        return expressions.create_expression(self._data)


class WorkerDescription(NamedDataView):
    """
    Description on how to instantiate a worker used in a workflow.

    Each workflow execution starts by instantiating a set of workers
    (instances of tools). This object represents the description of
    the worker in the workflow.
    """

    @property
    def expression(self) -> 'expressions.Expression':
        """
        Expression that once resolved returns instantiation information.

        This field returns an expression that once evaluated returns
        a plain object containing all the required information on how to
        instantiate the worker.

        :returns: expression that once evaluated provides instructions on
          how to instantiate worker
        """
        return expressions.Map(None, self._data)


class StepDescription(OrderedNamedDataView):
    """
    Description of a step contained in a workflow.

    Each workflow contains a list of steps descriptions. Each step description
    allows to instruct the executor to perform one action. Action can be either
    to create an artifact on a worker or yield some outputs and suspend the workflow
    execution.
    """

    def __init__(self, index: int, data: Dict) -> None:
        """
        Creates a step description from its YAML data

        :param index: the index of the step in the workflow YAML "steps" section
        :param data: the YAML parsed data in the "steps" section corresponding to this step
        """
        super().__init__(index, data)
        self._validate()

    @property
    def worker_name(self) -> str:
        """
        Name of the worker that needs to be used by this step.

        This property is None if the step instructs the executor to suspend execution.

        :returns: name of the worker used for the step, None if wait step
        """
        return self._data.get('worker', None)

    @property
    def artifact_name(self) -> str:
        """
        Name of the artifact that this step will create

        This property is None if the step instructs the executor to suspend execution.

        :returns: name of the artifact that will be created, None if wait step
        """
        return self._data.get('artifact', self._data.get('name', None))

    @property
    def arguments(self) -> NamedObjectMap[ArgumentDescription]:
        """
        List of arguments that should be sent to the worker when creating the artifact.

        This list is empty if the step instructs the executor to suspend execution.

        :returns: list of arguments that need to be passed to the worker
        """
        return create_data_views_from_dict(self._data.get('parameters', {}), ArgumentDescription)

    @property
    def outputs(self) -> NamedObjectMap[OutputAssignment]:
        """
        List of output assignments done by this step

        :returns: list of OutputAssignment objects
        """
        return create_data_views_from_dict(self._data.get('outputs', {}), OutputAssignment)

    @property
    def output(self) -> str:
        """
        Output where the artifact produced by this step should be stored

        This is not valid for wait steps.

        :returns: name of the workflow output.
        """
        return self._data.get('output', None)

    @property
    def description(self) -> str:
        """
        Human readable description of the step

        :returns: description of the step
        """
        return self._data.get('description', None)

    @property
    def is_wait(self) -> bool:
        """
        This property is true if the step instructs the executor to suspend the execution

        :returns: True if the step suspends execution, False otherwise
        """

        return 'wait' in self._data

    def _validate(self):
        if self.is_wait:

            if self.worker_name is not None:
                raise ValueError('Cannot have worker name in wait step ' + str(self.index))

            if self.artifact_name is not None:
                raise ValueError('Cannot have artifact name in wait step ' + str(self.index))

            if self.output is not None:
                raise ValueError('Cannot have output in wait step ' + str(self.index))

        else:

            if self.worker_name is None:
                raise ValueError('Missing worker name in step ' + str(self.index))

            if self.artifact_name is None:
                raise ValueError('Missing artifact name in step ' + str(self.index))


class Workflow(StorableObject):
    """
    The Workflow object represents the parsed YAML workflow file.

    It contains a set of step descriptions that need to be executed. Each step
     description either creates a new artifact or suspends the execution.

    The workflow also contains set of worker descriptions that are used to start
    the workers. The description can be for example a manifest that describes how
    to start a fresh copy of a tool or a reference to an existing tool that needs
    to be cloned.

    Each step can generate an artefact using one of the tools instantiated using
    the worker descriptions.

    Finally a workflow may have a list of parameters that need to be provided when
    the workflow is started and can be used to customize the workflow execution.
    """

    def __init__(self, data: Dict) -> None:
        """
        Creates a new workflow from the parsed YAML data stored in dict

        :param data: the workflow data parsed with YAML
        """
        self._data = data

    @property
    def workers(self) -> NamedObjectMap[WorkerDescription]:
        """
        Returns a list of worker descriptions for the workers that need to be instantiated
        to execute this workflow.

        :returns: list of workers descriptions
        """
        return create_data_views_from_dict(self._data.get('workers', {}), WorkerDescription)

    @property
    def steps(self) -> OrderedNamedObjectList[StepDescription]:
        """
        Returns a list of steps descriptions for the steps the executor needs to execute to
        carry out this workflow.

        :returns: list of step descriptions
        """
        return create_data_views_from_list(self._data.get('steps', []), StepDescription)

    @property
    def parameters(self) -> NamedObjectMap[Parameter]:
        """
        Returns a list of parameters that need to be provided to execute this workflow.

        :returns: list of parameters of the workflow
        """
        return create_data_views_from_dict(self._data.get('parameters', {}), Parameter)

    @property
    def outputs(self) -> NamedObjectMap[OutputDescription]:
        """
        Returns the list of descriptions of outputs produced by this workflow.

        :returns: list of outputs of the workflow
        """
        return create_data_views_from_dict(self._data.get('outputs', {}), OutputDescription)

    def to_dict(self) -> Dict:
        """
        Returns the raw parsed data representing the workflow

        :return: a dictionary containing the YAML data from which the workflow has been parsed
        """
        return self._data
