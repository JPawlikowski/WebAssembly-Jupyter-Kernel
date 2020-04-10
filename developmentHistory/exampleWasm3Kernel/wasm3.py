from ipykernel.kernelbase import Kernel
from subprocess import Popen, PIPE
from pexpect import EOF, replwrap
from subprocess import check_output
import signal
import re

# Example code to experiment with wasm3 interpreter
# The purpose of leaving this is to show different approaches we have tried
# This kernel does not work properly - the working kernel is in combinedWasmerKernel
class Wasm3Kernel(Kernel):
    implementation = 'wasm3kernel'
    implementation_version = '0.1'
    language = 'webassembly'
    language_version = '0.1'
    language_info = {'name': 'wasm3kernel', 'mimetype': 'text/plain', 'file_extension': '.wat'}
    banner = "Wasm kernel - stack based assembly extension"

    # Suggestion from jake - wat2wasm as a function call instead of in do_execute
    def wat2wasm(self, wat_name, wasm_name):
        
        convert_cmd = "wat2wasm {0} -o {1}".format(wat_name, wasm_name)
        sub_proccess = Popen(convert_cmd.split(" "), stdin=PIPE, stdout=PIPE, stderr=PIPE)
        sub_proccess.wait()
        return sub_proccess

    def wasm3(self, wasm_name):
        # may need the -repl flag
        # run_cmd = "wasm3 -repl {0}".format(wasm_name)
        run_cmd = "wasm3 -repl {0}".format(wasm_name)
        sub_process = Popen(run_cmd.split(" "), stdin=PIPE, stdout=PIPE, stderr=PIPE)
        sub_process.wait()
        return sub_process

    def do_execute(self, code, silent, store_history=True, user_expressions=None, allow_stdin=False):
        if not silent:

            self.send_response(self.iopub_socket, 'stream', code)
            # If webassembly is written in the cell, write it to a file
            if code.startswith("(module"):
                file_name = 'temp.wat'
                temp_file = open(file_name, 'w')
                temp_file.write(code)
                temp_file.close()

                return {'status': 'ok',
                        'execution_count': self.execution_count,
                        'payload': [],
                        'user_expressions': {},
                        }
            # "add" file name is temporary, was useful for add.wat where function and name of file were the same
            filename = 'temp'
            tempFile = open('{0}.wat'.format(filename), 'w')
            tempFile.write(code)
            tempFile.close()

            # May need to modify this to account if the user wants to write to a file of their choosing
            # similiar to one of the labs
            convert_file = self.wat2wasm("temp.wat", "temp.wasm")
            convert_output, convert_err = convert_file.communicate()

            if convert_file.returncode != 0:
                stream_content = {'name': 'stderr', 'text': str(convert_err)}
                self.send_response(self.iopub_socket, 'stream', stream_content)
                return {'status': 'ok',
                        'execution_count': self.execution_count,
                        'payload': [],
                        'user_expressions': {},
                        }

            # execute the wasm binary
            run_file = self.wasm3("temp.wasm")
            run_output, run_error = run_file.communicate()

            if run_file.returncode != 0:
                stream_content = {'name': 'stderr', 'text': str(run_error)}
                self.send_response(self.iopub_socket, 'stream', stream_content)
                return {'status': 'ok',
                        'execution_count': self.execution_count,
                        'payload': [],
                        'user_expressions': {},
                        }

            # Disply the output in jupyter
            stream_content = {'name': 'stdout', 'text': str(run_output)}
            self.send_response(self.iopub_socket, 'stream', stream_content)

        return {'status': 'ok',
                # The base class increments the execution count
                'execution_count': self.execution_count,
                'payload': [],
                'user_expressions': {},
                }


if __name__ == '__main__':
    from ipykernel.kernelapp import IPKernelApp

    # from . import EchoKernel
    IPKernelApp.launch_instance(kernel_class=Wasm3Kernel)