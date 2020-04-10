from ipykernel.kernelbase import Kernel
import pywasm
from subprocess import Popen, PIPE
import os

"""
Kernel for compiling WebAssembly code in jupyter
Part of 4TB3 Final Project
"""

class simplePywasmKernel(Kernel):
    implementation = 'simplePywasmkernel'
    implementation_version = '0.1'
    language = 'webassembly'
    language_version = '0.1'
    language_info = {'name': 'simplePywasmkernel', 'mimetype': 'text/plain', 'file_extension': '.wat'}
    banner = "Pywasm kernel - stack based assembly extension"

    def __init__(self, *args, **kwargs):
        #extend __init__
        super(simplePywasmKernel, self).__init__(*args, **kwargs)
        self.tempWatFile = 'temp.wat'
        self.tempWasmFile = 'temp.wasm'
        self.tempDir = './sessionFiles/'
        self.output = ''

    #function for easier output in webassembly
    def write(self, i):
        self.output += str(i) + '\n'

    def createNewFile(self):
        newpath = self.tempDir
        if not os.path.exists(newpath):
            os.makedirs(newpath)

        newFile = self.tempDir + self.tempWatFile
        file = open(newFile, 'w')
        file.close()
        return newFile

    def cleanupFiles(self):
        os.remove(str(self.tempDir + self.tempWatFile))
        os.remove(str(self.tempDir + self.tempWasmFile))
        os.rmdir(self.tempDir)

    def convertWatWasm(self, watFile, wasmFile):
        watSysCommand = "wat2wasm " + watFile + " -o " + wasmFile
        cmdAsArray = watSysCommand.split(' ')
        subproc = Popen(cmdAsArray, stdin=PIPE, stdout=PIPE, stderr=PIPE)
        subproc.wait()
        return subproc

    def do_execute(self, code, silent, store_history=True, user_expressions=None, allow_stdin=False):
        if not silent:
            self.output = ''    #new output for current cell
            newWatFile = self.createNewFile()
            currentFile = open(newWatFile,'w')
            currentFile.write(code)
            currentFile.close()
            newWasmFile = self.tempDir + self.tempWasmFile
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

            #Directory compile current binary
            pywasm.load(newWasmFile, {'P0lib': {'write': self.write}})
            
            stream_content = {'name': 'stdout', 'text': str(self.output)}
            self.send_response(self.iopub_socket, 'stream', stream_content)

        return {'status': 'ok',
                'execution_count': self.execution_count,
                'payload': [],
                'user_expressions': {},
               }

    def do_shutdown(self, restart):
        self.cleanupFiles()

if __name__ == '__main__':
    from ipykernel.kernelapp import IPKernelApp
    IPKernelApp.launch_instance(kernel_class=simplePywasmKernel)