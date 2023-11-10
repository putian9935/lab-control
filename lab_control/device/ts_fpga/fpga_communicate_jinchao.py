#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Feb  8 17:51:47 2019
Last modified on May 14, 2-23 

@author: stephan, wei hong
"""
import numpy as np
import socket
from time import perf_counter
import logging 

class socket_s():
    # initiates connection once called.
    def __init__(self, ):
        self.data = ''
        self.connected = False

    def connect(self, host, port):
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.settimeout(1)
        try:
            self.socket.connect((host, port))
            self.connected = True
        except Exception as e:
            raise ConnectionError(f"Could not connect to {host}") from e
        return 0

    def write(self, data):
        errcode = self.socket.send(data.encode())
        if errcode < 0:
            self.connected = False
        else:
            print('Sent data successfully.')
        return errcode

    def write_trigger(self, data):  # write and trigger wavemeter
        errcode = self.socket.send(data.encode())
        if errcode < 0:
            self.connected = False
        else:
            print('Sent data successfully.')
        return errcode

    def close(self):
        self.socket.close()
        self.connected = False
        return


def read_file(textfile):
    """This function reads the textfile. It gives back a list containing the delay
    and the setting for each output as well as the specified number of repetitions."""
    f = open(textfile)
    n_rep = int(f.readline())
    timestamps = np.asarray(
        list(map(int, f.readline().rstrip().split(';'))), dtype=np.int)
    time_interval = timestamps[1:] - timestamps[:-1]
    time_interval = np.insert(time_interval, 0, 100)
    f.close()

    read_array2 = np.loadtxt(textfile, 
                             delimiter=';', unpack=True, skiprows=2).astype(np.int64)
    data_list2 = np.roll(read_array2, 1, 0)

    return n_rep, time_interval, data_list2


def _convert_int(value, length):
    """converts integer value to the fpga encoding, value is the to be encoded value and len how
    many digits the encoding should have"""
    return _substitute('%0*x' % (length, value))


def _convert_bits(string):
    """Converts bit array to a FPGA encoding, takes a list"""
    return _substitute('%0*x' % ((len(string) + 3) // 4, int(string, 2)))


def _substitute(strval):
    """private function to converts hex string to an fpga encoding"""
    substitute = {'a': ':', 'b': ';', 'c': '<', 'd': '=', 'e': '>', 'f': '?'}
    for key in substitute.keys():
        strval = strval.replace(key, substitute[key])
    return strval


def prep_sequence(data_list, time_interval):
    """prepares the sequence to be loaded to the fpga. this function encodes the actual data and
    converts it into a string which can be send to the fpga"""
    seq_str = ''
    for i in range(len(data_list)):
        delay = int(time_interval[i] * 50 - 2)
        bits = np.array2string(
            np.flip(data_list[i][:], 0), max_line_width=1000, separator='')[1:-1]
        seq_str += 'm' + \
            _convert_int(i, 4) + _convert_int(delay, 8) + \
            _convert_bits(bits) + '\r\n'
    seq_str += 'r%s-----+++++-----+++++----\r\n' % _convert_int(
        len(data_list)-1, 4)
    return seq_str


def write_line(nrep):
    """this function encodes the start command for the fpga. this line also contains the number of
    repetitions for a sequence"""
    return 'n%s01-----+++++-----+++++--\r\n' % _convert_int(nrep, 4)


def main(textfile):
    tt = perf_counter()
    n_rep, time_interval, data_list = read_file(textfile)
    if __name__ == '__main__':
        print('data_list = \n', data_list)
        print('data_list[0] = \n', data_list[0])
        print('len(data_list[0]) = \n', len(data_list[0]))

    sequence = prep_sequence(data_list, time_interval)
    sequencer.write(sequence)

    start_line = write_line(n_rep)
    sequencer.write(start_line)

    logging.debug(f"Send FPGA in {perf_counter()-tt} second(s)")

# takes care of the connection to the FPGA and provides methods to write to it
sequencer = socket_s()

if __name__ == '__main__':
    sequencer.connect('192.168.107.194', 5555)
    main('out')