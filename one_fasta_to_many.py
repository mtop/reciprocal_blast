#!/usr/bin/env python

# This script takes a multi sequence fasta file 
# as input and creates new single sequence fasta 
# file for each sequence. 

from Bio import SeqIO
import sys

for file in sys.argv:
	for record in SeqIO.parse(open(file, 'rU'), "fasta"):
		output_file = open('%s.fst' % record.id, "w")
		SeqIO.write(record, output_file, 'fasta')
		output_file.close()
