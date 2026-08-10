from .vm import VirtualMachine


class Debugger:
    def __init__(self, program, max_steps=100_000, max_call_depth=500, input_provider=None):
        self.vm = VirtualMachine(max_steps, max_call_depth, input_provider).load(program)
        self.breakpoints = set()
        self.paused = True
        self.last_breakpoint = None

    def add_breakpoint(self, line):
        self.breakpoints.add(int(line))

    def remove_breakpoint(self, line):
        self.breakpoints.discard(int(line))

    def clear_breakpoints(self):
        self.breakpoints.clear()

    def step(self):
        self.paused = True
        self.last_breakpoint = None
        return self.vm.step()

    def continue_run(self):
        self.paused = False
        while not self.vm.halted:
            instruction = self.vm.instructions[self.vm.ip]
            line = instruction.token.line if instruction.token is not None else None
            if self.last_breakpoint is not None and line == self.last_breakpoint:
                self.vm.step()
                continue
            self.last_breakpoint = None
            if line in self.breakpoints:
                self.paused = True
                self.last_breakpoint = line
                break
            self.vm.step()
        return self.snapshot()

    def snapshot(self):
        state = self.vm.snapshot()
        state["paused"] = self.paused
        if not self.vm.halted and self.vm.ip < len(self.vm.instructions):
            instruction = self.vm.instructions[self.vm.ip]
            state["line"] = instruction.token.line if instruction.token is not None else None
            state["instruction"] = instruction.render()
        else:
            state["line"] = None
            state["instruction"] = None
        return state
