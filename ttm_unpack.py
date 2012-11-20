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

decryptState = 0xdeadcafe;

def advanceDecryptor():
	global decryptState
	decryptState = decryptState * 7 + 3

def extractAll(fname):
	global decryptState
	pfile = open(fname, "rb")
	#uint32_t has size of 4 bytes
	uint32_t_size = 4
	sig = struct.unpack('i', pfile.read(uint32_t_size))[0]
	if sig != 1397966674:
		print "Error: not a valid 'To the Moon' datafile"
		sys.exit(-1)
	
	sig = struct.unpack('i', pfile.read(uint32_t_size))[0]
	if sig != 16794689:
		print "Error: not a valid 'To the Moon' datafile"
		sys.exit(-1)
	
	numfiles = 0

	while True:
		#the following line produces faulty results for some reason
		fnameLen = struct.unpack('i', pfile.read(uint32_t_size))[0]
		#check for end of file
		if fnameLen == "" or fnameLen == 0:
			break
		
		fnameLen = fnameLen ^ decryptState
		advanceDecryptor()

		#read and decrypt the filename
		char_size = 1
		fname = struct.unpack('s', pfile.read(char_size * fnameLen))[0]
		
		for i in range(0, fnameLen):
			fname[i] = fname[i] ^ (decryptState & 0xFF)
			advanceDecryptor()

			#hack to mkdir everything
			if fname[i] == '\\':
				fname[i] = '\0'
				os.mkdir(fname, stat.S_IRWXU)
				fname[i] = '/'
		
		print "Extracting" + fname + "..."
		#get file size
		fsize = struct.unpack('i', pfile.read(uint32_t_size))[0]
		fsize = fsize ^ decryptState
		advanceDecryptor()

		#save decryptor state since it's needed for restoring later
		oldDecryptState = decryptState

		try:
			outFile = open(fname, "wb")
		except IOError:
			print "Error, could not create " + fname + "."
			print "Check that you have write permissions to the current directory"
			print "Extraction will now halt"
			close(pfile)
			sys.exit(-1)
		
		#read and decrypt file
		for idx in range(0, fsize):
			c = pfile.read(char_size)
			xorValue = int(decryptState)[idx & 3]
			c = c ^ xorValue
			outFile.write(c)
			if (idx & 3) == 3:
				advanceDecryptor()
		outFile.close()
		
		# restore the decryptor state
		# seems a bit weird, but seems to have been done
		# to make sure the game has fast random-access
		# to packed files
		decryptState = oldDecryptState
		numfiles = numfiles + 1
	print "Extracted " + numfiles + " files!"
		
def main(argv):
	fname = "To the Moon.rgssad"
	if len(argv) > 1:
		fname = argv[1]
	extractAll(fname)
	close(pfile)

if __name__ == "__main__":
	main(sys.argv)

