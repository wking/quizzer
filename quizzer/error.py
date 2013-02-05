class CommandError (RuntimeError):
    def __init__(self, arguments, stdin=None, stdout=None, stderr=None,
                 status=None, msg=None):
        error_msg = 'error executing {}'.format(arguments)
        if msg:
            error_msg = '{}: {}'.format(error_msg, msg)
        super(CommandError, self).__init__(error_msg)
        self.arguments = arguments
        self.stdin = stdin
        self.stdout = stdout
        self.stderr = stderr
        self.status = status
