#!/usr/bin/env python

#
# ttm_unpack_py is a python-port of ttm_unpack by David Gow.

# ttm_unpack_py is an unpacker for the game "To the Moon"'s datafiles

# Copyright (c) 2012, Jukka Pietila <jukkapietila@gmail.com>
# All rights reserved.

# Redistribution and use in source and binary forms, with or without modification, are permitted provided 
# that the following conditions are met:

# Redistributions of source code must retain the above copyright notice, this list of 
# conditions and the following disclaimer.
# Redistributions in binary form must reproduce the above copyright notice, this list of 
# conditions and the following disclaimer in the documentation and/or other materials provided with the 
# distribution.

# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND ANY EXPRESS OR IMPLIED 
# WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A 
# PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE FOR 
# ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED 
# TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) 
# HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING 
# NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE 
# POSSIBILITY OF SUCH DAMAGE.

import io
import sys
import os
import stat
import struct
from array import array

MAX_INT = 4294967295
decryptState = array("I") 
decryptState.append(0xdeadcafe)

def advanceDecryptor():
	global decryptState
	global MAX_INT
	value = decryptState[0]*7+3
	decryptState[0] = value % (MAX_INT + 1)

def extractAll(fname):
	global decryptState
	pfile = open(fname, "rb")
	#uint32_t has size of 4 bytes
	uint32_t_size = 4
	sig = struct.unpack('I', pfile.read(uint32_t_size))[0]
	if sig != 1397966674:
		print "Error: not a valid 'To the Moon' datafile"
		sys.exit(-1)
	
	sig = struct.unpack('I', pfile.read(uint32_t_size))[0]
	if sig != 16794689:
		print "Error: not a valid 'To the Moon' datafile"
		sys.exit(-1)
	
	numfiles = 0
	decryptState.append(decryptState[0])

	while True:
		readData = pfile.read(uint32_t_size)
		if len(readData) == 0:
			break #EOF reached
		fnameLen = struct.unpack('I', readData)[0]

		#since fnameLen is supposed to be unsigned, let's do abs magic
		fnameLen = abs(fnameLen)
		fnameLen = fnameLen ^ decryptState[0]
		advanceDecryptor()

		#read and decrypt the filename
		char_size = 1
		fname = struct.unpack(str(fnameLen) + 's',
					pfile.read(char_size * fnameLen))[0]

		fnameList = list(fname)

		for i in range(0, fnameLen):
			fnameList[i] = chr(ord(fnameList[i]) ^ (decryptState[0] & 0xFF))
			advanceDecryptor()

			#hack to mkdir everything
			if fnameList[i] == '\\':
				dirname = fnameList[:i]
				if not os.path.exists("".join(dirname)):
					os.mkdir("".join(dirname), stat.S_IRWXU)
					print "Creating " + "".join(dirname) + "..."
				fnameList[i] = '/'
		
		print "Extracting " + "".join(fnameList) + "..."
		#get file size
		fsize = struct.unpack('I', pfile.read(uint32_t_size))[0]
		#sys.exit(1)
		fsize = fsize ^ decryptState[0]
		advanceDecryptor()

		#save decryptor state since it's needed for restoring later
		decryptState[1] = decryptState[0]

		try:
			outFile = open("".join(fnameList), "wb")
		except IOError:
			print "Error, could not create " + fname + "."
			print "Check that you have write permissions to the current directory"
			print "Extraction will now halt"
			close(pfile)
			sys.exit(-1)
		
		idx = 0
		#read and decrypt file
		while idx != fsize:
			c = pfile.read(char_size)
			# Get the 'idx'th byte from decryptState (little endian)
			xorValue = (decryptState[0] >> (idx & 3) * 8) & 0xFF
			c = chr(ord(c) ^ xorValue)
			outFile.write(c)
			if (idx & 3) == 3:
				advanceDecryptor()
			idx += 1
		outFile.close()
		
		# restore the decryptor state
		# seems a bit weird, but seems to have been done
		# to make sure the game has fast random-access
		# to packed files
		decryptState[0] = decryptState[1]
		numfiles = numfiles + 1
	pfile.close()
	print "Extracted " + str(numfiles) + " files!"

def main(argv):
	fname = "To the Moon.rgssad"
	if len(argv) > 1:
		fname = argv[1]
	extractAll(fname)

if __name__ == "__main__":
	main(sys.argv)

