# Copyright

import logging as _logging
import select as _select
import socket as _socket
import re as _re
import urllib.parse as _urllib_parse
import wsgiref.simple_server as _wsgiref_simple_server

from . import UserInterface as _UserInterface


LOG = _logging.getLogger(__name__)


class HandlerError (Exception):
    def __init__(self, code, msg, headers=[]):
        super(HandlerError, self).__init__('{} {}'.format(code, msg))
        self.code = code
        self.msg = msg
        self.headers = headers


class HandlerErrorApp (object):
    """Catch HandlerErrors and return HTTP error pages.
    """
    def __init__(self, app):
        self.app = app

    def __call__(self, environ, start_response):
        try:
            return self.app(environ, start_response)
        except HandlerError as e:
            LOG.error(e)
            start_response('{} {}'.format(e.code, e.msg), e.headers)
            return []


class WSGI_DataObject (object):
    "Useful WSGI utilities for handling POST data"
    def __init__(self, **kwargs):
        super(WSGI_DataObject, self).__init__(**kwargs)

        # Maximum input we will accept when REQUEST_METHOD is POST
        # 0 ==> unlimited input
        self.maxlen = 0

    def ok_response(self, environ, start_response, content=None,
                    encoding=None, content_type='application/octet-stream',
                    headers=[]):
        response = '200 OK'
        if content is None:
            content_length = 0
        else:
            if encoding:
                if hasattr(content, 'encode'):
                    content = content.encode(encoding)
                content_type = '{}; charset={}'.format(
                    content_type, encoding.upper())
            content_length = len(content)
        start_response(response, [
                ('Content-Type', content_type),
                ('Content-Length', str(content_length)),
                ])
        if content is None:
            return []
        return [content]

    def _parse_query(self, query, encoding='utf-8'):
        if len(query) == 0:
            return {}
        data = _urllib_parse.parse_qs(
            query, keep_blank_values=True, strict_parsing=True)
        data = {str(k, encoding): [str(v, encoding) for v in vs]
                for k,vs in data.items()}
        for k,v in data.items():
            if len(v) == 1:
                data[k] = v[0]
        return data

    def post_data(self, environ):
        if environ['REQUEST_METHOD'] != 'POST':
            raise HandlerError(404, 'Not Found')
        post_data = self._read_post_data(environ)
        return self._parse_post(post_data)

    def _parse_post(self, post):
        return self._parse_query(post)

    def _read_post_data(self, environ):
        try:
            clen = int(environ.get('CONTENT_LENGTH', '0'))
        except ValueError:
            clen = 0
        if clen != 0:
            if self.maxlen > 0 and clen > self.maxlen:
                raise HandlerError(413,  'Request Entity Too Large')
            return environ['wsgi.input'].read(clen)
        return ''


class QuestionApp (WSGI_DataObject):
    """WSGI client serving quiz questions

    For details on WGSI, see `PEP 333`_.

    .. _PEP 333: http://www.python.org/dev/peps/pep-0333/
    """
    def __init__(self, ui, **kwargs):
        super(QuestionApp, self).__init__(**kwargs)
        self.ui = ui
        self.urls = [
            (_re.compile('^$'), self._index),
            (_re.compile('^question/'), self._question),
            (_re.compile('^answer/'), self._answer),
            (_re.compile('^results/'), self._results),
            ]
        self.setting = 'quizzer'
        self.user_regexp = _re.compile('^\w+$')

    def __call__(self, environ, start_response):
        "WSGI entry point"
        path = environ.get('PATH_INFO', '').lstrip('/')
        for regexp,callback in self.urls:
            match = regexp.match(path)
            if match is not None:
                setting = '{}.url_args'.format(self.setting)
                environ[setting] = match.groups()
                return callback(environ, start_response)
        raise HandlerError(404, 'Not Found')

    def _index(self, environ, start_response):
        lines = [
            '<html>',
            '  <head>',
            '    <title>Quizzer</title>',
            '  </head>',
            '  <body>',
            '    <h1>Quizzer</h1>',
            ]
        if self.ui.quiz.introduction:
            lines.append('    <p>{}</p>'.format(self.ui.quiz.introduction))
        lines.extend([
                '    <form name="question" action="../question/" method="post">',
                '      <p>Username: <input type="text" size="20" name="user">',
                '        (required, alphanumeric)</p>',
                '      <input type="submit" value="Start the quiz">',
                '    </form>',
                '  </body>',
                '</html>',
                ])
        content = '\n'.join(lines)
        return self.ok_response(
            environ, start_response, content=content, encoding='utf-8',
            content_type='text/html')

    def _results(self, environ, start_response):
        data = self.post_data(environ)
        user = data.get('user', '')
        if not self.user_regexp.match(user):
            raise HandlerError(303, 'See Other', headers=[('Location', '/')])
        lines = [
            '<html>',
            '  <head>',
            '    <title>Quizzer</title>',
            '  </head>',
            '  <body>',
            '    <h1>Results</h1>',
            ]
        answers = self.ui.answers.get_answers(user=user)
        for question in self.ui.quiz:
            if question.id in answers:
                lines.extend(self._format_result(question=question, user=user))
        lines.extend(self._format_totals(user=user))
        lines.extend([
                '  </body>',
                '</html>',
                ])
        content = '\n'.join(lines)
        return self.ok_response(
            environ, start_response, content=content, encoding='utf-8',
            content_type='text/html')

    def _format_result(self, question, user):
        answers = self.ui.answers.get_answers(user=user).get(question.id, [])
        la = len(answers)
        lc = len([a for a in answers if a['correct']])
        lines = [
            '<h2>Question</h2>',
            '<p>{}</p>'.format(question.format_prompt(newline='<br />')),
            '<p>Answers: {}/{} ({:.2f})</p>'.format(lc, la, float(lc)/la),
            ]
        if answers:
            lines.append('<ol>')
            for answer in answers:
                if answer['correct']:
                    correct = 'correct'
                else:
                    correct = 'incorrect'
                ans = answer['answer']
                if question.multiline:
                    ans = '\n'.join(ans)
                lines.extend([
                        '<li>',
                        '<p>You answered:</p>',
                        '<pre>{}</pre>'.format(ans),
                        '<p>which was {}</p>'.format(correct),
                        '</li>',
                        ])
            lines.append('</ol>')
        return lines

    def _format_totals(self, user=None):
        answered = self.ui.answers.get_answered(
            questions=self.ui.quiz, user=user)
        correctly_answered = self.ui.answers.get_correctly_answered(
            questions=self.ui.quiz, user=user)
        la = len(answered)
        lc = len(correctly_answered)
        return [
            '<h2>Totals</h2>',
            '<p>Answered {} of {} questions.'.format(la, len(self.ui.quiz)),
            'Of the answered questions,',
            '{} ({:.2f}) were answered correctly.'.format(lc, float(lc)/la),
            '</p>',
            ]

    def _question(self, environ, start_response):
        if environ['REQUEST_METHOD'] == 'POST':
            data = self.post_data(environ)
        else:
            data = {}
        user = data.get('user', '')
        if not self.user_regexp.match(user):
            raise HandlerError(303, 'See Other', headers=[('Location', '/')])
        question = data.get('question', None)
        if not question:
            question = self.ui.get_question(user=user)
            # put the question back on the stack until it's answered
            self.ui.stack[user].insert(0, question)
        if question is None:
            raise HandlerError(
                307, 'Temporary Redirect', headers=[('Location', '/results/')])
        if question.multiline:
            answer_element = (
                '<textarea rows="5" cols="60" name="answer"></textarea>')
        else:
            answer_element = '<input type="text" size="60" name="answer"/>'
        lines = [
            '<html>',
            '  <head>',
            '    <title>Quizzer</title>',
            '  </head>',
            '  <body>',
            '    <h1>Question</h1>',
            '    <form name="question" action="../answer/" method="post">',
            '      <input type="hidden" name="user" value="{}">'.format(user),
            '      <input type="hidden" name="question" value="{}">'.format(
                question.id),
            '      <p>{}</p>'.format(
                question.format_prompt(newline='<br/>')),
            answer_element,
            '      <br />',
            '      <input type="submit" value="submit">',
            '    </form>',
            '  </body>',
            '</html>',
            '',
            ]
        content = '\n'.join(lines)
        return self.ok_response(
            environ, start_response, content=content, encoding='utf-8',
            content_type='text/html')

    def _answer(self, environ, start_response):
        data = self.post_data(environ)
        user = data.get('user', '')
        if not self.user_regexp.match(user):
            raise HandlerError(303, 'See Other', headers=[('Location', '/')])
        question_id = data.get('question', None)
        raw_answer = data.get('answer', None)
        if not question_id or not raw_answer:
            LOG.error(data)
            raise HandlerError(422, 'Unprocessable Entity')
        try:
            question = self.ui.quiz.get(id=question_id)
        except KeyError as e:
            raise HandlerError(404, 'Not Found') from e
        if question.multiline:
            answer = raw_answer.splitlines()
        else:
            answer = raw_answer
        correct,details = self.ui.process_answer(
            question=question, answer=answer, user=user)
        link_target = '../question/'
        if correct:
            correct_msg = 'correct'
            self.ui.stack[user] = [q for q in self.ui.stack[user]
                                   if q != question]
            if self.ui.stack[user]:
                link_text = 'Next question'
            else:
                link_text = 'Results'
                link_target = '../results/'
        else:
            correct_msg = 'incorrect'
            link_text = 'Try again'
        if details:
            details = '<p>{}</p>'.format(details)
        lines = [
            '<html>',
            '  <head>',
            '    <title>Quizzer</title>',
            '  </head>',
            '  <body>',
            '    <h1>Answer</h1>',
            '    <p>{}</p>'.format(
                question.format_prompt(newline='<br/>')),
            '    <pre>{}</pre>'.format(raw_answer),
            '    <p>{}</p>'.format(correct_msg),
            details or '',
            '    <form name="question" action="{}" method="post">'.format(
                link_target),
            '      <input type="hidden" name="user" value="{}">'.format(user),
            '      <input type="submit" value="{}">'.format(link_text),
            '    </form>',
            '  </body>',
            '</html>',
            '',
            ]
        content = '\n'.join(lines)
        return self.ok_response(
            environ, start_response, content=content, encoding='utf-8',
            content_type='text/html')


class HTMLInterface (_UserInterface):
    def run(self, host='', port=8000):
        app = QuestionApp(ui=self)
        app = HandlerErrorApp(app=app)
        server = _wsgiref_simple_server.make_server(
            host=host, port=port, app=app)
        self._log_start(host=host, port=port)
        try:
            server.serve_forever()
        except _select.error as e:
            if len(e.args) == 2 and e.args[1] == 'Interrupted system call':
                pass
            else:
                raise

    def _log_start(self, host, port):
        if not host:
            host = _socket.getfqdn()
        LOG.info('serving on {}:{}'.format(host, port))
        try:
            addrs = _socket.getaddrinfo(host=host, port=port)
        except _socket.gaierror as e:
            LOG.warning(e)
        else:
            seen = set()
            for family,type_,proto,canonname,sockaddr in addrs:
                c = canonname or host
                if (c, sockaddr) not in seen:
                    LOG.info('address: {} {}'.format(c, sockaddr))
                    seen.add((c, sockaddr))
