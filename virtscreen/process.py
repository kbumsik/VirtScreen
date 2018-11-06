"""Subprocess wrapper"""

import subprocess
import asyncio
import signal
import shlex
import os
import logging


class SubprocessWrapper:
    """Subprocess wrapper class"""
    def __init__(self):
        pass

    def check_output(self, arg) -> None:
        return subprocess.check_output(shlex.split(arg), stderr=subprocess.STDOUT).decode('utf-8')

    def run(self, arg: str, input: str = None, check=False) -> str:
        if input:
            input = input.encode('utf-8')
        return subprocess.run(shlex.split(arg), input=input, stdout=subprocess.PIPE,
                              check=check, stderr=subprocess.STDOUT).stdout.decode('utf-8')


class _Protocol(asyncio.SubprocessProtocol):
    """SubprocessProtocol implementation"""

    def __init__(self, outer):
        self.outer = outer
        self.transport: asyncio.SubprocessTransport

    def connection_made(self, transport):
        logging.info("connectionMade!")
        self.outer.connected()
        self.transport = transport
        transport.get_pipe_transport(0).close()  # No more input

    def pipe_data_received(self, fd, data):
        if fd == 1: # stdout
            self.outer.out_recevied(data)
            if self.outer.logfile is not None:
                self.outer.logfile.write(data)
        elif fd == 2: # stderr
            self.outer.err_recevied(data)
            if self.outer.logfile is not None:
                self.outer.logfile.write(data)

    def pipe_connection_lost(self, fd, exc):
        if fd == 0: # stdin
            logging.info("stdin is closed. (we probably did it)")
        elif fd == 1: # stdout
            logging.info("The child closed their stdout.")
        elif fd == 2: # stderr
            logging.info("The child closed their stderr.")

    def connection_lost(self, exc):
        logging.info("Subprocess connection lost.")

    def process_exited(self):
        if self.outer.logfile is not None:
            self.outer.logfile.close()
        self.transport.close()
        return_code = self.transport.get_returncode()
        if return_code is None:
            logging.error("Unknown exit")
            self.outer.ended(1)
            return
        logging.info(f"processEnded, status {return_code}")
        self.outer.ended(return_code)

        
class AsyncSubprocess():
    """Asynchronous subprocess wrapper class"""

    def __init__(self, connected, out_recevied, err_recevied, ended, logfile=None):
        self.connected = connected
        self.out_recevied = out_recevied
        self.err_recevied = err_recevied
        self.ended = ended
        self.logfile = logfile
        self.transport: asyncio.SubprocessTransport
        self.protocol: _Protocol

    async def _run(self, arg: str, loop: asyncio.AbstractEventLoop):
        self.transport, self.protocol = await loop.subprocess_exec(
            lambda: _Protocol(self), *shlex.split(arg), env=os.environ)

    def run(self, arg: str):
        """Spawn a process.
        
        Arguments:
            arg {str} -- arguments in string
        """
        loop = asyncio.get_event_loop()
        loop.create_task(self._run(arg, loop))

    def close(self):
        """Kill a spawned process."""
        self.transport.send_signal(signal.SIGINT)
