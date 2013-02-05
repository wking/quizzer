# Copyright (C) 2013 W. Trevor King <wking@tremily.us>
#
# This file is part of quizzer.
#
# quizzer is free software: you can redistribute it and/or modify it under the
# terms of the GNU General Public License as published by the Free Software
# Foundation, either version 3 of the License, or (at your option) any later
# version.
#
# quizzer is distributed in the hope that it will be useful, but WITHOUT ANY
# WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR
# A PARTICULAR PURPOSE.  See the GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along with
# quizzer.  If not, see <http://www.gnu.org/licenses/>.

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
