# -*- coding: utf-8 -*-

# Copyright © Spyder Project Contributors
# Licensed under the terms of the MIT License
# (see spyder/__init__.py for details)

"""Kite completion HTTP client."""

# Standard library imports
import logging
import functools

# Qt imports
from qtpy.QtCore import Slot

# Local imports
from spyder.config.manager import CONF
from spyder.utils.programs import run_program
from spyder.api.completion import SpyderCompletionPlugin
from spyder.plugins.completion.kite.client import KiteClient
from spyder.plugins.completion.kite.utils.status import (
    check_if_kite_running, check_if_kite_installed)


logger = logging.getLogger(__name__)


class KiteCompletionPlugin(SpyderCompletionPlugin):
    CONF_SECTION = 'kite'
    CONF_FILE = False

    COMPLETION_CLIENT_NAME = 'kite'

    def __init__(self, parent):
        SpyderCompletionPlugin.__init__(self, parent)
        self.available_languages = []
        self.client = KiteClient(None)
        self.kite_process = None
        self.client.sig_client_started.connect(self.http_client_ready)
        self.client.sig_response_ready.connect(
            functools.partial(self.sig_response_ready.emit,
                              self.COMPLETION_CLIENT_NAME))
        self.update_configuration()

    @Slot(list)
    def http_client_ready(self, languages):
        logger.debug('Kite client is available for {0}'.format(languages))
        self.available_languages = languages
        self.sig_plugin_ready.emit(self.COMPLETION_CLIENT_NAME)

    def send_request(self, language, req_type, req, req_id):
        if self.enabled and language in self.available_languages:
            self.client.sig_perform_request.emit(req_id, req_type, req)
        else:
            self.sig_response_ready.emit(self.COMPLETION_CLIENT_NAME,
                                         req_id, {})

    def start_client(self, language):
        return language in self.available_languages

    def start(self):
        # Always start client to support possibly undetected Kite builds
        self.client.start()
        installed, path = check_if_kite_installed()
        if installed:
            logger.debug('Kite was found on the system: {0}'.format(path))
            running = check_if_kite_running()
            if not running:
                logger.debug('Starting Kite service...')
                self.kite_process = run_program(path)

    def shutdown(self):
        self.client.stop()
        if self.kite_process is not None:
            self.kite_process.kill()

    def update_configuration(self):
        self.client.enable_code_snippets = self.get_option('enable_snippets')
        self.enabled = self.get_option('enable')
