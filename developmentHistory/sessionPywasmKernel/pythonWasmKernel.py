from ipykernel.kernelbase import Kernel
import pywasm
from subprocess import Popen, PIPE
import os

"""
Web assemvly kernel for jupyter

Added functionality for exported functions, similating a live session
"""

class WasmKernel(Kernel):
    implementation = 'wasmkernel'
    implementation_version = '0.1'
    language = 'webassembly'
    language_version = '0.1'
    language_info = {'name': 'wasmkernel', 'mimetype': 'text/plain', 'file_extension': '.wat'}
    banner = "Wasm kernel - stack based assembly extension"

    def __init__(self, *args, **kwargs):
        #extend __init__
        super(WasmKernel, self).__init__(*args, **kwargs)
        self.tempFile = "temp"
        self.tempDir = "sessionFiles"
        self.textFiles = [] #list of file names
        self.compiledFiles = []
        self.fileCounter = 0

    def CreateNewFile(self):
        newpath = "./" + self.tempDir
        if not os.path.exists(newpath):
            os.makedirs(newpath)

        newFile = "./" + self.tempDir + "/" + self.tempFile + str(self.fileCounter) + ".wat"
        file = open(newFile, "w")
        file.close()
        self.textFiles.append(newFile)
        self.fileCounter = self.fileCounter + 1
        return newFile

    def do_execute(self, code, silent, store_history=True, user_expressions=None, allow_stdin=False):
        if not silent:
            if code.startswith('*MODULE*'):
                newWatFile = self.CreateNewFile()
                currentFile = open(newWatFile, "w")

                trimmedCode = '\n'.join(code.split('\n')[1:])
                currentFile.write(trimmedCode)
                currentFile.close()
                newWasmFile = newWatFile[:-4] + ".wasm"
                #convert code from .wat to a .wasm binary (same file path + name just different extension)
                watSysCommand = "wat2wasm " + newWatFile + " -o " + newWasmFile
                cmdAsArray = watSysCommand.split(' ')
                subpros = Popen(cmdAsArray, stdin=PIPE, stdout=PIPE, stderr=PIPE)
                subpros.wait()
                output, errs = subpros.communicate()
                if subpros.returncode != 0:
                    stream_content = {'name': 'stderr', 'text': str(errs)}
                    self.send_response(self.iopub_socket, 'stream', stream_content)
                else: 
                    self.compiledFiles.append(newWasmFile)
                    stream_content = {'name': 'stdout', 'text': str('Module Written - ' + newWasmFile)}
                    self.send_response(self.iopub_socket, 'stream', stream_content)

            elif code.startswith('*EXEC*'):
                output = ""
                trimmedCode = '\n'.join(code.split('\n')[1:])
                #multiple function callable on separate lines
                callLines = trimmedCode.split('\n')
                for line in callLines:
                    function = line.split(' ')[0]
                    parameters = []
                    if ' ' in line:
                        parameters = line.split(' ')[1:]
                        for i in range(0, len(parameters)): #convert parameters to integers
                            parameters[i] = int(parameters[i]) 
                    #load all exported functions
                    for module in self.compiledFiles:
                        vm = pywasm.load(str(module))
                        for func in vm.module_instance.exports:
                            if func.name == function:
                                output += str(vm.exec(str(func.name), parameters)) + '\n'
                
                if output == "":
                    stream_content = {'name': 'stderr', 'text': 'No matching function found'}
                    self.send_response(self.iopub_socket, 'stream', stream_content)
                else:
                    stream_content = {'name': 'stdout', 'text': output}
                    self.send_response(self.iopub_socket, 'stream', stream_content)

            else:
                stream_content = {'name': 'stderr', 'text': 'Missing header, should be *MODULE* or *EXEC*'}
                self.send_response(self.iopub_socket, 'stream', stream_content)
            
            
        return {'status': 'ok',
                'execution_count': self.execution_count,
                'payload': [],
                'user_expressions': {},
               }


if __name__ == '__main__':
    from ipykernel.kernelapp import IPKernelApp
    IPKernelApp.launch_instance(kernel_class=WasmKernel)