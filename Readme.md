# Python Bluetooth Low Energy(BLE) Wrapper

A Python wrapper for connecting Bluetooth smart peripherals and centrals.
Currently this wrapper only supports OSX.

## Installation

pip install -U git+https://github.com/brettchien/PyBLEWrapper.git

## Usage

- example usage is in example.py

- A interactive console is also provided

```
    $ git clone https://github.com/brettchein/PyBLEWrapper.git
    $ cd PyBLEWrapper
    $ python setup install
    $ cd pyble
    $ python backend.py
    INFO:osx.centralManager.OSXCentralManager:Initialize CBCentralManager
    INFO:osx.centralManager.OSXCentralManager:BLE is ready!!
    EcoBLE(20-c9-d0-97-57-a0) $ help

    Documented commands (type help <topic>):
    ========================================
    connect     debug       disconnectAll  execute  help  list  shell
    connectAll  disconnect  eval           exit     hist  scan  stop 

    Undocumented commands:
    ======================
    EOF  test

    EcoBLE(20-c9-d0-97-57-a0) $ 
```

## License

    The MIT license
    
    Copyright (c) 2015 Brett Chien

    Permission is hereby granted, free of charge, to any person obtaining a copy
    of this software and associated documentation files (the "Software"), to deal
    in the Software without restriction, including without limitation the rights
    to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
    copies of the Software, and to permit persons to whom the Software is
    furnished to do so, subject to the following conditions:

    The above copyright notice and this permission notice shall be included in
    all copies or substantial portions of the Software.

    THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
    IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
    FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
    AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
    LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
    OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
    THE SOFTWARE.
