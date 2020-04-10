from ipykernel.kernelbase import Kernel
from wasmer import Module, Instance
from subprocess import Popen, PIPE
import os
import shutil

"""
WebAssembly Jupyter Kernel Program
4TB3 Project - April 2nd 2020

Contributors:
Anthony Mella
Tyler Philips
Jakub Pawlikowski
"""

class wasmerKernel(Kernel):
    implementation = 'wasmerKernel'
    implementation_version = '0.1'
    language = 'webassembly'
    language_version = '0.1'
    language_info = {'name': 'wasmerKernel', 'mimetype': 'text/plain', 'file_extension': '.wat'}
    banner = "Wasmer kernel - stack based assembly extension"

    def __init__(self, *args, **kwargs):
        #extend __init__
        super(wasmerKernel, self).__init__(*args, **kwargs)
        self.tempFile = 'temp'
        self.tempWasmFile = 'temp.wasm'
        self.tempDir = './sessionFiles/'
        self.fileCounter = 0
        self.textFiles= []
        self.output = ''
        self.modules = {}
        self.instances = {}

    #./sessionFiles is designated location for temporary files
    #every new *WAAM* has its code written into a new temp#.wat file
    def createNewFile(self):
        newpath = self.tempDir
        if not os.path.exists(newpath):
            os.makedirs(newpath)

        newFile = self.tempDir + self.tempFile + str(self.fileCounter) + ".wat"
        file = open(newFile, 'w')
        file.close()
        self.textFiles.append(newFile)
        self.fileCounter = self.fileCounter + 1
        return newFile

    #Use wabt "wat2wasm" to convert .wat to .wasm
    def convertWatWasm(self, watFile, wasmFile):
        watSysCommand = "wat2wasm " + watFile + " -o " + wasmFile
        cmdAsArray = watSysCommand.split(' ')
        subproc = Popen(cmdAsArray, stdin=PIPE, stdout=PIPE, stderr=PIPE)
        subproc.wait()
        return subproc

    #main function executed every time a cell is ran
    def do_execute(self, code, silent, store_history=True, user_expressions=None, allow_stdin=False):
        if not silent:
            #empty output in case something left over in state
            self.output = ''
            #code to handle web assembly code in the cell
            if code.startswith('*WASM*'):
                #TODO improve module naming
                currentModName = code.split('\n')[0].split(' ')[1]
                trimmedCode = '\n'.join(code.split('\n')[1:])
                newWatFile = self.createNewFile()
                currentFile = open(newWatFile,'w')
                currentFile.write(trimmedCode)
                currentFile.close()
                newWasmFile = newWatFile[:-4] + '.wasm'
                convertProcess = self.convertWatWasm(newWatFile, newWasmFile)
                convertOutput, convertErrs = convertProcess.communicate()
                if convertProcess.returncode != 0:
                    stream_content = {'name': 'stderr', 'text': str(convertErrs)}
                    self.send_response(self.iopub_socket, 'stream', stream_content)
                    return {'status': 'ok',
                    'execution_count': self.execution_count,
                    'payload': [],
                    'user_expressions': {},
                    }
                else:
                    #create 'module' and 'instance' using wasmer python extension
                    wasmBytes = open(newWasmFile, 'rb').read()
                    self.modules[currentModName] = Module(wasmBytes)
                    self.instances[currentModName] = self.modules[currentModName].instantiate()

                    self.output = "Created Module : " + currentModName + '\n' + "Created Instance : " + currentModName
                    stream_content = {'name': 'stdout', 'text': str(self.output)}
                    self.send_response(self.iopub_socket, 'stream', stream_content)

            # Code will handle python code in the cell
            elif code.startswith('*PYTHON*'):
                trimmedCode = '\n'.join(code.split('\n')[1:])
                # error handling for the python code - will return the output if an error is thrown
                try:
                    #NOTICE:
                    #usage of exec is potentially unsafe, unfiltered code from cell used with full global scope
                    exec(trimmedCode)
                except Exception as e:
                    stream_content = {'name': 'stderr', 'text': 'Error: {0}'.format(e)}
                    self.send_response(self.iopub_socket, 'stream', stream_content)
                    return {'status': 'ok',
                    'execution_count': self.execution_count,
                    'payload': [],
                    'user_expressions': {},
                    }
                stream_content = {'name': 'stdout', 'text': str(self.output)}
                self.send_response(self.iopub_socket, 'stream', stream_content)

            # Will throw an error if the header does not match *WASM* or *PYTHON*
            else:
                error_message = 'Header not valid, please use *PYTHON* when running Python code' \
                               ' or *WASM* for running WebAssembly code'
                stream_error = {'name': 'stderr', 'text': error_message}
                self.send_response(self.iopub_socket, 'stream', stream_error)

                return {'status': 'ok',
                        # The base class increments the execution count
                        'execution_count': self.execution_count,
                        'payload': [],
                        'user_expressions': {},
                        }
           
        return {'status': 'ok',
                'execution_count': self.execution_count,
                'payload': [],
                'user_expressions': {},
               }

    #cleanup ./sessionFiles/ upon kernel shutdown
    def do_shutdown(self, restart):
        shutil.rmtree(self.tempDir)

if __name__ == '__main__':
    from ipykernel.kernelapp import IPKernelApp
    IPKernelApp.launch_instance(kernel_class=wasmerKernel)