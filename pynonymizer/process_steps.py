from enum import Enum


class ProcessSteps(Enum):
    START = 0
    CREATE_DB = 200
    RESTORE_DB = 300
    ANONYMIZE_DB = 400
    DUMP_DB = 500
    DROP_DB = 600
    END = 9999

    @staticmethod
    def names():
        return [step.name for step in ProcessSteps]

    @staticmethod
    def from_value(step_value):
        """
        resolve a enum value from key (case insensitive)
        :return: ProcessSteps property
        """
        # Try to resolve as a string value
        return ProcessSteps[step_value.upper()]


class SkipReason:
    pass


class StepBeforeStartReason(SkipReason):
    def __init__(self, start_at_step):
        self.start_at_step = start_at_step

    def __str__(self):
        return "Starting at [{}]".format(self.start_at_step.name)


class StepAfterStopReason(SkipReason):
    def __init__(self, stop_at_step):
        self.stop_at_step = stop_at_step

    def __str__(self):
        return "Stopped at [{}]".format(self.stop_at_step.name)


class StepSkippedReason(SkipReason):
    def __init__(self, skipped_steps):
        self.skipped_steps = skipped_steps

    def __str__(self):
        formatted_skips = ", ".join(
            ["[{}]".format(step.name) for step in self.skipped_steps]
        )
        return "Skipping ({})".format(formatted_skips)


class DryRunReason(SkipReason):
    def __str__(self):
        return "Skipping (DRY RUN)"


class StepAction:
    """
    A container that represents the action for a step (run, or skip) and the reason(s) why
    """

    def __init__(
        self, process_step, start_at_step, stop_at_step, skip_steps, dry_run=False
    ):
        self.process_step = process_step

        skip_reasons = []
        if dry_run:
            skip_reasons.append(DryRunReason())

        if start_at_step.value > process_step.value:
            skip_reasons.append(StepBeforeStartReason(start_at_step))

        if stop_at_step.value < process_step.value:
            skip_reasons.append(StepAfterStopReason(stop_at_step))

        if process_step in skip_steps:
            skip_reasons.append(StepSkippedReason(skip_steps))

        if len(skip_reasons) > 0:
            self.skipped = True
            self.skip_reasons = skip_reasons
        else:
            self.skipped = False

    def __eq__(self, other):
        return self.skipped == other.skipped and self.skip_reasons == other.skip_reasons

    @property
    def summary(self):
        if self.skipped:
            skip_strings = [str(reason) for reason in self.skip_reasons]
            return "Skipped [{}]: ({})".format(
                self.process_step.name, ",\n".join(skip_strings)
            )
        else:
            return "[{}]".format(self.process_step.name)


class StepActionMap:
    def __init__(
        self,
        start_at_step=ProcessSteps.START,
        stop_at_step=ProcessSteps.END,
        skip_steps=None,
        dry_run=False,
        only_step=None,
    ):
        action_map = {}
        if only_step:
            start_at_step = only_step
            stop_at_step = only_step

        if skip_steps is None:
            skip_steps = []
        for step in ProcessSteps:
            action_map[step] = StepAction(
                step, start_at_step, stop_at_step, skip_steps, dry_run=dry_run
            )

        self.__action_map = action_map

    def step(self, step):
        return self.__action_map[step]

    def skipped(self, step):
        return self.__action_map[step].skipped

    def summary(self, step):
        return self.__action_map[step].summary

    def any_skipped(self, *steps):
        for step in steps:
            if self.skipped(step):
                return True

        return False

    def all_skipped(self, *steps):
        for step in steps:
            if not self.skipped(step):
                return False

        return True
